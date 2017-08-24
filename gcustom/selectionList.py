# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

class cSelectionList(Gtk.Window):
    def __init__(self, parent, title, itemsList):
        super(cSelectionList, self).__init__()
        self.parent = parent
        self.set_title = title
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.set_resizable(False)
        self.itemList = itemList
        self.setup_ui()
        self.show()

    def setup_ui(self):
        model = Gtk.ListStore(str)
        for item in self.itemList
            self.model.append(self.vo.text_data[idx])
        
        treeView = Gtk.TreeView(model)
        
        cellRenderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Select', cellRenderer)
        
        treeview.append(column)

        # Add layouts
        vbox = Gtk.VBox()
        vbox.pack_start(treeView, False, False, 3)
        self.add(vbox)

        # Finally show all widgets
        self.show_all()

#    def on_main_button_click(self, sender, sender_name):
#        self.destroy()
