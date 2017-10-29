import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from progressBar import cProgressBar
from os.path import exists
from numpy import savez_compressed as savez, array as numarray
from cffmpeg import cffmpeg
from cffmpeginfo import cffmpeginfo
from utils import iround, mediaDur
import os
from math import ceil, floor
from subutils import ms2ts

class cWaveformGenerationDialog(Gtk.Window):
    def __init__(self, parent, video_file, audio_file):
        super(cWaveformGenerationDialog, self).__init__()
        self.parent = parent
        self.set_title("Waveform Generation Progress")
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.videoFile = video_file.decode('utf-8')
        self.audioFile = audio_file.decode('utf-8')
        self.progressBar = cProgressBar()
        self.add(self.progressBar)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.ffmpeg = cffmpeg('ffmpeg -y -i "%s" -vn -ac 1 -c:a pcm_u8 -f u8 "%s.raw"' % (self.videoFile, self.audioFile))
        self.ffmpeg.connect('progress', self.ffmpeg_progress)

    def ffmpeg_progress(self, sender, value):
        self.set_progress(float(value) / 2)

    def process_wav(self):
        os.rename(self.audioFile + '.raw', self.audioFile)
        audioSize = os.stat(self.audioFile).st_size
        audioDuration = iround( (1000.0 * audioSize) / self.audioRate )
        audioDuration = ceil(audioDuration / 10.0) * 10 # VSS SYNC
        if audioSize <= 0:
            return
        samplesPerDataPoint = self.audioRate / 100.0
        dataPoints = ceil(audioSize / samplesPerDataPoint)
        samplesPerDataPoint = int(samplesPerDataPoint)

        with open(self.audioFile, 'rb') as f:

            hiAudio = []
            lowAudio = []
            dp_div = iround(dataPoints / 10.0)

            for point in xrange(iround(dataPoints)):
                tmpData = bytearray(f.read(samplesPerDataPoint))
                if len(tmpData) == 0:
                    break

                hiAudio.append(abs(max(tmpData) - 128))
                lowAudio.append(-abs(min(tmpData) - 128))

                if point % dp_div == 0:
                    self.set_progress(0.5 + (point / dataPoints) / 2 )
                    self.process_messages()

        maxv = max(hiAudio)
        minv = min(lowAudio)
        hiAudio = numarray(hiAudio) / float(maxv)
        lowAudio = numarray(lowAudio) / float(minv)

        self.set_progress(1)
        self.process_messages()

        with open(self.audioFile, 'wb') as f:
            savez(f, hiAudio, lowAudio, numarray([audioDuration]))

    def error(self, err):
        dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, err)
        dlg.run()
        dlg.destroy()

    def run(self):
        self.show()
        self.process_messages()

        ffmpeginfo = cffmpeginfo('ffmpeg -i "%s"' % self.videoFile, ['Stream', 'Audio', 'Hz'])
        ffmpeginfo.run()
        res = ffmpeginfo.result
        if len(res) == 0:
            self.error('Could not get audio rate.')

        res = res[0]
        res = res[:res.find('Hz')]
        res = res[res.rfind(',')+1:]
        self.audioRate = int(res.strip())

        self.ffmpeg.run()
        if exists(self.audioFile + '.raw'):
            self.process_wav()
        else:
            self.error('Could not generate audio file from video.')
        self.destroy()

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
