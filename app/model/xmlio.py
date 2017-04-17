from project import Project, Item
import xml.etree.ElementTree as etree


def open_xml(flname, from_resource=False):
	if from_resource:
		return open_xml_resource(flname)
	else:
		with open(flname) as fl:
			return parse_xml(fl.read())

def open_xml_resource(flname):
	from .. import resources
	text = resources.read(flname)
	return parse_xml(text)

def parse_xml(text):
	document = etree.fromstring(text)
	project = Project()
	assert(document.tag == 'document')

	for element in document:
		if element.tag == 'block':
			block = etree_as_item(element)
			project.add_item(block)

		elif element.tag == 'main':
			for child in element:
				key = int(child.attrib.get('id', None) or child.text.strip())
				project.append(key)
		else:
			raise RuntimeError('Unknown tag {}'.format(element.tag))		
	return project

def etree_as_item(element):
	key = int(element.attrib['id'])
	title = str(element.attrib.get('title', ''))
	text = ''
	children = []
	for section in element:
		if section.tag == 'text':
			text = str(section.text)
		elif section.tag == 'child':
			child_key = int(section.attrib['id'])
			children.append(child_key)
	return Item(key, title, text, children)

def parse_item(text):
	element = etree.fromstring(text)
	return etree_as_item(element)

def render_project(project):
	return etree.tostring(project_as_etree(project))

def project_as_etree(project):
	document = etree.Element('document')
	for item in project.items.values():
		tree = item_as_etree(item)
		document.append(tree)
	main = etree.SubElement(document, 'main')
	for key in project.children:
		child = etree.SubElement(main, 'child')
		child.set('id', str(key))
	return document

def render_item(item):
	return etree.tostring(item_as_etree(item))

def item_as_etree(item):
	block = etree.Element('block')
	block.set('id', str(item.key))
	block.set('title', str(item.title))
	text = etree.SubElement(block, 'text')
	text.text = str(item.text)
	for key in item.children:
		child = SubElement(block, 'child')
		child.set('id', str(key))
	return block
