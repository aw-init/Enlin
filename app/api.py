from gi.repository import Gtk
import neodata as data

#type project: contains information about blocks and how they fit together
#type cache: contains all the information neccesary to rebuild the project or some subset of it.

# control the format of the gui
def model():
	"title, key, is_tag, editable"
	return Gtk.TreeStore(str, int, bool, bool)

# save information-complete cache of the current project
def record_cache(project):
	pass
# update the gui from a cache
# update the project from a cache

# update the gui from a project

# find the row containing information about a block by id

# create a new empty project
def create_new_project():
	return data.Project()

# open a project from file
def load_project_from_file(flname):
	with open(flname) as fl:
		text = fl.read()
		return data.parse_project(text)

# write project to xml
# write project as html
# modify the title/text of a specific block by id
# get text of a certain block as a title,text pair

# create new block
# add block to current project
# remove block from specific tree
