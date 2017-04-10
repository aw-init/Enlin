from gi.repository import Gtk, Gdk, Gio

MODEL_TYPE = [str, int, bool]

def create_treemodel():
	return Gtk.TreeStore(*MODEL_TYPE)

def get_title(model, i):
	return model.get_value(i, 0)
def get_key(model, i):
	return model.get_value(i, 1)

def get_row(node):
	return [node.title, node.key, False]

def update_row(model, dest, row):
	for i in range(len(MODEL_TYPE)):
		model.set_value(dest, i, row[i])
	return dest
		
def update_treemodel(model, project, parent=None, group=None):
	group = group or project
	if parent is None:
		insert = model.get_iter_first()
	else:
		insert = model.iter_children(parent)

	pattern_stack = [project[k] for k in group.children]
	pattern_stack.reverse()

	# loop through the items in order and make the current row match
	while len(pattern_stack) > 0:
		current = pattern_stack.pop()
		row = get_row(current)

		if insert is None:
			# there are no more already-existing rows
			insert = model.append(parent, row)

		elif get_key(model, insert) == current.key:
			# the current row already has the same id
			insert = update_row(model, insert, row)

		else:
			# the current row does not match the expected item
			# search the current level to see if the matching row exists
			mvsrc = model.iter_next(insert)
			while mvsrc is not None:
				if get_key(model, mvsrc) == current.key:
					break
				else:
					mvsrc = model.iter_next(mvsrc)

			if mvsrc is None:
				# the matching row does not already exist
				insert = model.insert_before(parent, insert, row)
			else:
				# move the matching row into place
				model.move_before(mvsrc, insert)
				insert = model.iter_previous(insert)

		# recurse and update the children
		update_treemodel(model, project, insert, current)
		insert = model.iter_next(insert)

	# delete remaining unused rows
	while insert is not None:
		tmp = model.iter_next(insert)
		model.remove(insert)
		insert = tmp


def update_element(model, project, group, current=None):
	if current is None:
		current = model.get_iter_first()
	values = get_row(group)

	while current is not None:
		if get_key(model, current) == group.key:
			update_row(model, current, values)
			update_treemodel(model, project, current, group)

		child = model.iter_children(current)
		if child is not None:
			update_element(model, project, group, child)
		current = model.iter_next(current)


def update_group_from_model(model, group, first_child):
	keys = []
	current = first_child
	while current is not None:
		key = get_key(model, current)
		keys.append(key)
		current = model.iter_next(current)
	group.children = keys
	
