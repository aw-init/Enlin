import xml.etree.ElementTree as etree
import re
class BlockFormatError(RuntimeError):
	pass

class Note(object):
	def __init__(self, blocks):
		self.blocks = blocks

	def __getitem__(self, key):
		return self.blocks[key]

	def __repr__(self):
		return 'Note({0})'.format(repr(self.blocks))

	def as_dict(self):
		return [x.as_dict() for x in self.blocks]

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
				output[block.block_id] = block
			else:
				raise BlockFormatError("Unknown tag document/{0}".format(block_elem.tag))

		return Note(output)

	@staticmethod
	def Save(note):
		raise NotImplementedError()

class Block(object):
	def __init__(self, block_id, title, tags, text):
		self.block_id = block_id
		self.title = title
		self.tags = list(tags)
		self.text = text

	def __repr__(self):
		return 'Block(title="{0}")'.format(self.title)

	def as_edit_text(self):
		return self.title+ '\n' + self.text

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
		self._children = {}

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

	@staticmethod
	def FromNote(note):
		root = Tree()
		for key, value in note.blocks.items():
			for tag in value.tags:
				tagls = tag.split('/')
				root.add_tag_list(tagls, key)
		return root

	@staticmethod
	def OfModel(model):
		root = Tree()
		child = model.get_iter_first()
		while child is not None:
			val = model.get_value(child, 1)
			if val > -1:
				root.append(val)
			else:
				tag = model.get_value(child, 0)
				root[tag] = Tree.FromModelIter(model, child)
			child = model.iter_next(child)
		return root

	@staticmethod
	def FromModelSubtree(model, root_iter):
		root = Tree()
		tag = model.get_value(root_iter, 0)
		root[tag] = Tree.FromModelIter(model, root_iter)
		return root

	@staticmethod
	def FromModelIter(model, root_iter):
		root = Tree()
		child = model.iter_children(root_iter)
		while child is not None:
			val = model.get_value(child, 1)
			if val > -1:
				root.append(val)
			else:
				tag = model.get_value(child, 0)
				root[tag] = Tree.FromModelIter(model, child)
			child = model.iter_next(child)
		return root

	@staticmethod
	def Flatten(tree, output=None, path=None):
		path = path or []
		output = output if output is not None else {}
		output_id = id(output)

		values = list(tree.values())

		for block_id in values:
			pathstr = '/'.join(path)
			if block_id in output:
				output[block_id].append(pathstr)
			else:
				output[block_id] = [pathstr]
		
		for (tag, child) in tree.children():
			newpath = path + [tag]
			Tree.Flatten(child, output, newpath)

		return output
if __name__ == '__main__':
	note = Note.Open("test.xml")
	tree = Tree.FromNote(note)
	flat = Tree.Flatten(tree)
	print(flat)
