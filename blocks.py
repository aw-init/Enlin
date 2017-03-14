import xml.etree.ElementTree as etree

from xml.dom import minidom

import re

class BlockFormatError(RuntimeError):
	pass

def pretty_render(xml):
	xmlstr = etree.tostring(xml)
	domtree = minidom.parseString(xmlstr)
	domstr = domtree.toprettyxml(indent="\t")
	return domstr
	

class Note(object):
	def __init__(self, blocks=None):
		if blocks is not None:
			self._max_id = max(blocks.keys())
			self._blocks = blocks
		else:
			self._max_id = 1
			self._blocks = {}

	def __getitem__(self, key):
		return self._blocks[key]

	def __repr__(self):
		return 'Note({0})'.format(repr(self._blocks))

	def as_dict(self):
		return [x.as_dict() for x in self._blocks]

	def as_xml(self):
		document = etree.Element('document')
		for block in self._blocks.values():
			block_elem = block.as_xml()
			document.append(block_elem)
		return document

	def __iter__(self):
		return iter(self._blocks.values())

	def add_block(self, block):
		self._blocks[block.block_id] = block

	def save(self, flname):
		xml = self.as_xml()	
		with open(flname, 'w') as fl:
			fl.write(pretty_render(xml))

	def save_stdout(self):
		print(pretty_render(self.as_xml()))
			

	@staticmethod
	def Open(flname):
		return Note.FromXml(etree.parse(flname).getroot())

	@staticmethod
	def FromXml(document):
		assert(document.tag == 'document')
		output = {}
		for block_elem in document:
			if block_elem.tag == 'block':
				block = Block.FromXml(block_elem)
				output[block.get_id()] = block
			else:
				raise BlockFormatError("Unknown tag document/{0}".format(block_elem.tag))

		return Note(output)


class NoteLink(object):
	def __init__(self):
		self._links = {}

	def __iter__(self):
		return iter(self._links)

	def __getitem__(self, key):
		return self._links.get(key, set())

	def items(self):
		return iter(self._links.items())

	def add_link(self, bid, *tags):
		for tag in tags:
			if bid not in self._links:
				self._links[bid] = set()		
			if tag != "":
				self._links[bid].add(tag)

	@staticmethod
	def FromModel(model):
		tree = Tree.FromModel(model)
		return NoteLink.FromTree(tree)

	@staticmethod
	def FromTree(tree, link=None, current_tag=""):
		link = NoteLink() if link is None else link
		if current_tag != "":
			for block_id in tree.values():
				link.add_link(block_id, current_tag)
		for name, child in tree.children():
			new_tag = '{}/{}'.format(current_tag, name)
			link = NoteLink.FromTree(child, link, new_tag)
		return link

class Block(object):
	def __init__(self, block_id, title, tags, text):
		self._block_id = block_id
		self._title = title
		self._tags = list(tags)
		self._text = text

	def __repr__(self):
		return 'Block(title="{0}")'.format(self._title)

	def get_id(self):
		return self._block_id

	def get_title(self):
		return self._title
	def set_contents(self, title=None, text=None):
		if title is not None:
			self._title = title
		if text is not None:
			self._text = text

	def get_text(self):
		return self._text

	def has_tags(self):
		return len(self._tags) > 0
	def iter_tags(self):
		return iter(self._tags)

	def as_edit_text(self):
		return self._title+ '\n' + self._text

	def as_xml(self):
		block_elem = etree.Element('block')
		block_elem.set('id', str(self._block_id))

		title = etree.SubElement(block_elem, 'title')
		title.text = self._title

		for tag in self._tags:
			assert(tag is not None and tag != "")
			tag_elem = etree.SubElement(block_elem, 'tag')
			tag_elem.text = tag

		text = etree.SubElement(block_elem, 'text')
		text.text = self._text

		return block_elem


	@staticmethod
	def ParseEditText(text):
		first_newline = text.index('\n')
		title = text[:first_newline].strip()
		contents = text[first_newline:].strip()
		return title, contents

	@staticmethod
	def FromXml(elem):
		assert(elem.tag == 'block')
		title = ''
		tags = []
		text = ''
		block_id = int(elem.attrib['id'])
		for node in elem:
			if node.tag == 'tag':
				tags.append(node.text)
			elif node.tag == 'title':
				title = node.text
			elif node.tag == 'text':
				text = node.text
			else:
				raise BlockFormatError("Unknown tag document/block/{0}".format(node.tag))
		return Block(block_id, title, tags, text)
				


class Tree(object):
	def __init__(self):
		self._blocks = []
		self._children = {} # tag => block_id

	def __str__(self):
		blockstr = ','.join(str(x) for x in self._blocks)
		childstr = ','.join(self._children.keys())
		return '({})=>[{}]'.format(blockstr, childstr)

	def append(self, value):
		self._blocks.append(value)

	def __contains__(self, key):
		return key in self._children

	def __setitem__(self, key, value):
		self._children[key] = value

	def __getitem__(self, key):
		return self._children[key]

	def values(self):
		return iter(self._blocks)

	def children(self):
		return self._children.items()

	def add_tag(self, tag, bid):
		self.add_tag_list(tag.split('/'), bid)

	def add_tag_list(self, tagseq, value):
		if len(tagseq) == 0:
			self.append(value)
		elif tagseq[0] in self:
			node = self[tagseq[0]]
			node.add_tag_list(tagseq[1:], value)
		else:
			node = Tree()
			self[tagseq[0]] = node
			node.add_tag_list(tagseq[1:], value)

	def as_hierarchy(self):
		output = {}
		for (tag, child) in self.children():
			output[tag] = child.as_hierarchy()
		return output

	def as_xml(self):
		elem = etree.Element('node')
		blocks = ' '.join(str(x) for x in self._blocks)
		elem.set('blocks', blocks)
		for child in self._children.values():
			elem.append(child.as_xml())
		return elem		

	@staticmethod
	def FromNote(note):
		root = Tree()
		for block in note:
			if block.has_tags():
				for tag in block.iter_tags():
					tagls = tag.split('/')
					root.add_tag_list(tagls, block.get_id())
			else:
				root.add_tag_list([], block.get_id())
		return root

	@staticmethod
	def FromModel(model, mnode=None):
		tree = Tree()
		if mnode is None:
			child = model.get_iter_first()
		else:
			child = model.iter_children(mnode)
		while child is not None:
			block_id = model.get_value(child, 1)
			if block_id > 0:
				tree.append(block_id)

			tag = model.get_value(child, 0)
			if model.iter_has_child(child):
				tree[tag] = Tree.FromModel(model, child)

			child = model.iter_next(child)
		return tree

class Tag:
	@staticmethod
	def FromModel(model, node):
		tagname = model.get_value(node, 0)
		parent = model.iter_parent(node)
		if parent is not None:
			above = Tag.FromModel(model, parent)
			return '{}/{}'.format(above, tagname)
		else:
			return tagname
		
if __name__ == '__main__':
	note = Note.Open("test.xml")
	note.save_stdout()
	#note.save('test2.xml')
