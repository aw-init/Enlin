import model
#import data
import api
import snapshot
from gi.repository import Gtk, Gdk, GtkSource, Gio, GObject, GdkPixbuf
AUTO_COMMIT_ON_EDIT = True

class Application(model.Application):
	def __init__(self):
		super(Application, self).__init__()
		self.DragInProgress = False
		self.DragInfo = {}

	def do_activate(self):
		super(Application, self).do_activate()
		self.Gui.connect_signals(self)
		self.TreeWindow.connect('drag-begin', self.on_drag_begin)
		self.TreeWindow.connect_after('drag-end', self.on_drag_end)
		
		self.set_keyboard_shortcut("<Control>Z", self.Action_Undo)
		#self.set_keyboard_shortcut("<Control>C", self.Action_CopyText)
		#self.set_keyboard_shortcut("<Control>V", self.Action_PasteText)
		#self.set_keyboard_shortcut("<Control>X", self.Action_CutText)

		self.set_keyboard_shortcut("<Control>U", self.debug_undo_manager)
		self.set_keyboard_shortcut("<Control>P", self.debug_project)

	def debug_undo_manager(self, *args):
		print self.History
	def debug_project(self, *args):
		print self.Project

	def Action_Commit(self, *args):
		if self.EditedBlockId > 0:
			# parse the text in the window and write it to the active block
			block_id = self.EditedBlockId
			contents = self.get_edit_text()

			title, text = data.Block.ParseEditableText(contents)

			self.ModifyBlock(block_id, title, text)
 
	def Action_Edit(self, *args):
		# get the block associated with the selected row and edit it.
		if self.EditedBlockId > 0 and AUTO_COMMIT_ON_EDIT:
			with self.History.not_undoable() as locked:
				self.Action_Commit()

		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = model.get_iter(current_path)
			block_id = model.get_value(current, 1)
			if block_id > 0:
				self.EditBlock(block_id)

	def on_treeWindow_row_activated(self, tree, *arg):
		self.Action_Edit()	

	def Action_New(self, *args):
		# create brand new project, and reset the gui, history, and edit window
		self.NewProject()
		self.Gui_Update(data.Element.FromProject(self.Project))
		self.EditBlock(0)
		self.History.reset()

	def Action_Open(self, *args):
		# open project from xml, and reset the gui, history, and edit window
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.MainWindow,
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
			self.OpenProject(flname)
			self.EditBlock(0)
			self.Gui_Update(data.Element.FromProject(self.Project))
		fileChooser.destroy()
		self.History.reset()

	def Action_Quit(self, *args):
		# close the application
		self.quit()

	def Action_Save(self, *args):
		# write the current project to xml on disk
		self.SaveProject()

	def Action_SaveAs(self, *args):
		# write the current project to xml on disk
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.MainWindow,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			flname = fileChooser.get_filename()
			self.SaveProject(flname)
		fileChooser.destroy()

	def Action_Render(self, *args):
		# write the current project to html on disk
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.MainWindow,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			flname = fileChooser.get_filename()
			self.Render(flname)
		fileChooser.destroy()		

	def Action_NewBlock(self, *args):
		# create new block, insert it into the current project
		new_id = self.Project.get_unique_id()
		title = 'Default Title'
		new_block = data.Block(new_id, title, [None], '')
		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		self.History.snapshot(self, 'new-block:{}'.format(new_id))
		if len(selected) > 0:
			current_path = selected[0]
			current = model.get_iter(current_path)
			if model.get_value(current, 1) > 0:
				model.insert_after(None, current, [title, new_id, False])
			else:
				self.TreeWindow.expand_row(current_path, False)
				model.insert_after(current, None, [title, new_id, False])
		else:
			# insert at beginning of root
			model.insert_after(None, None, [title, new_id, False])

		self.Project.add_block(new_block)
		self.updateProjectTagsFromModel()

	def Action_RemoveElement(self, *args):
		# remove selected block from the gui (and project)
		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = model.get_iter(current_path)
			self.History.snapshot(self, 'remove-element:{}'.format(current_path))
			model.remove(current)

	def Action_NewTag(self, *args):
		# add new group
		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		self.History.snapshot(self, 'new-tag')
		if len(selected) > 0:
			current_path = selected[0]
			current = model.get_iter(current_path)
			if model.get_value(current, 1) > 0:
				model.insert_after(None, current, ['tag', -1, False])
			else:
				model.insert_after(current, None, ['tag', -1, False])
		else:
			# insert at beginning of root
			model.insert_after(None, None, ['tag', -1, False])
	
	def Action_DeleteText(self, *args):
		txtbuffer = self.EditWindow.get_buffer()
		selection = txtbuffer.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			txtbuffer.delete(start, stop)

	def Action_CopyText(self, *args):
		txtbuffer = self.EditWindow.get_buffer()
		selection = txtbuffer.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = txtbuffer.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)

	def Action_CutText(self, *args):
		txtbuffer = self.EditWindow.get_buffer()
		selection = txtbuffer.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = txtbuffer.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)
			txtbuffer.delete(start, stop)

	def Action_PasteText(self, *args):
		txtbuffer = self.EditWindow.get_buffer()
		#dest = txtbuffer.get_insert()
		text = self.Clipboard.wait_for_text()
		txtbuffer.insert_at_cursor(text, -1)
	
	def Action_Undo(self, *args):
		if self.History.can_undo():
			self.History.revert(self)

	def Action_Redo(self, *args):
		if self.History.can_redo():
			self.History.restore(self)

	def Action_Rename(self, *args):
		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = model.get_iter(current_path)
			model.set_value(current, 2, True)
			column = self.TreeWindow.get_column(0)
			self.TreeWindow.set_cursor(current_path, column, True)
			self.TreeWindow.grab_focus()

	def on_drag_begin(self, treeview, context):
		self.DragInProgress = True
		self.History.snapshot(self, 'drag')	

	def on_drag_end(self, widget, context):
		self.DragInProgress = False
		self.updateProjectTagsFromModel()

	def on_editBuffer_insert_text(self, textbuffer, start,  text, length):
		if self.History.can_record():
			offset = start.get_offset()
			self.History.insert(offset, text)

	def on_editBuffer_delete_range(self, textbuffer, start, end):
		if self.History.can_record():
			offset = start.get_offset()
			text = self.EditWindow.get_buffer().get_text(start, end, True)
			self.History.delete(offset, text)

	def on_cell_edited(self, cell, path, text):
		node = self.tagTree.get_iter(path)
		block_id = self.tagTree.get_value(node, 1)
		if block_id > 0:
			self.ModifyBlock(block_id, text, None)
		else:
			self.History.snapshot(self, 'rename:{}'.format(repr(text)))
			self.tagTree.set_value(node, 0, text)
