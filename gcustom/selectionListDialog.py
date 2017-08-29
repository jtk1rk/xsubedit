# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

class cSelectionListDialog(Gtk.Dialog):
    def __init__(self, parent, itemList, title = 'Select', header_title = 'Select'):
        super(cSelectionListDialog, self).__init__()
        self.parent = parent
        self.set_title = title
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.set_resizable(False)
        self.itemList = itemList
        self.result = None
        self.header_title = header_title
        self.setup_ui()
        self.show()

    def setup_ui(self):
        # Setup TreeView
        model = Gtk.ListStore(int, str)
        for item in enumerate(self.itemList):
            model.append([item[0], item[1]])

        treeView = Gtk.TreeView(model)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(self.header_title, renderer)
        column.add_attribute(renderer, 'text', 1)
        column.set_expand(True)

        treeView.append_column(column)

        # Add layouts
        self.vbox.add(treeView)

        # Connections
        treeView.connect('button-press-event', self.on_tv_button_press)
        treeView.connect('key-release-event', self.on_key_release)

        # Finally show all widgets
        self.show_all()

    def on_tv_button_press(self, widget, event):
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            res = widget.get_path_at_pos(event.x, event.y)
            if res == None:
                return
            if widget.get_column(0) == res[1]:
                self.result =  widget.get_model()[res[0]][0]
                self.close()

    def on_key_release(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close()
