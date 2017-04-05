import xml.etree.ElementTree as etree
import re
import itertools, collections
import json

class BlockFormatError(RuntimeError):
	pass

from xml.dom import minidom
def pretty_render(xml):
	if isinstance(xml, etree.ElementTree):
		xml = xml.getroot()
	xmlstr = etree.tostring(xml)
	domtree = minidom.parseString(xmlstr)
	domstr = domtree.toprettyxml(indent="\t")
	return domstr

def pretty_json(value):
	return json.dumps(value, indent=4, sort_keys=True)

def join(source, base):
	if source == "":
		return base
	elif base == "":
		return source
	else:
		return '{}/{}'.format(source, base)

class Data(object):
	def __str__(self):
		return pretty_render(self.as_xml())
	def as_xml(self):
		raise NotImplementedError()
	
class Project(Data):
	def __init__(self, contents=None):
		if contents is None:
			contents = []
		self._blocks = dict((block.get_id(), block) for block in contents)

	def __iter__(self):
		return iter(self._blocks.values())

	def get_unique_id(self):
		if len(self._blocks) > 0:
			max_id = max(self._blocks.keys())
			return max_id + 1
		else:
			return 1

	def using_id(self, bid):
		return bid in self._blocks.keys()
	def add_block(self, block):
		self._blocks[block.get_id()] = block
	def remove_block(self, block_id):
		del self._blocks[block_id]

	def get_block(self, key):
		return self._blocks.get(key)

	def remove_block(self, key):
		del self._blocks[key]

	def as_xml(self):
		document = etree.Element('document')
		for block in self._blocks.values():
			block_elem = block.as_xml()
			document.append(block_elem)
		return document	

	def merge_with_project(self, other):
		for block in other:
			block_id = block.get_id()
			if block_id in self._blocks:
				self._blocks[block_id].tags.update(block.tags)
			else:
				self.add_block(block)

	@staticmethod
	def FromFile(flname):
		return Project.FromXml(etree.parse(flname).getroot())

	@staticmethod
	def FromXml(document):	
		result = Project()
		for block_elem in document:
			if block_elem.tag == 'block':
				block = Block.FromXml(block_elem)
				result.add_block(block)
			else:
				raise BlockFormatError("Unknown tag document/{0}".format(block_elem.tag))
		return result
	@staticmethod
	def FromCache(cache, project=None):
		if project is None:
			project = Project()

		for struct in cache['blocks']:
			block = Block.FromJson(struct)
			project.add_block(block)

		for name, child in cache['children']:
			Project.FromCache(child, project)
		return project
	
class Block(Data):
	def __init__(self, bid, title, tags, text):
		self._block_id = int(bid)
		self._title = str(title)
		self._tags = {str(x) for x in tags}
		assert(len(self._tags) > 0)
		self._text = str(text)
		

	def __eq__(self, other):
		return isinstance(other, Block) and self.get_id() == other.get_id()
	@property
	def tags(self):
		return self._tags

	@tags.setter
	def tags(self, value):
		self._tags = {str(x) for x in value}

	def get_id(self):
		return self._block_id

	@property
	def title(self):
		return self._title
	@title.setter
	def title(self, value):
		self._title = value

	@property
	def text(self):
		return self._text
	@text.setter
	def text(self, value):
		self._text = value

	def as_xml(self):
		block_elem = etree.Element('block')
		block_elem.set('id', str(self._block_id))

		title = etree.SubElement(block_elem, 'title')
		title.text = self._title

		for tag in self._tags:
			tag_elem = etree.SubElement(block_elem, 'tag')
			tag_elem.text = tag

		text = etree.SubElement(block_elem, 'text')
		text.text = self._text

		return block_elem

	def as_edit_text(self):
		return '{}\n{}'.format(self._title, self._text)

	def as_json(self):
		return {
			'id' : self._block_id,
			'title' : self._title,
			'tags' : [str(x) for x in self._tags],
			'text' : self._text
		}

	@staticmethod
	def FromJson(cache):
		return Block(cache['id'], cache['title'], cache['tags'], cache['text'])
	@staticmethod
	def ParseEditableText(txt):
		if '\n' in txt:
			i = txt.index('\n')
			title = txt[:i]
			text = txt[i+1:]
			return title, text
		else:
			return txt, ''

	@staticmethod
	def FromXml(elem):
		assert(elem.tag == 'block')
		title = ''
		tags = []
		text = ''
		block_id = int(elem.attrib['id'])
		for node in elem:
			if node.tag == 'tag':
				tags.append(node.text or '')
			elif node.tag == 'title':
				title = node.text
			elif node.tag == 'text':
				text = node.text
			else:
				raise BlockFormatError("Unknown tag document/block/{0}".format(node.tag))
		return Block(block_id, title, tags, text)

