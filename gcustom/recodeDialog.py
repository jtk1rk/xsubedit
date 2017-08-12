import gi
gi.require_version('Gtk', '3.0')
from os.path import exists
from gi.repository import Gtk
from progressBar import cProgressBar
from cffmpeg import cffmpeg
from gcustom.messageDialog import cMessageDialog

class cRecodeDialog(Gtk.Window):
    def __init__(self, parent, filename, new_filename, ffmpeg_cmd, title):
        super(cRecodeDialog, self).__init__()
        self.parent = parent
        self.set_title(title)
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.progressBar = cProgressBar()
        self.add(self.progressBar)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.new_filename = new_filename.decode('utf-8')
        self.filename = filename.decode('utf-8')
        self.ffmpeg = cffmpeg(ffmpeg_cmd.replace('SOURCEFILE', self.filename).replace('DESTFILE', self.new_filename))
        self.ffmpeg.connect('progress', self.ffmpeg_progress)
        self.result = False

    def ffmpeg_progress(self, sender, value):
        self.set_progress(float(value))

    def run(self):
        self.show()
        self.process_messages()
        self.ffmpeg.run()
        if exists(self.new_filename):
            self.result = True
        else:
            messageDialog = cMessageDialog(self, Gtk.MessageType.ERROR, "Could not generate a compatible video file.")
            messageDialog.run()
            messageDialog.destroy()
            self.result = False
        self.destroy()

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
