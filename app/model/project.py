import collections
class Project(object):
	def __init__(self, items=None, root=None):
		self.items = items or collections.OrderedDict()
		self.children = root or []

	def get_unique_key(self):
		if len(self.items) > 0:
			return max(self.items.keys()) + 1
		else:
			return 1

	def __getitem__(self, key):
		return self.items[key]

	def add_item(self, item):
		assert(isinstance(item.key, int))
		self.items[item.key] = item

	def append(self, key):
		assert(isinstance(key, int))
		self.children.append(key)

	def copy(self):
		dup = Project()
		for item in self.items.values():
			dup.add_item(item.copy())
		for key in self.children:
			dup.append(key)
		return dup
		

class Item(object):
	def __init__(self, key, title, text, children):
		assert(isinstance(key, int))
		self.key = key
		self.title = title
		self.text = text
		self.children = children
	def append(self, key):
		assert(isinstance(key, int))
		self.children.append(key)
	def copy(self):
		return Item(self.key, self.title, self.text, self.children[:])
	def __str__(self):
		return 'Item({})'.format(self.key)
