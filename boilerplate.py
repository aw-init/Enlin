import gi
gi.require_version('Gtk', '3.0')

import sys
from gi.repository import Gtk, Gdk, GtkSource, Gio, GObject, GdkPixbuf
import blocks
import project

"""
# bookmarks
https://lazka.github.io/pgi-docs/
http://faq.pygtk.org/index.py?file=faq13.010.htp&req=show
"""

class Application(Gtk.Application):
	def __init__(self, gui_flname):
		super(Application, self).__init__(
			application_id="app.enlin",
			flags=Gio.ApplicationFlags.FLAGS_NONE)
		GObject.type_register(GtkSource.View)
		self.Gui = None
		self.GuiPath = gui_flname
		self.Project = project.Project()

	def do_startup(self):
		Gtk.Application.do_startup(self)

	def do_activate(self):
		Gtk.Application.do_activate(self)

		self.Gui = Gtk.Builder()
		self.Gui.add_from_file(self.GuiPath)
		self.Gui.connect_signals(self)

		self.mainWindow = self.Gui.get_object("mainWindow")
		self.mainWindow.set_default_size(800, 600)

		self.add_window(self.mainWindow)
		self.mainWindow.show_all()
		self.mainWindow.present()

		self.editWindow = self.Gui.get_object("editWindow")

		self.treeWindow = self.Gui.get_object("treeWindow")

		renderer = Gtk.CellRendererText()
		renderer.connect("edited", self.on_cell_edited)
		text_column = Gtk.TreeViewColumn(
			title="Tag",
			cell_renderer=renderer,
			text=0,
			editable=2)
		self.treeWindow.append_column(text_column)

		self.treeWindow.set_model(self.Project.model)
		self.treeWindow.set_reorderable(True)
		self.treeWindow.connect_after("drag_begin", self.on_drag_begin)
		self.treeWindow.set_enable_search(False)
		self.treeContextPopup = self.Gui.get_object('treeContextPopup')

		self.drag_label = Gtk.Label("")
		self.drag_widget = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
		self.drag_widget.set_border_width(0)
		self.drag_widget.add(self.drag_label)
		self.drag_widget.set_decorated(False)
		self.drag_label.show()

	def on_drag_begin(self, source_widget, drag_context):
		model, selected = self.treeWindow.get_selection().get_selected_rows()
		assert(len(selected) >= 1)
		text = model.get_value(model.get_iter(selected[0]), 0)
		self.drag_label.set_text(text)
		Gtk.drag_set_icon_widget(drag_context, self.drag_widget, 0, 0)

def main(app):
	exit_status = app.run(sys.argv)
	sys.exit(exit_status)

