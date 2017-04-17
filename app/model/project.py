import collections
import json
class Container(object):
	def __init__(self, children):
		self.children = children

class Project(Container):
	def __init__(self, items=None, root=None):
		Container.__init__(self, root or [])
		self.items = items or collections.OrderedDict()

	def debug(self):
		print 'Project'
		for item in self.items.values():
			print '    {}'.format(str(item))
		print '    main: [{}]'.format(', '.join(str(x) for x in self.children))

	def get_unique_key(self):
		if len(self.items) > 0:
			return max(self.items.keys()) + 1
		else:
			return 1

	def __contains__(self, key):
		return key in self.items

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

	def clean(self):
		# remove unreachable blocks
		reachable = set()
		inspect = self.children[:]
		while len(inspect) > 0:
			key = inspect.pop()
			reachable.add(key)
			inspect.extend(self[key].children)
		
		all_keys = set(self.items.keys())
		for key in all_keys.difference( reachable ):
			del self.items[key]
		

class Item(Container):
	def __init__(self, key, title, text, children):
		assert(isinstance(key, int))
		Container.__init__(self, children)
		self.key = key
		self.title = title
		self.text = text

	def __str__(self):
		s = 'Item(key={}, title="{}")'.format(self.key, self.title)
		if len(self.children) > 0:
			s += ' [{}]'.format(', '.join(str(x) for x in self.children))
		return s

	def append(self, key):
		assert(isinstance(key, int))
		self.children.append(key)

	def copy(self):
		return Item(self.key, self.title, self.text, self.children[:])
