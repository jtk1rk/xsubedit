#ffmpeg -i input.flv  -filter:v "select='gt(scene,0.4)',showinfo"  -f null  - 2> ffout
#grep showinfo ffout | grep pts_time:[0-9.]* -o | grep [0-9.]* -o > timestamps
#>>> print re.search('pts_time:(\d*)(.\d*)',s1,0).group().replace('pts_time:','')
import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from os.path import exists
import subprocess, locale
import threading
import re

class cSceneDetect(GObject.GObject, threading.Thread):
    __gsignals__ = {'detect': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
                    'finish': (GObject.SIGNAL_RUN_LAST, None, ())}

    def __init__(self, vidFile):
        GObject.GObject.__init__(self)
        threading.Thread.__init__(self)

        self.file_not_found = False
        self._stop = False
        if not exists(vidFile.decode('utf-8')):
            self.file_not_found = True
            return

        self.exec_cmd = 'ffmpeg -i "%s"  -filter:v "select=\'gt(scene,0.4)\',showinfo"  -f null  -' % vidFile.decode('utf-8')
        self.re_pos = re.compile('pts_time:(\d*)(.\d*)', 0)

    def stop(self):
        self._stop = True

    def run(self):
        if self.file_not_found:
            return

        # Running FFMPEG
        pipe = subprocess.Popen(self.exec_cmd.encode(locale.getpreferredencoding()), shell = True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)
        line = ""

        # Processing FFMPEG output
        while not (line == "" and pipe.poll() != None) :
            line = pipe.stdout.readline().strip()
            self.parse_pos(line)
            if self._stop:
                pipe.kill()
                return

        # Finally
        GObject.idle_add(self.signal_finish)

    def signal_finish(self):
        self.emit('finish')

    def signal_detect(self, pos):
        self.emit('detect', float(pos))

    def parse_pos(self, line):
        match = self.re_pos.search(line)
        if match:
            pos = float(match.group().replace('pts_time:','')) * 1000.0
            GObject.idle_add(self.signal_detect, pos)
