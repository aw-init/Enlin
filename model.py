from gi.repository import Gtk
import gui
import snapshot
import data

"""
Add actions here
Each action should be atomic, reversable, and independent of the view.
actions may return suggestions to the gui as to what to update
"""
class InvalidActionError(RuntimeError):
	pass

class Application(gui.Application):
	def __init__(self):
		super(Application, self).__init__()
		self.Project = data.Project()
		self.EditedBlockId = 0
		self.Filename = None
		self.History = snapshot.History()


	def do_activate(self):
		super(Application, self).do_activate()

	def SetFilename(self, flname=None):
		self.Filename = flname
		if flname is not None:
			self.MainWindow.set_title("Enlin - {}".format(flname))
		else:
			self.MainWindow.set_title("Enlin")	

	def OpenProject(self, flname):
		self.Project = data.Project.FromFile(flname)
		self.SetFilename(flname)

	def CloseProject(self):
		self.NewProject()

	def NewProject(self):
		self.Project = data.Project()	
		self.SetFilename()

	def SaveProject(self, flname=None):
		self.updateProjectTagsFromModel()
		if flname is None:
			flname = self.Filename
		if self.Project is not None:
			xml = self.Project.as_xml()
			text = data.pretty_render(xml)
			with open(flname, 'w') as fl:
				fl.write(text)
		else:
			raise InvalidActionError("SaveProject")

	def ModifyBlock(self, block_id, title, text, undoable=True):
		# used from Action_Commit
		if undoable:
			self.History.snapshot(self, 'modify:{}({})'.format(block_id, title))
		with self.History.not_undoable() as locked:
			block = self.Project.get_block(block_id)
			if title is not None:
				block.title = title
			if text is not None:
				block.text = text
			elem = data.Element.FromBlock(block)
			rows = list(self.find_block_rows(block_id))
			for row in rows:
				self.Gui_Update(elem, row)

	def EditBlock(self, block_id):
		self.History.snapshot(self, 'set-edit:{}'.format(block_id))
		with self.History.not_undoable() as locked:
			self.EditedBlockId = block_id
			if block_id > 0:
				block = self.Project.get_block(block_id)
				self.set_edit_text(block.as_edit_text())
			else:
				self.set_edit_text("")
		

	def updateProjectTagsFromModel(self):
		tags = {}
		for (tag, block_id) in self.block_iter():
			if block_id in tags:
				tags[block_id].append(tag)
			else:
				tags[block_id] = [tag]
		for block_id, tag_list in tags.items():
			block = self.Project.get_block(block_id)
			block.tags = tag_list
