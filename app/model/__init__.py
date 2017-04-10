def test():
	from . import xmlio
	proj = xmlio.open_xml_resource('tmp_test.xml')
	print(repr(proj))
	print xmlio.render_xml(proj)

from .xmlio import open_xml, render_project
from project import Project, Item
from treemodel import create_treemodel, update_treemodel, update_element
from treemodel import get_key, get_title, get_row
from treemodel import update_group_from_model
