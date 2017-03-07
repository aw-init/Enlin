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

	def Action_Quit(self, action):
		self.quit()
		
	def Action_Edit(self, action):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) == 1:
			loc = model.get_iter(selected[0])
			block_id = model.get_value(loc, 1)
			if block_id > -1:
				block = self.Project.note[block_id]
				self.Project.block_id = block_id
				text = block.as_edit_text()
				txtbuf = self.editWindow.get_buffer()
				txtbuf.begin_not_undoable_action()
				txtbuf.set_text(text)
				txtbuf.end_not_undoable_action()
	
	def UpdateEditedBlock(self):
		if self.Project.editing():
			txtbuf = self.editWindow.get_buffer()
			edit_text = txtbuf.get_text(txtbuf.get_start_iter(), txtbuf.get_end_iter(), True)
			title, body = blocks.Block.ParseEditText(edit_text)
			block = self.Note[self.editedBlockId]

			# undo/redo atomic action?
			block.title = title
			block.text = body


	def Action_Save(self, action):
		self.UpdateEditedBlock()
		tree = blocks.Tree.OfModel(self.Model)
		flat = blocks.Tree.Flatten(tree)
		for block_id, tags in flat.items():
			self.Project.note[block_id].tags = tags
		blocks.Note.Save(self.Note)

	def OpenNote(self, flname):
		assert(self.Gui != None)
		assert(self.Model != None)
		self.Project.open_project(flname)

		self.Model.clear()
		tree = blocks.Tree.FromNote(self.Project.note)
		self.UpdateModel(self.Model, self.Project.note, tree)

	def UpdateModel(self, model, note, tree, dest=None):
		for block_id in tree.values():
			title = note[block_id].title
			model.append(dest, [title, block_id])

		for (tag, child) in tree.children():
			sub = model.append(dest, [tag, -1])
			self.UpdateModel(model, note, child, sub)

	def on_treeWindow_button_press(self, tree, arg):
		if arg.button == 3:
			menu = self.Gui.get_object('treeContextPopup')
			menu.popup(None, None, None, None, arg.button, Gtk.get_current_event_time())
			#menu.popup_at_pointer(arg)

if __name__ == '__main__':
	app = EnlinApplication("gui.glade")
	boilerplate.main(app)
