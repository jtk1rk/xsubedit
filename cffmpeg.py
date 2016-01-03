import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
import subprocess, locale
import subutils
import re

class cffmpeg(GObject.GObject):
    __gsignals__ = {'codec': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
                    'progress': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
                    'finish': (GObject.SIGNAL_RUN_LAST, None, ())}

    def __init__(self, cmd):
        super(cffmpeg, self).__init__()
        self.exec_cmd = cmd
        self.re_position = re.compile('time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})\d*', re.U | re.I)
        self.re_duration = re.compile('Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})[^\d]*', re.U)
        self.duration = None
        self.codec = None

    def run(self):
        pipe = subprocess.Popen(self.exec_cmd.encode(locale.getpreferredencoding()), shell = True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)

        line = ""

        while not (line == "" and pipe.poll() != None) :
            line = pipe.stdout.readline().strip()
            self.parse_progress(line)
            self.parse_codec(line)
            self.process_messages()
        self.emit('finish')

    def parse_codec(self, line):
        if 'Video:' in line:
            self.codec = line.split()[int(line.split().index('Video:'))+1]
            if self.codec == 'mpeg4':
                self.codec = 'XVID' if 'XVID' in line else self.codec
            self.emit('codec', self.codec)

    def parse_progress(self, line):
        if self.duration == None:
            match = self.re_duration.search(line)
            if match:
                self.duration = subutils.ts2ms(match.group(0)[10:21])
        else:
            match = self.re_position.search(line)
            if match:
                self.progress = subutils.ts2ms(match.group(0)[5:]) / float(self.duration)
                self.emit('progress', self.progress if self.progress <= 1 else 1)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
