import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GtkSource, Gio, GObject, GdkPixbuf
import data

class Application(Gtk.Application):
	def __init__(self):
		super(Application, self).__init__(application_id="app.enlinmvc", flags=Gio.ApplicationFlags.FLAGS_NONE)

		self.Gui = None
		self.GuiPath = "gui_txt.glade"

		self.tagTree = Gtk.TreeStore(str, int, bool)
		self.Clipboard = None

	def do_startup(self):
		Gtk.Application.do_startup(self)

	def do_activate(self):
		Gtk.Application.do_activate(self)

		self.Gui = Gtk.Builder()
		self.Gui.add_from_file(self.GuiPath)

		self.Clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

		self.MainWindow = self.Gui.get_object("mainWindow")
		self.MainWindow.set_default_size(800, 600)
		self.MainWindow.set_title("Enlin - Untitled")

		self.add_window(self.MainWindow)
		self.MainWindow.show_all()
		self.MainWindow.present()

		self.EditWindow = self.Gui.get_object("editWindow")
		self.editBuffer = self.EditWindow.get_buffer()

		self.TreeWindow = self.Gui.get_object("treeWindow")

		renderer = Gtk.CellRendererText()
		renderer.connect("edited", self.on_cell_edited)
		text_column = Gtk.TreeViewColumn(
			title="Tag",
			cell_renderer=renderer,
			text=0,
			editable=2)
		self.TreeWindow.append_column(text_column)

		self.TreeWindow.set_reorderable(True)
		self.TreeWindow.set_enable_search(False)
		self.TreeWindow.connect_after("drag_begin", self.__on_drag_begin_icon)
		self.TreeWindow.set_model(self.tagTree)

		self.drag_label = Gtk.Label("")
		self.drag_widget = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
		self.drag_widget.set_border_width(0)
		self.drag_widget.add(self.drag_label)
		self.drag_widget.set_decorated(False)
		self.drag_label.show()

		self.editAccelerators = self.Gui.get_object("editShortcuts")
		self.treeContextPopup = self.Gui.get_object('treeContextPopup')

	def set_keyboard_shortcut(self, keychord, callback):
		if len(keychord) > 1:
			key, mod = Gtk.accelerator_parse(keychord)
		else:
			key = Gdk.keyval_from_name(keychord)
			mod = Gdk.ModifierType.CONTROL_MASK
		self.editAccelerators.connect(key, mod, 0, callback)

	def __on_drag_begin_icon(self, source_widget, drag_context):
		model, selected = self.TreeWindow.get_selection().get_selected_rows()
		text = model.get_value(model.get_iter(selected[0]), 0)
		self.drag_label.set_text(text)
		Gtk.drag_set_icon_widget(drag_context, self.drag_widget, 0, 0)

	def on_treeWindow_button_press(self, tree, arg):
		if arg.button == 3:
			# tree context window
			menu = self.Gui.get_object('treeContextPopup')
			menu.popup(None, None, None, None, arg.button, Gtk.get_current_event_time())
			return True
		elif self.TreeWindow.get_path_at_pos(arg.x, arg.y) is None:
			# nothing clicked
			self.TreeWindow.get_selection().unselect_all()

	def get_row(self, node):
		if node is not None:
			return [self.tagTree.get_value(node, i) for i in range(3)]
		else:
			return None

	def copy_row(self, node, row):
		for i in range(3):
			self.tagTree.set_value(node, i, row[i])

	def get_edit_text(self, include_hidden=True):
		textbuffer = self.EditWindow.get_buffer()
		return textbuffer.get_text(
			textbuffer.get_start_iter(),
			textbuffer.get_end_iter(), include_hidden)

	def set_edit_text(self, text):
		self.EditWindow.get_buffer().set_text(text, -1)

	def block_iter(self, prefix='', node=None):
		for (tag, child) in self.model_iter(prefix, node):
			yield (tag, self.tagTree.get_value(child, 1))

	def model_iter(self, prefix='', node=None):
		if node is None:
			node = self.tagTree.get_iter_first()
		while node is not None:
			row = self.get_row(node)
			if row[1] > 0:
				yield (prefix, node)
			else:
				child = self.tagTree.iter_children(node)
				if child is not None:
					subprefix = data.join(prefix, row[0])
					for (tag, subnode) in self.model_iter(subprefix, child):
						yield (tag, subnode)
			node = self.tagTree.iter_next(node)

	def node_iter(self, node=None):
		if node is None:
			node = self.tagTree.get_iter_first()
		while node is not None:
			yield node
			node = self.tagTree.iter_next(node)

	def Gui_Update(self, element, node=None):
		if node is None:
			self.Gui_UpdateChildren(element, node)
		else:
			self.copy_row(node, element.row)
			if not element.is_block() or self.tagTree.iter_has_child(node):
				self.Gui_UpdateChildren(element, node)

	def Gui_UpdateChildren(self, element, parent=None):
		if parent is None:
			current = self.tagTree.get_iter_first()
		else:
			current = self.tagTree.iter_children(parent)

		current_info = {}
		for node in self.node_iter(current):
			row = self.get_row(node)
			key = row[1] if row[1] > 0 else row[0]
			path = self.tagTree.get_path(node)
			expanded = self.TreeWindow.row_expanded(path)
			current_info[key] = expanded

		insert = current
		for child in element.children():
			key  = child.block_id if child.is_block() else child.name
			expanded = current_info.get(key, None)

			if insert is None: # append to end of list
				insert = self.tagTree.append(parent, child.row)
				self.Gui_UpdateChildren(child, insert)
				
			elif not child.is_block(): # insert tag
				self.copy_row(insert, child.row)
				self.Gui_UpdateChildren(child, insert)

			else: # insert block
				insert = self.tagTree.insert_before(parent, insert, child.row)


			if expanded is not None:
				path = self.tagTree.get_path(insert)
				if expanded:
					self.TreeWindow.expand_row(path, False)
				else:
					self.TreeWindow.collapse_row(path)

			insert = self.tagTree.iter_next(insert)

		while insert is not None:
			tmp = self.tagTree.iter_next(insert)
			self.tagTree.remove(insert)
			insert = tmp
				
		
	def Test_Gui_UpdateTree(self, element, parent=None):
		# assume node is the first in a list of elements to correct
		# assume element has already been checked, and look over children
		if parent is None:
			current = self.tagTree.get_iter_first()
			print element
		else:
			current = self.tagTree.iter_children(parent)
		
		for child in element.children():
			if current is None:
				current = self.tagTree.append(parent)

			self.copy_row(current, child.row)

			if not child.is_block():
				self.Gui_UpdateTree(child, current)

			current = self.tagTree.iter_next(current)

		while current is not None:
			tmp = self.tagTree.iter_next(current)
			self.tagTree.remove(current)
			current = tmp
			
	def find_block_rows(self, block_id, node=None):
		if node is None:
			node = self.tagTree.get_iter_first()
		while node is not None:
			if self.tagTree.get_value(node, 1) == block_id:
				yield node
			else:
				child = self.tagTree.iter_children(node)
				if child is not None:
					for result in self.find_block_rows(block_id, child):
						yield result
			node = self.tagTree.iter_next(node)
				
