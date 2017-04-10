from .. import model
from . import render
from . import snapshot
from gi.repository import Gtk, Gdk, Gio

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
		if self.edited > 0:
			# autocommit
			pass
			
		if self.project is not None and self.project[key] != 'group':
			block = self.project[key]
			text = '{}\n{}'.format(block.title, block.text)
			self.history.record('edit/{}'.format(key), self)
			with self.history.lock():
				self.edited = key
				self.set_edit_text(text)
		else:
			return None

	def Commit(self):
		if self.project is not None and self.edited > 0:
			self.history.record('commit/{}'.format(self.edited), self)
			block = self.project[self.edited]
			edit_text = self.get_edit_text()
			if '\n' in edit_text:
				i = edit_text.index('\n')
				title = edit_text[:i]
				text = edit_text[i+1:]
			else:
				title = edit_text
				text = ''
			with self.history.lock():
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

	def CreateElement(self, store, parent, sibling):
		key = self.project.get_unique_key()
		item = model.Item(key, 'Default Title', '', [])
		values = model.get_row(item)
		self.history.record('create-element/{}'.format(key), self)
		with self.history.lock():
			self.project.add_item(item)
			store.insert_after(parent, sibling, values)
		model.update_element(self.treemodel, self.project, item)

	def RemoveElement(self, store, row):
		row_key = model.get_key(store, row)
		group = None
		iter_start = None
		parent = store.iter_parent(row)
		if parent is None:
			group = self.project
			iter_start = store.get_iter_first()
		else:
			key = model.get_key(store, parent)
			group = self.project[key]
			iter_start = store.iter_children(parent)
		self.history.record('remove/{}'.format(row_key), self)
		with self.history.lock():
			store.remove(row)
			model.update_group_from_model(store, group, iter_start)
			model.update_element(self.treemodel, self.project, group)

	def AddElement(self, store, src, dest_path, key):
		if dest_path is not None:
			path, rel = dest_path
			sibling = store.get_iter(path)
		else:
			# placed somewhere not next to a row, but on the widget
			# put at the end?
			head = store.get_iter_first()
			sibling = None
			while head is not None:
				sibling = head
				head = store.iter_next(head)
			rel = Gtk.TreeViewDropPosition.AFTER

		item = self.project[key]
		values = model.get_row(item)

		self.history.record('drag-element/{}'.format(key), self)

		with self.history.lock():
			if rel == Gtk.TreeViewDropPosition.BEFORE:
				dest = store.insert_before(None, sibling, values)

			elif rel == Gtk.TreeViewDropPosition.AFTER:
				dest = store.insert_after(None, sibling, values)

			else:
				raise RuntimeError('Unknown drop location {}'.format(rel))

		src_parent = store.iter_parent(src)
		if src_parent is None:
			src_parent_path = None
		else:
			src_parent_path = store.get_path(src_parent)

		dest_parent = store.iter_parent(dest)
		if dest_parent is not None:

			# move if dragged to same group
			# copy if dragged to different group
			if src_parent_path == store.get_path(dest_parent):
				store.remove(src)

			dest_parent_key = model.get_key(store, dest_parent)
			group = self.project[dest_parent_key]
			iter_start = store.iter_children(dest_parent)
			with self.history.lock():
				model.update_group_from_model(store, group, iter_start)
				model.update_element(self.treemodel, self.project, group)
		else:
			if src_parent_path is None:
				store.remove(src)

			group = self.project
			iter_start = store.get_iter_first()
			with self.history.lock():
				model.update_group_from_model(store, self.project, iter_start)
				model.update_treemodel(self.treemodel, self.project)

	def Save(self, flname=None):
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
		output = render.render_project(self.project)
		with open(flname, 'w') as fl:
			fl.write(output)

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
