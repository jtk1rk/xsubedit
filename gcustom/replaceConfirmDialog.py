# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

#class cReplaceConfirmDialog(Gtk.Window):
class cReplaceConfirmDialog(Gtk.Dialog):
    def __init__(self, parent, text, replaceText, find_pointers):
        super(cReplaceConfirmDialog, self).__init__()

        # Setup Window Properties and Variables
        self.parent = parent
        self.set_title('Confirm Replace')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_size_request(300, 100)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.text = None
        self.replaceText = None
        self.set_resizable(False)
        self.result = 'NO' # returns 'YES', 'NO', 'STOP'

        # Widgets
        textView = Gtk.TextView()
        textView.set_property('can-focus', False)
        textView.set_property('editable', False)
        textView.get_buffer().set_text(text)

        button_stop = Gtk.Button('Stop')
        button_cancel = Gtk.Button('Cancel')
        button_ok = Gtk.Button('OK')

        # Layout
        hbox = Gtk.HBox()
        hbox.add(button_stop)
        hbox.add(button_cancel)
        hbox.add(button_ok)

        self.vbox.pack_start(textView, True, True, 3)
        self.vbox.pack_start(hbox, False, False, 3)

        # Connections
        button_stop.connect('clicked', self.on_button_clicked, 'Stop')
        button_ok.connect('clicked', self.on_button_clicked, 'OK')
        button_cancel.connect('clicked', self.on_button_clicked, 'Cancel')
        self.connect('key-press-event', self.on_key_press)

        # Finally
        iter_start = textView.get_buffer().get_iter_at_offset(find_pointers[0])
        iter_end = textView.get_buffer().get_iter_at_offset(find_pointers[1])
        textView.get_buffer().create_tag('red_background', background = 'red')
        textView.get_buffer().apply_tag_by_name('red_background', iter_start, iter_end)

        self.show_all()
        self.show()

    def on_button_clicked(self, widget, button_name):
        self.result = button_name
        self.hide()

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.result = 'Stop'
            self.hide()
        elif event.keyval == Gdk.KEY_Return:
            self.result = 'OK'
            self.hide()
