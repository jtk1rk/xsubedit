import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from progressBar import cProgressBar
from os.path import exists
from numpy import savez_compressed as savez, array as numarray
from cffmpeg import cffmpeg
from utils import iround
import os

class cWaveformGenerationDialog(Gtk.Window):
    def __init__(self, parent, video_file, audio_file, audio_rate):
        super(cWaveformGenerationDialog, self).__init__()
        self.parent = parent
        self.set_title("Waveform Generation Progress")
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
        self.audioDuration = 0
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.ffmpeg = cffmpeg('ffmpeg -y -i "%s" -vn -ar "%s" -ac 1 -c:a pcm_u8 -f u8 "%s.raw"' % (self.videoFile, str(self.audioRate), self.audioFile))
        self.ffmpeg.connect('progress', self.ffmpeg_progress)

    def ffmpeg_progress(self, sender, value):
        self.set_progress(float(value) / 2)

    def process_wav(self):
        os.rename(self.audioFile + '.raw', self.audioFile)
        audioSize = os.stat(self.audioFile).st_size
        self.audioDuration = audioSize / 8.0
        if audioSize <= 0:
            return
        dataPoints = self.audioDuration / 10
        samplesPerDataPoint = audioSize / dataPoints

        with open(self.audioFile, 'rb') as f:
            tmpData = f.read(iround(samplesPerDataPoint / 2.0))
            tmpData = map(lambda i: ord(i) - 128, tmpData)
            hiAudio = []
            lowAudio = []
            dp_div = iround(dataPoints / 10.0)
            samplesPerDataPoint = iround(samplesPerDataPoint)

            for point in xrange(iround(dataPoints)):
                if len(tmpData) == 0:
                    hiAudio.append(0)
                    lowAudio.append(0)
                else:
                    hiAudio.append(abs(max(tmpData)-128))
                    lowAudio.append(-abs(min(tmpData)-128))
                tmpData = bytearray(f.read(samplesPerDataPoint))
                if point % dp_div == 0:
                    self.set_progress(0.5 + (point / dataPoints) / 2 )
                    self.process_messages()

        maxv = float(max(hiAudio))
        minv = float(min(lowAudio))
        hiAudio = numarray(hiAudio) / maxv
        lowAudio = numarray(lowAudio) / minv

        self.set_progress(1)
        self.process_messages()

        with open(self.audioFile, 'wb') as f:
            savez(f, hiAudio, lowAudio, numarray([self.audioDuration]))

    def run(self):
        self.show()
        self.process_messages()
        self.ffmpeg.run()
        if exists(self.audioFile + '.raw'):
            self.process_wav()
        else:
            dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 'Could not generate audio file from video.')
            dlg.run()
            dlg.destroy()
        self.destroy()

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
