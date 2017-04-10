import sys
import jinja2
#from .. import resources

env = jinja2.Environment(
	loader=jinja2.PackageLoader('app', 'resources'),
	autoescape=jinja2.select_autoescape(['html', 'xml']))

def generate_tree(project, key):
	node = project[key]
	return {
		'key' : node.key,
		'title': node.title,
		'text' : node.text,
		'children': [generate_tree(project, x) for x in node.children]
	}

def render_project(project):
	items = [generate_tree(project, x) for x in project.children]
	template = env.get_template('template.html')
	return template.render(blocks=items)
