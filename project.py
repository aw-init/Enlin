from gi.repository import Gtk, Gdk, GtkSource, Gio, GObject, GdkPixbuf
import blocks

class Project(object):
	ModelFormat = [GObject.TYPE_STRING, GObject.TYPE_INT, GObject.TYPE_BOOLEAN]
	def __init__(self):
		self.filename =  ""
		self.block_id = 0
		self.note = None
		self.model = Gtk.TreeStore(*Project.ModelFormat)
		self.renaming = None

	def file_is_open(self):
		return self.filename != "" and self.note_is_available()

	def block_is_edited(self):
		return self.block_id > 0

	def note_is_available(self):
		return self.note is not None

	def new_note(self):
		self.filename = ""
		self.note = blocks.Note()
		self.block_id = 0

	def open_note(self, flname):
		self.filename = flname
		self.note = blocks.Note.Open(flname)

	def save_note(self, flname):
		if self.note_is_available():
			return self.note.save(flname)

	def close_note(self):
		self.filename = ""
		self.note = None
		self.block_id = 0

	def get_unique_id(self):
		self.note.max_id += 1
		return self.note.max_id

	def stop_edit(self):
		self.block_id = 0

	def edit_block(self, bid):
		self.block_id = bid

	def get_block(self, bid):
		if self.note_is_available():
			return self.note[bid]

	def get_current_block(self):
		if self.block_is_edited() and self.note_is_available():
			return self.get_block(self.block_id)

	def model_as_tree(self):
		return blocks.Tree.OfModel(self.model)

	def model_as_flat(self):
		return blocks.Tree.Flatten(self.model_as_tree())

	def row(self, s, i=-1, b=False):
		return [s, i, b]
		
