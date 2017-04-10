import api

def indent(s, count=4):
	return s.replace('\n', '\n'+(' '*count))

class Operation(object):
	def try_merge(self, op):
		return False
	def is_delta(self):
		return False
	def apply(self, owner, undo=True):
		raise NotImplementedError()

class Snapshot(Operation):
	def __init__(self, description=None):
		self.description = description or ""
		self.tree = None
		self.edit = None
		self.blocks = None

	def __str__(self):
		return '[{}]'.format(self.description)

	def set_description(self, text):
		self.description = text
		return self

	def record_tree(self, model, node=None):
		self.tree = data.Element.FromModel(model, node)
		return self

	def record_edit_window(self, owner):
		self.edit = {'block':owner.EditedBlockId, 'text':owner.get_edit_text()}
		return self

	def record_project(self, owner):
		self.filename = owner.Filename
		if owner.Project is not None:
			self.blocks = {}
			for block in owner.Project:
				self.blocks[block.get_id()] = block.as_json()

	def record_all(self, owner):
		self.record_tree(owner.tagTree)
		self.record_edit_window(owner)
		self.record_project(owner)
		return self

	def apply(self, owner, undo=True):
		if self.tree is not None:
			owner.Gui_Update(self.tree)
		if self.edit is not None:
			owner.EditedBlockId = self.edit['block']
			owner.set_edit_text(self.edit['text'])
		if self.blocks is not None:
			updated = set()
			for block_id, cache in self.blocks.items():
				block = owner.Project.get_block(block_id)
				if block is None:
					block = data.Block.FromJson(cache)
					owner.Project.add_block(block)
				else:
					block.title = cache['title']
					block.text = cache['text']
					block.tags = cache['tags']
				updated.add(block_id)

			for block in owner.Project:
				block_id = block.get_id()
				if block_id not in updated:
					owner.Project.remove_block(block_id)
			owner.updateProjectTagsFromModel()
		

class Insertion(Operation):
	def __init__(self, offset, text):
		self.offset = offset
		self.text = text

	def __str__(self):
		return '+[{}]{}'.format(self.offset, repr(self.text))

	def is_delta(self):
		return True

	def try_merge(self, other):
		if not isinstance(other, Insertion):
			return False
		if self.offset + len(self.text) == other.offset and len(other.text) == 1:
			self.text += other.text
			return True
		else:
			return False

	def apply(self, owner, undo=True):
		if undo:
			buff = owner.EditWindow.get_buffer()
			start = buff.get_iter_at_offset(self.offset)
			stop = buff.get_iter_at_offset(self.offset + len(self.text))
			buff.delete(start, stop)
		else:
			buff = owner.EditWindow.get_buffer()
			start = buff.get_iter_at_offset(self.offset)
			buff.insert(start, self.text)
		
class Deletion(Operation):
	def __init__(self, offset, text):
		self.offset = offset
		self.text = text

	def __str__(self):
		return '-[{}]{}'.format(self.offset, repr(self.text))

	def is_delta(self):
		return True

	def try_merge(self, other):
		if not isinstance(other, Deletion):
			return False
		else:
			if len(other.text) == 1 and other.offset + len(other.text) == self.offset:
				self.offset = other.offset
				self.text = other.text + self.text
				return True
			else:
				return False
	def apply(self, owner, undo=True):
		if undo:
			buff = owner.EditWindow.get_buffer()
			start = buff.get_iter_at_offset(self.offset)
			buff.insert(start, self.text)
		else:
			buff = owner.EditWindow.get_buffer()
			start = buff.get_iter_at_offset(self.offset)
			stop = buff.get_iter_at_offset(self.offset + len(self.text))
			buff.delete(start, stop)

class History(object):
	def __init__(self):
		self._past = []
		self._future = []
		self._locked = False

	def __str__(self):
		past = [str(x) for x in reversed(self._past)]
		future = [str(x) for x in self._future]
		lines = ['SnapshotStack:'] + future + ['<present>'] + past
		return indent('\n'.join(lines))	

	def can_record(self):
		return not self._locked

	def lock(self):
		self._locked = True

	def unlock(self):
		self._locked = False

	def not_undoable(self):
		if self.can_record():
			return Lock(self)
		else:
			return Guest(self)

	def reset(self):
		if self.can_record():
			self._past = []
			self._future = []

	def insert(self, offset, text):
		if self.can_record():
			delta = Insertion(offset, text)
			if len(self._past) > 0 and self._past[-1].try_merge(delta):
				pass
			else:
				self._past.append(delta)
			self._future = []

	def delete(self, offset, text):
		if self.can_record():
			delta = Deletion(offset, text)
			if len(self._past) > 0 and self._past[-1].try_merge(delta):
				pass
			else:
				self._past.append(delta)
			self._future = []

	def snapshot(self, owner, description=None):
		# record a snapshot of the present
		if self.can_record():
			shot = Snapshot(description).record_all(owner)
			self._past.append(shot)
			self._future = []

	def can_undo(self):
		return not self._locked and len(self._past) > 0

	def revert(self, owner):
		# make present state of owner be equal to a past snapshot
		if self.can_undo():
			instant = self._past.pop()

			# record present as the near future
			if instant.is_delta():
				present = instant
			else:
				present = Snapshot('~'+instant.description).record_all(owner)
			self._future.append(present)

			# get the last past state and change the present to be that past
			with self.not_undoable() as locked:
				instant.apply(owner, undo=True)

	def can_redo(self):
		return not self._locked and len(self._future) > 0

	def restore(self, owner):
		if self.can_redo():
			future = self._future.pop()
			if future.is_delta():
				present = future
			else:
				present = Snapshot('~'+instant.description).record_all(owner)
			self._past.append(present)
			with self.not_undoable() as locked:
				future.apply(owner, undo=False)


class Guest(object):
	def __init__(self, owner):
		self.owner = owner
	def __enter__(self):
		pass
	def __exit__(self, *args):
		pass
	
class Lock(object):
	def __init__(self, stack):
		self.owner = stack

	def __enter__(self):
		self.owner.lock()
		return self

	def __exit__(self, *args):
		self.owner.unlock()
