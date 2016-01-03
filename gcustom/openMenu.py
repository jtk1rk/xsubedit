import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, GObject
from os.path import split, exists

class cOpenMenu(GObject.GObject):
    
    __gsignals__ = { 'custom-select': (GObject.SIGNAL_RUN_LAST, None, (str, )) }

    def __init__(self, preferences):
        super(cOpenMenu, self).__init__()
        self.result = None
        self.handler_select = None
        self.menu = Gtk.Menu()

        # Menu Items
        if not 'MRU' in preferences.keys():
            self.menu.show()
            return

        self.menu_items = []

        preferences['MRU'] = [ item for item in preferences['MRU'] if exists(item) ]

        for item in preferences['MRU']:
            menu_item = Gtk.MenuItem(split(item)[1])
            self.menu_items.append((menu_item, menu_item.connect('activate', self.on_item_activate), item))
            self.menu.add(menu_item)
            menu_item.show()

        self.menu.show()

    def on_item_activate(self, sender):
        for item in self.menu_items:
            if item[0] == sender:
                self.result = item[2]
                break
        if self.result != None:
            self.emit('custom-select', item[2])
