import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, GObject
from model import Model
from view import View
from controller import Controller
import sys

#from utils import set_process_name
#set_process_name()

try:
    GObject.threads_init()
    win = Controller(Model(), View('xSubEdit 1.7.4'))
    Gtk.main()
except:
    win.crash_save()
    sys.exit()
