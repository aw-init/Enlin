import sys
sys.dont_write_bytecode = True
toplevel_module = "behaviour"
app = __import__(toplevel_module).Application()

sys.exit(app.run(sys.argv))
