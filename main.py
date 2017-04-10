import sys
sys.dont_write_bytecode = True

import gi
gi.require_version('Gtk', '3.0')


def main():
	from app.view import Application
	app = Application()
	exitcode = app.run(sys.argv)
	sys.exit(exitcode)

def test():
	from app.model import test
	test()

if __name__ == '__main__':
	if '-t' in sys.argv:
		test()
	else:
		main()
