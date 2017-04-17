from .. import model
from . import render
from . import snapshot
from gi.repository import Gtk, Gdk, Gio

def get_iter_last(store):
	last = None
	cur = store.get_iter_first()
	while cur is not None:
		last = cur
		cur = store.iter_next(cur)
	return last

class DataController(object):
	def __init__(self, edit_buffer):
		self.project = None
		self.edited = 0
		self.filename = None
		self.treemodel = model.create_treemodel()
		self.edit_buffer = edit_buffer
		self.history = snapshot.SnapshotController()

	def Edit(self, key):
		assert(isinstance(key, int))
		self.history.record('edit/{}'.format(key), self)

		if self.edited > 0:
			with self.history.lock():
				self.Commit()
			
		if self.project is not None and self.project[key] != 'group':
			block = self.project[key]
			text = '{}\n{}'.format(block.title, block.text)
			with self.history.lock():
				self.edited = key
				self.set_edit_text(text)
		else:
			return None

	def Commit(self):
		# not undoable
		if self.project is not None and self.edited > 0:
			#self.history.record('commit/{}'.format(self.edited), self)
			block = self.project[self.edited]
			edit_text = self.get_edit_text()
			if '\n' in edit_text:
				i = edit_text.index('\n')
				title = edit_text[:i]
				text = edit_text[i+1:]
			else:
				title = edit_text
				text = ''

			block.title = title
			block.text = text
			model.update_element(self.treemodel, self.project, block)

	def Open(self, flname=None):
		if flname is None:
			self.project = model.Project()
			self.filename = None
		else:
			self.project = model.open_xml(flname)
			self.filename = flname
		self.edited = 0
		self.history.reset()
		model.update_treemodel(self.treemodel, self.project)

	def CreateElement(self, store, parent, sibling, title='Default'):
		key = self.project.get_unique_key()
		item = model.Item(key, title, '', [])
		if parent is None:
			dest = (sibling, Gtk.TreeViewDropPosition.AFTER)
		else:
			dest = (parent, Gtk.TreeViewDropPosition.INTO_OR_AFTER)
		self.AddElement(store, item, source=None, dest_path=dest)

	def RemoveElement(self, store, row):
		row_key = model.get_key(store, row)

		group = None
		iter_start = None

		parent = store.iter_parent(row)
		if parent is None:
			self.history.record('remove/{}'.format(row_key), self)
			with self.history.lock():
				store.remove(row)
				iter_start = store.get_iter_first()
				model.update_group_from_model(store, self.project, iter_start)
				model.update_treemodel(self.treemodel, self.project)
		else:
			group_key = model.get_key(store, parent)
			group = self.project[group_key]
			iter_start = store.iter_children(parent)
			self.history.record('remove/{}'.format(row_key), self)

			with self.history.lock():
				store.remove(row)
				model.update_group_from_model(store, group, iter_start)
				model.update_element(self.treemodel, self.project, group)

	def AddElement(self, store, item, source=None, dest_path=None):
		if store is None:
			store = self.treemodel
		# make sure the item is in the project, get the key
		if isinstance(item, model.Item):
			key = item.key
			if key not in self.project:
				self.project.add_item(item)
		else:
			key = item
			item = self.project[key]

		# determine insertion location (insert, rel)
		if dest_path is None:
			insert = get_iter_last(store)
			rel = Gtk.TreeViewDropPosition.AFTER
		else:
			path, rel = dest_path
			insert = store.get_iter(path) if path is not None else path

		self.history.record('add-element/{}'.format(key), self)

		# figure out what to insert
		dest_iter = None
		with self.history.lock():
			values = model.get_row(item)
			if rel == Gtk.TreeViewDropPosition.BEFORE:
				dest_iter = store.insert_before(None, insert, values)
			elif rel == Gtk.TreeViewDropPosition.AFTER:
				dest_iter = store.insert_after(None, insert, values)
			elif rel == Gtk.TreeViewDropPosition.INTO_OR_AFTER:
				dest_iter = store.insert_after(insert, None, values)
			elif rel == Gtk.TreeViewDropPosition.BEFORE_OR_AFTER:
				dest_iter = store.insert_before(insert, None, values)
			else:
				raise NotImplementedError(rel)
			
		# what to do with the source
		# TODO: if the object is not moved, do not record
		if source is not None:
			with self.history.lock():
				store.remove(source)

		
		dest_parent = store.iter_parent(dest_iter)
		with self.history.lock():
			if dest_parent is None:
				iter_start = store.get_iter_first()
				model.update_group_from_model(store, self.project, iter_start)
				model.update_treemodel(store, self.project)
			else:
				key = model.get_key(store, dest_parent)
				start = store.iter_children(dest_parent)
				model.update_group_from_model(store, self.project[key], start)
				model.update_element(store, self.project, self.project[key])

	def Save(self, flname=None):
		self.Commit()
		self.project.clean()
		if flname is None:
			flname = self.filename
		# save xml
		output = model.render_project(self.project)
		with open(flname, 'w') as fl:
			fl.write(output)

	def RecordInsertion(self, offset, text):
		if self.history.can_record():
			self.history.insert(offset, text)

	def RecordDeletion(self, offset, text):
		if self.history.can_record():
			self.history.delete(offset, text)

	def Render(self, flname):
		self.Commit()
		output = render.render_project(self.project)
		with open(flname, 'w') as fl:
			fl.write(output)

	def WriteElementToClipboard(self, clipboard, key):
		block = self.project[key]
		text = model.render_item(block)
		clipboard.set_text(text, -1)

	def Undo(self):
		self.history.revert(self)

	def Redo(self):
		self.history.restore(self)

	def set_edit_text(self, text):
		self.edit_buffer.set_text(text, -1)

	def get_edit_text(self, include_hidden=True):
		buff = self.edit_buffer
		return buff.get_text(
			buff.get_start_iter(),
			buff.get_end_iter(), include_hidden)
