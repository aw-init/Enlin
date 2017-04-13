import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio

from .. import resources
from .. import model

GLADE_PATH = "gui.glade"
KEY_TARGET_ID = 0 # arbitrary number

class Application(Gtk.Application):
	def __init__(self):
		super(Application, self).__init__(
			application_id="app.enlin",
			flags=Gio.ApplicationFlags.FLAGS_NONE)
		self.Gui = None
		self.DragSource = None

	def do_activate(self):
		Gtk.Application.do_activate(self)

		glade = resources.read(GLADE_PATH)
		self.Gui = Gtk.Builder.new_from_string(glade, -1)

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

		# (model) control how tree is rendered
		renderer = Gtk.CellRendererText()
		text_column = Gtk.TreeViewColumn(
			title="Tag",
			cell_renderer=renderer,
			text=0,
			editable=2)
		self.TreeWindow.append_column(text_column)

		drag_actions = Gdk.DragAction.MOVE

		targets = [('text/plain', Gtk.TargetFlags.SAME_WIDGET, KEY_TARGET_ID)]
		self.TreeWindow.enable_model_drag_source(
			Gdk.ModifierType.BUTTON1_MASK,
			targets,
			drag_actions)
		self.TreeWindow.enable_model_drag_dest(targets, drag_actions)

		
		self.TreeWindow.connect_after("drag_begin", self.__on_drag_begin)
		self.TreeWindow.connect('drag-data-get', self.__on_drag_data_get)
		self.TreeWindow.connect('drag-data-received', self.__on_drag_data_received)

		self.drag_label = Gtk.Label("")
		self.drag_widget = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
		self.drag_widget.set_border_width(0)
		self.drag_widget.add(self.drag_label)
		self.drag_widget.set_decorated(False)
		self.drag_label.show()

		self.editAccelerators = self.Gui.get_object("editShortcuts")
		self.treeContextPopup = self.Gui.get_object('treeContextPopup')

	def __on_drag_begin(self, widget, context):
		store, selected = widget.get_selection().get_selected_rows()
		if len(selected) > 0:
			current_path = selected[0]
			current = store.get_iter(current_path)
			title = model.get_title(store, current)
			self.drag_label.set_text(title)
			Gtk.drag_set_icon_widget(context, self.drag_widget, 0, 0)

	def __on_drag_data_get(self, widget, context, data, info, time):
		if info == KEY_TARGET_ID:
			store, selected = widget.get_selection().get_selected_rows()
			if len(selected) > 0:
				current_path = selected[0]
				current = store.get_iter(current_path)
				self.DragSource = current
				key = model.get_key(store, current)
				data.set_text(str(key), -1)
				return
			else:
				raise RuntimeError('TreeView drag source has nothing selected')

	def __on_drag_data_received(self, widget, context, x, y, data, info, time):
		drop_dest = widget.get_dest_row_at_pos(x, y)
		text = data.get_text()
		if text is not None:
			key = int(text)
			store = widget.get_model()
			self.on_drop_block(store, self.DragSource, drop_dest, key)
		else:
			raise RuntimeError('view.gui: drag_data_received failed, text is None')

	def on_drop_block(self, store, src, dest, key):
		raise NotImplementedError()

	def on_treeWindow_button_press(self, tree, arg):
		if arg.button == 3:
			# tree context window
			menu = self.Gui.get_object('treeContextPopup')
			menu.popup(None, None, None, None, arg.button, Gtk.get_current_event_time())
			return True
		elif self.TreeWindow.get_path_at_pos(arg.x, arg.y) is None:
			# nothing clicked
			self.TreeWindow.get_selection().unselect_all()

	def set_keyboard_shortcut(self, keychord, callback):
		if len(keychord) > 1:
			key, mod = Gtk.accelerator_parse(keychord)
		else:
			key = Gdk.keyval_from_name(keychord)
			mod = Gdk.ModifierType.CONTROL_MASK
		self.editAccelerators.connect(key, mod, 0, callback)

	def create_open_xml_file_chooser(self):
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.MainWindow,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		xmlfilter = Gtk.FileFilter()
		xmlfilter.set_name("Note Xml File")
		xmlfilter.add_mime_type("text/xml")
		fileChooser.add_filter(xmlfilter)

		value = None
		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			value = fileChooser.get_filename()
		fileChooser.destroy()
		return value

	def create_save_file_chooster(self):
		fileChooser = Gtk.FileChooserDialog("Please choose a file",
			self.MainWindow,
            Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

		value = None
		response = fileChooser.run()
		if response == Gtk.ResponseType.OK:
			value = fileChooser.get_filename()
		fileChooser.destroy()
		return value


	def set_edit_text(self, text):
		self.EditWindow.get_buffer().set_text(text, -1)
