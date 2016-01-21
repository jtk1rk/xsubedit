import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

class cTextResultWin(Gtk.Window):
    def __init__(self, parent, caption, text):
        super(cTextResultWin, self).__init__()
        self.parent = parent
        self.set_title(caption)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(600, 500)
        textview = Gtk.TextView()
        button_close = Gtk.Button("Close")
        vbox = Gtk.VBox()
        scrWin = Gtk.ScrolledWindow()
        scrWin.add(textview)
        vbox.pack_start(scrWin, True, True, 3)
        vbox.pack_start(button_close, False, False, 0)
        self.add(vbox)
        self.connect('key-release-event', self.on_key_release)
        button_close.connect('clicked', self.on_button_close_clicked)
        textview.get_buffer().set_text(text)
        textview.set_property('editable', False)
        textview.set_property('can-focus', False)
        self.show_all()
        self.show()

    def on_key_release(self, sender, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def on_button_close_clicked(self, sender):
        self.destroy()
