from .. import model
class SnapshotController(object):
	def __init__(self):
		self._past = []
		self._future = []
		self._locked = False

	def debug(self):
		print 'SnapshotController'
		if len(self._future) > 0:
			print 'redo'
			for inst in self._future:
				print '   ',inst
		if len(self._past) > 0:
			print 'undo'
			for inst in reversed(self._past):
				print '   ', inst

	def can_record(self):
		return not self._locked

	def lock(self):
		return self
	def __enter__(self):
		self._locked = True
	def __exit__(self, *args):
		self._locked = False

	def reset(self):
		if self.can_record():
			self._past = []
			self._future = []

	def insert(self, offset, text):
		self.push(Insertion(offset, text))

	def delete(self, offset, text):
		self.push(Deletion(offset, text))

	def record(self, name, data):
		self.push(Snapshot(name, data))

	def push(self, other):
		if self.can_record():
			if len(self._past) > 0 and self._past[-1].can_merge(other):
				self._past[-1].merge(other)
			else:
				self._past.append(other)
			self._future = []

	def revert(self, data):
		# make present state of owner be equal to a past snapshot
		if not self._locked and len(self._past) > 0:
			instant = self._past.pop()

			# record present as the near future
			if isinstance(instant, Insertion) or isinstance(instant, Deletion):
				present = instant
			else:
				present = Snapshot('~'+instant.name, data)
			self._future.append(present)

			# get the last past state and change the present to be that past
			with self.lock():
				instant.apply(data, undo=True)

	def restore(self, data):
		if not self._locked and len(self._future) > 0:
			future = self._future.pop()
			if isinstance(future, Insertion) or isinstance(future, Deletion):
				present = future
			else:
				present = Snapshot('~'+future.name, data)
			self._past.append(present)
			with self.lock():
				future.apply(data, undo=False)

class Operation(object):
	def can_merge(self, op):
		return False
	def merge(self, other):
		raise NotImplementedError()
	def apply(self, owner, undo=True):
		raise NotImplementedError()

class Insertion(Operation):
	def __init__(self, offset, text):
		self.offset = offset
		self.text = text

	def __str__(self):
		return '+[{}]{}'.format(self.offset, repr(self.text))

	def can_merge(self, other):
		return (isinstance(other, Insertion) and
			self.offset + len(self.text) == other.offset and
			len(other.text) == 1)

	def merge(self, other):
		self.text += other.text

	def apply(self, controller, undo=True):
		buff = controller.edit_buffer
		if undo:
			start = buff.get_iter_at_offset(self.offset)
			stop = buff.get_iter_at_offset(self.offset + len(self.text))
			buff.delete(start, stop)
		else:
			start = buff.get_iter_at_offset(self.offset)
			buff.insert(start, self.text)

class Deletion(Operation):
	def __init__(self, offset, text):
		self.offset = offset
		self.text = text

	def __str__(self):
		return '-[{}]{}'.format(self.offset, repr(self.text))

	def can_merge(self, other):
		return (isinstance(other, Deletion) and
			len(other.text) == 1 and
			other.offset + len(other.text) == self.offset)

	def merge(self, other):
		self.offset = other.offset
		self.text = other.text + self.text

	def apply(self, controller, undo=True):
		buff = controller.edit_buffer
		if undo:
			start = buff.get_iter_at_offset(self.offset)
			buff.insert(start, self.text)
		else:
			start = buff.get_iter_at_offset(self.offset)
			stop = buff.get_iter_at_offset(self.offset + len(self.text))
			buff.delete(start, stop)

class Snapshot(Operation):
	def __init__(self, name, data):
		self.name = name
		self.project = data.project.copy()
		self.text = data.get_edit_text()
		self.edited = data.edited
		self.filename = data.filename

	def __str__(self):
		return self.name

	def apply(self, data, undo=True):
		data.set_edit_text(self.text)
		data.edited = self.edited
		data.filename = self.filename
		data.project = self.project
		model.update_treemodel(data.treemodel, data.project)
