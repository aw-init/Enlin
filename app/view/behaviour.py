from . import gui
from .. import controller
from .. import model

class Application(gui.Application):
	def __init__(self):
		super(Application, self).__init__()
		self.DragInProgress = False
		self.Data = None

	def do_activate(self):
		super(Application, self).do_activate()
		self.Data = controller.DataController(self.EditWindow.get_buffer())

		self.TreeWindow.set_model(self.Data.treemodel)

		self.Gui.connect_signals(self)
		
		self.set_keyboard_shortcut("<Control>Z", self.Action_Undo)

		self.set_keyboard_shortcut("<Control>U", self.debug_undo_manager)
		self.set_keyboard_shortcut("<Control>P", self.debug_project)

		self.Data.Open()

	def debug_undo_manager(self, *args):
		self.Data.history.debug()

	def debug_project(self):
		print self.Data.project

	def on_drag_begin(self, widget, context):
		self.DragInProgress = True

	def on_drag_end(self, widget, context):
		self.DragInProgress = False
		

	def on_editBuffer_insert_text(self, textbuffer, start,  text, length):
		offset = start.get_offset()
		self.Data.RecordInsertion(start.get_offset(), text)

	def on_editBuffer_delete_range(self, textbuffer, start, end):
		offset = start.get_offset()
		text = self.EditWindow.get_buffer().get_text(start, end, True)
		self.Data.RecordDeletion(offset, text)

	def on_treeWindow_row_activated(self, tree, *arg):
		self.Action_Edit()

	def on_copy_block(self, store, src, dest_path, key):
		self.Data.AddElement(store, src, dest_path, key)

	# Actions
	def Action_AppendChild(self, *args):	
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		parent = None
		if len(selected) > 0:
			current_path = selected[0]
			parent = store.get_iter(current_path)
		self.Data.CreateElement(store, parent, None)

	def Action_Commit(self, *args):
		self.Data.Commit()

	def Action_CopyText(self, *args):
		buff = self.EditWindow.get_buffer()
		selection = buff.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = buff.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)

	def Action_CutText(self, *args):
		buff = self.EditWindow.get_buffer()
		selection = buff.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = buff.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)
			buff.delete(start, stop)

	def Action_DeleteText(self, *args):
		buff = self.EditWindow.get_buffer()
		selection = buff.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			buff.delete(start, stop)


	def Action_Edit(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			key = model.get_key(store, current)
			self.Data.Edit(key)
			
	def Action_InsertSibling(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		sibling = None
		if len(selected) > 0:
			current_path = selected[0]
			sibling = store.get_iter(current_path)
		self.Data.CreateElement(store, None, sibling)

	def Action_New(self, *args):
		self.Data.open_project()

	def Action_Open(self, *args):
		flname = self.create_open_xml_file_chooser()
		if flname is not None:
			self.Data.Open(flname)

	def Action_PasteText(self, *args):
		text = self.Clipboard.wait_for_text()
		self.EditWindow.get_buffer().insert_at_cursor(text, -1)

	def Action_Quit(self, *args):
		self.quit()

	def Action_Redo(self, *args):
		self.Data.Redo()

	def Action_RemoveElement(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			self.Data.RemoveElement(store, current)

	def Action_Render(self, *args):
		flname = self.create_save_file_chooster()
		if flname is not None:
			self.Data.Render(flname)

	def Action_Save(self, *args):
		self.Data.Save()

	def Action_SaveAs(self, *args):
		flname = self.create_save_file_chooster()
		if flname is not None:
			self.Data.Save(flname)

	def Action_Undo(self, *args):
		self.Data.Undo()
