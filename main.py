import boilerplate
from gi.repository import Gtk, GLib, GtkSource, Gio, GObject
import re
import blocks

def row(s, i=-1, b=False):
	return [s, i, b]

class EnlinApplication(boilerplate.Application):
	def __init__(self, gui_path):
		super(EnlinApplication, self).__init__(gui_path)

	def do_activate(self):
		super(EnlinApplication, self).do_activate()

		self.Action_New()
		
	def Action_Open(self, action):
		self.Action_Close()

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
			self.openNote(flname)
		fileChooser.destroy()

	def openNote(self, flname):
		# open a new note
		self.Project.open_note(flname)

		# refresh the gui to match the note
		self.RefreshGui()

	def Action_Close(self, action=None):
		pass

	def Action_Rename(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			path = selected[0]

			# set editable
			treeiter = model.get_iter(path)
			model.set_value(treeiter, 2, True)

			col = self.treeWindow.get_column(0)
			self.treeWindow.set_cursor(path, col, True)
			self.treeWindow.grab_focus()

	def Action_New(self, action=None):
		self.Project.new_note()
		self.RefreshGui()

	def Action_Quit(self, action):
		self.quit()
		
	def Action_Edit(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) == 1:
			loc = model.get_iter(selected[0])
			block_id = model.get_value(loc, 1)
			if block_id > 0:
				self.Project.edit_block(block_id)
				self.RefreshEditWindow()

	def Action_Save(self, action=None):
		if self.Project.file_is_open():
			self.saveNoteToFile(self.Project.filename)

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
			self.saveNoteToFile(flname)			
		fileChooser.destroy()

	def saveNoteToFile(self, flname):
		self.commitChangesToProject()
		self.Project.write_note_to_file(flname)

	def Action_RemoveElement(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		for rowpath in selected:
			treeiter = model.get_iter(rowpath)
			self.Project.model.remove(treeiter)
		self.commitChangesToProject()
	
	def Action_NewBlock(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			for rowpath in selected:
				treeiter = model.get_iter(rowpath)
				tag = blocks.Tag.FromModel(model, treeiter)
				self._addNewBlock(model, tag, treeiter)
		else:
			self._addNewBlock(model, "")

	def _addNewBlock(self, model, tag, dest=None):
		if dest is None:
			dest = model.get_iter_first()
		new_id = self.Project.get_unique_id()
		newBlock = blocks.Block(new_id, "Default Title", [], "")

		# update project
		self.Project.note.add_block(newBlock)

		# update gui
		model.append(dest, row(newBlock.get_title(), new_id))

	def Action_NewTag(self, action=None):
		(model, selected) = self.treeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			for rowpath in selected:
				treeiter = model.get_iter(rowpath)
				self._addNewTag(model, "default", treeiter)
		else:
			self._addNewTag(model, "default")

	def _addNewTag(self, model, tag, dest=None):
		if dest is None:
			dest = model.get_iter_first()

		# update gui
		model.append(dest, row(tag))
		

	def RefreshGui(self):
		self.RefreshTree()
		self.RefreshEditWindow()
		if self.Project.file_is_open():
			self.mainWindow.set_title("Enlin - {}".format(self.Project.filename))

	def RefreshEditWindow(self):
		if self.Project.block_is_edited():
			block = self.Project.get_current_block()
			text = block.as_edit_text()
			txtbuf = self.editWindow.get_buffer()
			txtbuf.begin_not_undoable_action()
			txtbuf.set_text(text)
			txtbuf.end_not_undoable_action()
		else:
			txtbuf = self.editWindow.get_buffer()
			txtbuf.begin_not_undoable_action()
			txtbuf.set_text("")
			txtbuf.end_not_undoable_action()

	def RefreshBlockTitles(self, model=None, node=None):
		if model is None:
			model = self.Project.model
		if node is None:
			node = model.get_iter_first()

		bid = model.get_value(node, 1)
		if bid > 0:
			block = self.Project.get_block(bid)
			model.set_value(node, 0, block.get_title())
		
		child = model.iter_children(node)
		while child is not None:
			self.RefreshBlockTitles(model, child)
			child = model.iter_next(child)

	def RefreshTree(self):
		# warning: will reset opened tags
		model = self.Project.model
		note = self.Project.note
		tree = blocks.Tree.FromNote(note)
		model.clear()
		self._writeTagTree(model, note, tree)		

	def _writeTagTree(self, model, note, tree, dest=None):
		for block_id in tree.values():
			title = note[block_id].get_title()
			model.append(dest, row(title, block_id))

		for (tag, child) in tree.children():
			sub = model.append(dest, row(tag))
			self._writeTagTree(model, note, child, sub)

	def commitChangesToProject(self):
		if self.Project.note_is_available():
			notelink = blocks.NoteLink.FromModel(self.Project.model)
			for block_id, tag_set in notelink.items():
				tag_list = list(tag_set)
				self.Project.set_block_tags(block_id, tag_list)

			if self.Project.block_is_edited():
				txtbuf = self.editWindow.get_buffer()
				edit_text = txtbuf.get_text(txtbuf.get_start_iter(), txtbuf.get_end_iter(), True)
				title, body = blocks.Block.ParseEditText(edit_text)

				self.Project.set_block_contents(None, title, body)

				block = self.Project.get_current_block()

				self.RefreshBlockTitles()

	def on_treeWindow_button_press(self, tree, arg):
		if arg.button == 3:
			menu = self.Gui.get_object('treeContextPopup')
			menu.popup(None, None, None, None, arg.button, Gtk.get_current_event_time())
			return True
		elif self.treeWindow.get_path_at_pos(arg.x, arg.y) is None:
			# clicked on nothing
			# unselect all
			# stop renaming
			self.treeWindow.get_selection().unselect_all()


	def on_treeWindow_row_activated(self, tree, *arg):
		self.Action_Edit()

	def on_cell_edited(self, cell, path, text):
		model = self.Project.model
		treeiter = model.get_iter(path)
		model.set_value(treeiter, 2, False)
		model.set_value(treeiter, 0, text)
		bid = model.get_value(treeiter, 1)
		if bid > 0:
			self.Project.set_block_contents(bid, text, None)

if __name__ == '__main__':
	app = EnlinApplication("gui.glade")
	boilerplate.main(app)
