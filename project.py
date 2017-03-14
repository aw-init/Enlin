from gi.repository import Gtk, Gdk, GtkSource, Gio, GObject, GdkPixbuf
import blocks

class Project(object):
	ModelFormat = [GObject.TYPE_STRING, GObject.TYPE_INT, GObject.TYPE_BOOLEAN]
	def __init__(self):
		self.filename =  ""
		self.edited_block_id = 0
		self.note = None
		self.model = Gtk.TreeStore(*Project.ModelFormat)
		self.renaming = None

	def __str__(self):
		return blocks.pretty_render(self.note.as_xml())

	def file_is_open(self):
		return self.filename != "" and self.note_is_available()

	def block_is_edited(self):
		return self.edited_block_id > 0

	def note_is_available(self):
		return self.note is not None

	def new_note(self):
		self.filename = ""
		self.note = blocks.Note()
		self.edited_block_id = 0

	def open_note(self, flname):
		self.filename = flname
		self.note = blocks.Note.Open(flname)

	def write_note_to_file(self, flname):
		if self.note_is_available():
			return self.note.save(flname)

	def close_note(self):
		self.filename = ""
		self.note = None
		self.edited_block_id = 0

	def get_unique_id(self):
		self.note.max_id += 1
		return self.note.max_id

	def stop_edit(self):
		self.edited_block_id = 0

	def edit_block(self, bid):
		self.edited_block_id = bid

	def get_block(self, bid):
		if self.note_is_available():
			return self.note[bid]

	def get_current_block(self):
		if self.block_is_edited() and self.note_is_available():
			return self.get_block(self.edited_block_id)	

	def set_block_tags(self, block_id, tags):
		if block_id is None:
			block_id = self.edited_block_id
		block = self.get_block(block_id)
		block.tags = tags

	def set_block_contents(self, block_id, title, text):
		if block_id is None:
			block_id = self.edited_block_id

		block = self.get_block(block_id)
		block.set_contents(title, text)
