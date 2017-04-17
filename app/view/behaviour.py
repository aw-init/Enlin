from . import gui
from .. import controller
from .. import model

class Application(gui.Application):
	def __init__(self):
		super(Application, self).__init__()

	def do_activate(self):
		super(Application, self).do_activate()
		self.Data = controller.DataController(self.EditWindow.get_buffer())

		self.TreeWindow.set_model(self.Data.treemodel)

		self.Gui.connect_signals(self)
		
		self.set_keyboard_shortcut("<Control>Z", self.Action_Undo)
		self.set_keyboard_shortcut("<Control>P", self.debug_project)
		self.set_keyboard_shortcut("<Control>S", self.debug_save)
		self.set_keyboard_shortcut("<Control>U", self.debug_undo_manager)
		
		self.set_keyboard_shortcut("<Control>C", self.on_ctrlc_element)
		self.set_keyboard_shortcut("<Control>X", self.on_ctrlx_element)
		self.set_keyboard_shortcut("<Control>V", self.on_ctrlv_element)
		self.Data.Open()

	def debug_undo_manager(self, *args):
		self.Data.history.debug()

	def debug_save(self, *args):
		self.Data.project.clean()

	def debug_project(self, *args):
		self.Data.project.debug()

	def on_editBuffer_insert_text(self, textbuffer, start,  text, length):
		offset = start.get_offset()
		self.Data.RecordInsertion(start.get_offset(), text)

	def on_editBuffer_delete_range(self, textbuffer, start, end):
		offset = start.get_offset()
		text = self.EditWindow.get_buffer().get_text(start, end, True)
		self.Data.RecordDeletion(offset, text)

	def on_treeWindow_row_activated(self, tree, *arg):
		self.Action_Edit()

	def on_drop_block(self, store, src, dest_path, key):
		self.Data.AddElement(store, key, src, dest_path)

	def on_ctrlc_element(self, accel, window, info, modifier):
		if window.get_focus() == self.TreeWindow:
			self.Action_CopyElement()
			return True

	def on_ctrlx_element(self, accel, window, info, modifier):
		if window.get_focus() == self.TreeWindow:
			self.Action_CutElement()
			return True

	def on_ctrlv_element(self, accel, window, info, modifier):
		if window.get_focus() == self.TreeWindow:
			self.Action_PasteElement()
			return True

	# Actions
	def Action_AppendChild(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		parent = None
		if len(selected) > 0:
			current_path = selected[0]
			parent = store.get_iter(current_path)
		title = self.create_text_entry_dialog('Enter block title:')
		self.Data.CreateElement(store, parent, None, title)

	def Action_CopyElement(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			key = model.get_key(store, current)
			self.Data.WriteElementToClipboard(self.Clipboard, key)

	def Action_CopyText(self, *args):
		buff = self.EditWindow.get_buffer()
		selection = buff.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = buff.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)

	def Action_CutElement(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			key = model.get_key(store, current)
			self.Data.WriteElementToClipboard(self.Clipboard, key)
			self.Data.RemoveElement(store, current)	

	def Action_CutText(self, *args):
		buff = self.EditWindow.get_buffer()
		selection = buff.get_selection_bounds()
		if selection is not None:
			(start, stop) = selection
			text = buff.get_text(start, stop, True)
			self.Clipboard.set_text(text, -1)
			buff.delete(start, stop)

	def Action_DeleteElement(self, *args):
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			self.Data.RemoveElement(store, current)	

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
		title = self.create_text_entry_dialog('Enter block title:')
		self.Data.CreateElement(store, None, sibling, title)

	def Action_New(self, *args):
		self.Data.open_project()

	def Action_Open(self, *args):
		flname = self.create_open_xml_file_chooser()
		if flname is not None:
			self.Data.Open(flname)

	def Action_PasteText(self, *args):
		text = self.Clipboard.wait_for_text()
		self.EditWindow.get_buffer().insert_at_cursor(text, -1)

	def Action_PasteElement(self, *args):
		text = self.Clipboard.wait_for_text()
		block = model.parse_item(text)
		store, selected = self.TreeWindow.get_selection().get_selected_rows()
		sibling = None
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			after = Gtk.TreeViewDropPosition.AFTER
			self.Data.AddElement(store, block, None, (current, after))
		
	def Action_Quit(self, *args):
		self.quit()

	def Action_Redo(self, *args):
		self.Data.Redo()

	def Action_Render(self, *args):
		flname = self.create_save_file_chooser()
		if flname is not None:
			self.Data.Render(flname)

	def Action_Save(self, *args):
		self.Data.Save()

	def Action_SaveAs(self, *args):
		flname = self.create_save_file_chooser()
		if flname is not None:
			self.Data.Save(flname)

	def Action_Undo(self, *args):
		self.Data.Undo()