class Element(Data):
	def __init__(self, value='', block_id=None):
		if block_id is None:
			self._row = [value, -1, False]
		else:
			self._row = [value, block_id, False]
		self._blocks = [] # [Element]
		self._children = collections.OrderedDict() # str => [Element]

	def __repr__(self):
		if self.is_block():
			return 'block#{}'.format(self.block_id)
		else:
			return '[{}: {}]'.format(self.name,
				', '.join(repr(x) for x in self.children()))

	def match(self, model, node):
		if self.is_block():
			return model.get_value(node, 1) == self.block_id
		else:
			return model.get_value(node, 0) == self.name

	def add_child(self, elem):
		if elem.is_block():
			self._blocks.append(elem)
		else:
			self._children[elem.name] = elem

	def get_child(self, key):
		return self._children.get(key)

	def is_block(self):
		return self._row[1] > 0
	def is_root(self):
		return not self.is_block() and self.name == ''

	@property
	def name(self):
		return self._row[0]

	@property
	def block_id(self):
		return self._row[1]

	@property
	def row(self):
		return self._row[:]

	def children(self):
		return itertools.chain(iter(self._blocks), iter(self._children.values()))

	def as_xml(self):
		if self.is_block():
			elem = etree.Element('tag')
			elem.set('id', str(self.block_id))
		elif self.name == '':
			elem = etree.Element('root')
		else:
			elem = etree.Element(self.name)

		for child in self.children():
			elem.append( child.as_xml() )
		return elem

	@staticmethod
	def FromProject(project):
		tree = Element()
		for block in project:
			for tag in block.tags:
				if tag == '':
					tagls = []
				else:
					tagls = tag.split('/')
				Element.AddBlock(tree, tagls, block)
		return tree

	@staticmethod
	def AddBlock(tree, path, block):
		if len(path) == 0:
			child = Element.FromBlock(block)
			tree.add_child(child)
		else:
			tagname = path[0]
			child = tree.get_child(tagname)
			if child is None:
				child = Element(tagname)
				tree.add_child(child)
			Element.AddBlock(child, path[1:], block)

	@staticmethod
	def FromBlock(block):
		return Element(block.title, block.get_id())

	@staticmethod	
	def FromModel(model, treeiter=None):
		if treeiter is None:
			elem = Element()
			node = model.get_iter_first()
		elif model.get_value(treeiter, 1) > 0:
			name = model.get_value(treeiter, 0)
			bid = model.get_value(treeiter, 1)
			return Element(name, bid)
		else:
			name = model.get_value(treeiter, 0)
			elem = Element(name)
			node = model.iter_children(treeiter)

		while node is not None:
			elem.add_child(Element.FromModel(model, node))
			node = model.iter_next(node)
		return elem

	@staticmethod
	def Flatten(element, tag='', output=None):
		if output is None:
			output = {}
		
		if element.is_block():
			if element.block_id in output:
				output[element.block_id].append(tag)
			else:
				output[element.block_id] = [tag]

		else:
			new_tag = join(tag, element.name)
			for child in element.children():
				Element.Flatten(child, new_tag, output)

		return output

def path_to(model, node=None):
	if node is None:
		return ''
	else:
		value = model.get_value(node, 1)
		name = '' if value > 0 else model.get_value(node, 0)
		parent = model.iter_parent(node)
		if parent is None:
			return name
		else:
			return join(path_from_model(model, parent), name)

if __name__ == '__main__':
	project = Project.FromFile("test2.xml")
	tree = Element.FromProject(project)
	print tree
