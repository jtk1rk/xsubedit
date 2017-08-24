#ffmpeg -i input.flv  -filter:v "select='gt(scene,0.4)',showinfo"  -f null  - 2> ffout
#grep showinfo ffout | grep pts_time:[0-9.]* -o | grep [0-9.]* -o > timestamps
#>>> print re.search('pts_time:(\d*)(.\d*)',s1,0).group().replace('pts_time:','')
#for fastest detecting, first encode: ffmpeg -y -i 1.mkv -c:a copy -vf "scale=100:-2" -sws_flags fast_bilinear -sws_dither none -c:v libx264 -preset:v ultrafast  out.mkv
import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject
from os.path import exists
import subprocess, locale
import threading
import re
import subutils

class cSceneDetect(GObject.GObject, threading.Thread):
    __gsignals__ = {'detect': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
                    'progress': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT,)),
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
        self.re_scenepos = re.compile('pts_time:(\d*)(.\d*)', 0)
        self.re_position = re.compile('time=(\d{2}):(\d{2}):(\d{2})\.(\d{2})\d*', re.U | re.I)
        self.re_duration = re.compile('Duration: (\d{2}):(\d{2}):(\d{2}).(\d{2})[^\d]*', re.U)
        self.duration = None


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
            self.parse_scenepos(line)
            self.parse_progress(line)
            if self._stop:
                pipe.kill()
                return

        # Finally
        GObject.idle_add(self.signal_finish)

    def signal_progress(self, percent):
        self.emit('progress', percent)

    def signal_finish(self):
        self.emit('finish')

    def signal_detect(self, pos):
        self.emit('detect', float(pos))

    def parse_progress(self, line):
        if self.duration == None:
            match = self.re_duration.search(line)
            if match:
                self.duration = subutils.ts2ms(match.group(0)[10:21])
        else:
            match = self.re_position.search(line)
            if match:
                progress = subutils.ts2ms(match.group(0)[5:]) / float(self.duration)
                GObject.idle_add(self.signal_progress, float(progress if progress <= 1 else 1))

    def parse_scenepos(self, line):
        match = self.re_scenepos.search(line)
        if match:
            pos = float(match.group().replace('pts_time:','')) * 1000.0
            GObject.idle_add(self.signal_detect, pos)
