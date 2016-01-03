import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class cMessageDialog(Gtk.MessageDialog):
    def __init__(self, parent, message_type, message):
        super(cMessageDialog, self).__init__(message_format="MessageDialog")
        self.set_property('message-type', message_type)
        self.set_property('text', message)
        self.set_title('Error!')
        self.set_parent(parent)
        self.set_transient_for(parent)
        self.add_button('_OK', Gtk.ResponseType.OK)
        self.set_resizable(False)

