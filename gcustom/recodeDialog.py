import gi
gi.require_version('Gtk', '3.0')
from os.path import exists
from gi.repository import Gtk
from progressBar import cProgressBar
from gcustom.messageDialog import cMessageDialog
from time import sleep

class cRecodeDialog(Gtk.Window):
    def __init__(self, parent, filename, new_filename):
        super(cRecodeDialog, self).__init__()
        self.parent = parent
        self.set_title("Generating a fixed b-frame video")
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
#        self.ffmpeg = cffmpeg('ffmpeg -y -fflags +genpts -i "' + self.filename + '" -c:a aac -strict -2 -c:v copy "' + self.new_filename + '"')
        self.exec_cmd = 'ffmpeg -y -fflags +genpts -i "%s" -c:a aac -strict -2 -c:v copy "%s"' % (self.filename, self.new_filename)
        self.result = False

    def ffmpeg_run(self):
        pipe = subprocess.Popen(self.exec_cmd.encode(locale.getpreferredencoding()), shell = True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)
        line = ""
        while not (line == "" and pipe.poll() != None) :
            line = pipe.stdout.readline().strip()
            self.parse_progress(line)
            self.parse_codec(line)

    def parse_codec(self, line):
        if 'Video:' in line:
            self.codec = line.split()[int(line.split().index('Video:'))+1]
            if self.codec == 'mpeg4':
                self.codec = 'XVID' if 'XVID' in line else self.codec

    def parse_progress(self, line):
        if self.duration == None:
            match = self.re_duration.search(line)
            if match:
                self.duration = subutils.ts2ms(match.group(0)[10:21])
        else:
            match = self.re_position.search(line)
            if match:
                self.set_progress(subutils.ts2ms(match.group(0)[5:]) / float(self.duration))
                self.process_messages()

    def ffmpeg_progress(self, sender, value):
        self.set_progress(float(value) / 2)

    def run(self):
        self.show()
        self.process_messages()
        self.ffmpeg_run()
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
        sleep(0.01)
        while Gtk.events_pending():
            sleep(0.001)
            Gtk.main_iteration_do(False)
