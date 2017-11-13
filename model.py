import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from video import Video
from audio import Audio
from subtitles import Subtitles
from voreference import cVOReference
from numpy import load
import sys

class Model(GObject.GObject):
    __gsignals__ = { 'audio-ready': (GObject.SIGNAL_RUN_LAST, None, ()) }

    def __init__(self):
        super(Model, self).__init__()
        Gst.init(None)
        self.video = Video()
        self.audio = None
        self.subtitles = Subtitles()
        self.voReference = cVOReference()
        self.scenes = []
        self.ready = False
        # File Names
        self.voFilename = ""
        self.subFilename = ""
        self.peakFilename = ""
        self.projectFilename = ""
        self.audioDuration = 0

    def setup_audio(self, buffers):
        self.audio = Audio(*buffers)
        self.ready = True
        self.emit("audio-ready")

    def get_waveform(self):
        if self.peakFilename == "":
            return
        f = open(self.peakFilename, 'rb')
        dataFile = load(f)
        hiAudio = dataFile['arr_0']
        lowAudio = dataFile['arr_1']
        self.audioDuration = int(dataFile['arr_2'][0] * 1000)
        f.close()
        self.audio = Audio(hiAudio, lowAudio)
        self.ready = True
        self.emit("audio-ready")
