import boilerplate
from gi.repository import Gtk, GLib, GtkSource, Gio, GObject
import re
import blocks

class EnlinApplication(boilerplate.Application):
	def __init__(self, gui_path):
		super(EnlinApplication, self).__init__(gui_path)
		self.Model = None

	def do_activate(self):
		super(EnlinApplication, self).do_activate()

		# IN DEBUG_MODE_ONLY
		#self.OpenNote('test.xml')
		
	def Action_Open(self, action):
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.mainWindow,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		xmlfilter = Gtk.FileFilter()
		xmlfilter.set_name("Note Xml File")
		xmlfilter.add_mime_type("text/xml")
		fileChooser.add_filter(xmlfilter)

		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			flname = fileChooser.get_filename()
			self.OpenNote(flname)
		fileChooser.destroy()

	def Action_New(self, action):
		if self.Project.file_is_open():
			self.Action_Save()
		if self.Project.block_is_edited():
			self.ClearEditWindow()

		self.Project.new_note()

	def Action_Quit(self, action):
		self.quit()
		
	def Action_Edit(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) == 1:
			loc = model.get_iter(selected[0])
			block_id = model.get_value(loc, 1)
			if block_id > 0:
				block = self.Project.get_block(block_id)
				text = block.as_edit_text()
				txtbuf = self.editWindow.get_buffer()
				txtbuf.begin_not_undoable_action()
				txtbuf.set_text(text)
				txtbuf.end_not_undoable_action()
				self.Project.edit_block(block_id)

	def Action_Save(self, action=None):
		if self.Project.file_is_open():
			self.SaveNoteToFile(self.Project.filename)

	def Action_SaveAs(self, action=None):
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.mainWindow,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
	
		if self.Project.file_is_open():
			fileChooser.set_filename(self.Project.filename)

		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			flname = fileChooser.get_filename()
			self.SaveNoteToFile(flname)
			
		fileChooser.destroy()

	def SaveNoteToFile(self, flname):
		self.UpdateNoteModel()
		self.Project.save_note(flname)	
	
	def UpdateNoteModel(self):
		# write all gui changes to the Note model
		if self.Project.note_is_available():
			if self.Project.block_is_edited():
				txtbuf = self.editWindow.get_buffer()
				edit_text = txtbuf.get_text(txtbuf.get_start_iter(), txtbuf.get_end_iter(), True)
				title, body = blocks.Block.ParseEditText(edit_text)
				block = self.Project.get_current_block()

				# undo/redo atomic action?
				block.title = title
				block.text = body

			tree = blocks.Tree.OfModel(self.Model)
			flat = blocks.Tree.Flatten(tree)
			for block_id, tags in flat.items():
				self.Project.get_block(block_id).tags = tags
			

	def OpenNote(self, flname):
		assert(self.Gui != None)
		assert(self.Model != None)
		self.Project.open_note(flname)

		self.Model.clear()
		note = self.Project.note
		tree = blocks.Tree.FromNote(note)
		self.UpdateTreeModel(self.Model, note, tree)

	def ClearEditWindow(self):
		txtbuf = self.editWindow.get_buffer()
		txtbuf.begin_not_undoable_action()
		txtbuf.set_text("")
		txtbuf.end_not_undoable_action()
		self.Project.stop_edit()

	def UpdateTreeModel(self, model, note, tree, dest=None):
		for block_id in tree.values():
			title = note[block_id].title
			model.append(dest, [title, block_id])

		for (tag, child) in tree.children():
			sub = model.append(dest, [tag, -1])
			self.UpdateTreeModel(model, note, child, sub)

	def on_treeWindow_button_press(self, tree, arg):
		if arg.button == 3:
			menu = self.Gui.get_object('treeContextPopup')
			menu.popup(None, None, None, None, arg.button, Gtk.get_current_event_time())
			return True

if __name__ == '__main__':
	app = EnlinApplication("gui.glade")
	boilerplate.main(app)
