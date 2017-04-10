import xml.etree.ElementTree as etree
import collections

class Project(object):
	def __init__(self):
		self.items = collections.OrderedDict()
		self.tree = None

	def __getitem__(self, key):
		return self.items[key]

	def add(self, item, parent=None):
		self.items[item.key] = item


class Item(object):
	def __init__(self, key, title, text='', children=None):
		self.key = key
		self.title = title
		self.text = text
		self.children = children or []


# represents a tag, block, or group arranged in a tree
# contains only ids that refer back to a project
class Element(object):
	def __init__(self, data, children=None):
		self.data = data
		self.children = children or []

	def add(self, child):
		self.children.append(child)


def parse_project(text):
	document = etree.fromstring(text)
	project = Project()

	for element in document:
		if element.tag == 'block':
			bid = element.attrib['id']
			title = element.attrib.get('title', '')
			text = element.text
			project.add( Item(bid, title, text) )

		elif element.tag == 'group':
			bid = element.attrib['id']
			title = element.attrib.get('title', '')
			children = [child.attrib['id'] for child in element if child.tag == 'child']
			project.add( Item(bid, title, children=children) )

		elif element.tag == 'hierarchy':
			project.tree = parse_hierarchy(element)

		else:
			raise RuntimeError('Unknown element {}'.format(element.tag))
	return project

def parse_hierarchy(element, title=None):
	children = []
	for child in element:
		if child.tag == 'tag':
			children.append(parse_hierarchy(child, child.attrib['title']))

		elif child.tag == 'block':
			children.append(Element(child.attrib['id']))

		elif child.tag == 'group':
			children.append(Element(child.attrib['id']))

		else:
			raise RuntimeError('Unknown element {}'.format(child.tag))

	return Element(title, children)

def main():
	import resources
	text = resources.read('tmp_test.xml')
	result = parse_project(text)
	print result
