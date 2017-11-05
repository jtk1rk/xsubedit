import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, GObject
from model import Model
from view import View
from controller import Controller
import sys

GObject.threads_init()
win = Controller(Model(), View('xSubEdit 1.9.9-1'))
Gtk.main()
sys.exit(1)
