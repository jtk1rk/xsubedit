import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from .progressBar import cProgressBar

class cProgressBarDialog(Gtk.Window):
    def __init__(self, parent, title, label = ''):
        super(cProgressBarDialog, self).__init__()
        self.parent = parent
        self.set_title(title)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.progressBar = cProgressBar()
        vbox = Gtk.VBox()
        if not ( label == '' ):
            self.lb = Gtk.Label(label)
            vbox.add(self.lb)
        vbox.add(self.progressBar)
        self.add(vbox)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)

    def update_info(self, value):
        if hasattr(self, 'lb'):
            self.lb.set_text(value)

    def update_title(self, value):
        self.set_title(value)

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
