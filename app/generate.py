import data
import sys
import jinja2
import resources

env = jinja2.Environment(
	loader=jinja2.PackageLoader('app', 'resources'),
	autoescape=jinja2.select_autoescape(['html', 'xml']))

def render_project(project):
	element = data.Element.FromProject(project)
	template = env.get_template("basic.html")
	return template.render(blocks=_translate(project, element))
	
def _translate(project, element):
	if element.is_root():
		return [_translate(project, child) for child in element.children()]
	elif element.is_block():
		block = project.get_block(element.block_id)
		return {'name': element.name, 'text': block.text}
	else:
		children = [_translate(project, child) for child in element.children()]
		return {'name': element.name, 'children': children}
