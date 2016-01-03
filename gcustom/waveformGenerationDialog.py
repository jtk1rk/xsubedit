import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from progressBar import cProgressBar
from os.path import exists
from numpy import savez_compressed as savez, array as numarray
from cffmpeg import cffmpeg
from gcustom.messageDialog import cMessageDialog
import os

class cWaveformGenerationDialog(Gtk.Window):
    def __init__(self, parent, video_file, audio_file, video_duration, audio_rate):
        super(cWaveformGenerationDialog, self).__init__()
        self.parent = parent
        self.set_title("Waveform Generation Progress")
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.videoFile = video_file.decode('utf-8')
        self.audioFile = audio_file.decode('utf-8')
        self.videoDuration = video_duration
        self.audioRate = audio_rate
        self.progressBar = cProgressBar()
        self.add(self.progressBar)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.ffmpeg = cffmpeg('ffmpeg -y -i "' + self.videoFile + '" -vn -ar ' + str(self.audioRate) + ' -ac 1 -c:a pcm_u8 "' + self.audioFile + '.wav"')
        self.ffmpeg.connect('progress', self.ffmpeg_progress)

    def ffmpeg_progress(self, sender, value):
        self.set_progress(float(value) / 2)

    def process_wav(self):
        os.rename(self.audioFile + '.wav', self.audioFile)
        audioSize = os.stat(self.audioFile).st_size - 44
        if audioSize <= 0:
            return
        dataPoints = self.videoDuration / 1000000.0 / 10.0
        samplesPerDataPoint = audioSize / dataPoints

        with open(self.audioFile, 'rb') as f:
            #f.read( 44 + int(self.audioRate * (15 / 1000.0)) )
            f.read( 44 + int(self.audioRate * (7.5 / 1000.0)) )
            tmpData = f.read(int(round(samplesPerDataPoint / 2.0)))
            tmpData = map(lambda i: ord(i) - 128, tmpData)
            hiAudio = []
            lowAudio = []
            dp_div = int(round(dataPoints / 10))
            samplesPerDataPoint = int(round(samplesPerDataPoint))

            for point in xrange(int(round(dataPoints))):
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
            savez(f, hiAudio, lowAudio)

    def run(self):
        self.show()
        self.process_messages()
        self.ffmpeg.run()
        if exists(self.audioFile + '.wav'):
            self.process_wav()
        else:
            messageDialog = cMessageDialog(self, Gtk.MessageType.ERROR, 'Could not generate audio file from video.')
            messageDialog.run()
            messageDialog.destroy()
        self.destroy()

    def set_progress(self, value):
        self.progressBar.set_fraction(value)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
