import pkg_resources

def join(names):
	return '/'.join(names)

def exists(*names):
	return pkg_resources.resource_exists(__name__, join(names))

def read(*names):
	return pkg_resources.resource_string(__name__, join(names))
