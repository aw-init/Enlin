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
			block = parse_block(element)
			project.add_item(block)

		elif element.tag == 'main':
			for child in element:
				key = int(child.attrib.get('id', None) or child.text.strip())
				project.append(key)
		else:
			raise RuntimeError('Unknown tag {}'.format(element.tag))		
	return project

def parse_block(element):
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

def render_project(project):
	document = etree.Element('document')
	raise NotImplementedError()
