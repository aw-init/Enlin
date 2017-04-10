import sys
sys.dont_write_bytecode = True

import gi
gi.require_version('Gtk', '3.0')


from app import View

def main():
	app = View()
	sys.exit(app.run(sys.argv))

if __name__ == '__main__':
	main()
