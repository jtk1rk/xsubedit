import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from .progressBar import cProgressBar
from os.path import exists
from numpy import savez_compressed as savez, array as numarray
from cffmpeg import cffmpeg
import os

class cRawGenerationDialog(Gtk.Window):
    def __init__(self, parent, video_file, audio_file, audio_rate = 8000):
        super(cRawGenerationDialog, self).__init__()
        self.parent = parent
        self.set_title("Raw Audio Generation Progress")
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.videoFile = video_file.decode('utf-8')
        self.audioFile = audio_file.decode('utf-8')
        self.audioRate = audio_rate
        self.progressBar = cProgressBar()
        self.add(self.progressBar)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.ffmpeg = cffmpeg( 'ffmpeg -y -i "%s" -vn -ar %s -ac 1 -c:a pcm_u8 -f u8 "%s"' % (self.videoFile, str(self.audioRate), self.audioFile) )
        self.ffmpeg.connect('progress', self.ffmpeg_progress)

    def ffmpeg_progress(self, sender, value):
        self.set_progress(value / 2)

    def run(self):
        self.show()
        self.process_messages()
        self.ffmpeg.run()
        if not exists(self.audioFile):
            dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 'Could not generate raw audio file from video.')
            dlg.run()
            dlg.destroy()
        self.destroy()

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
