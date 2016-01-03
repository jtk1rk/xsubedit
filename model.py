import gi
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject
from video import Video
from audio import Audio
from subtitles import Subtitles
from voreference import cVOReference
from numpy import load

class Model(GObject.GObject):
    __gsignals__ = { 'audio-ready': (GObject.SIGNAL_RUN_LAST, None, ()) }

    video = None
    audio = None
    subtitles = Subtitles()
    voReference = cVOReference()
    ready = False
    voFilename = ""
    subFilename = ""
    peakFilename = ""
    projectFilename = ""

    def __init__(self):
        super(Model, self).__init__()
        Gst.init(None)
        self.video = Video()
        self.audio = None
        self.subtitles = Subtitles()
        self.voReference = cVOReference()
        self.ready = False
        # File Names
        self.voFilename = ""
        self.subFilename = ""
        self.peakFilename = ""
        self.projectFilename = ""

    def setup_audio(self, buffers):
        self.audio = Audio(*buffers)
        self.ready = True
        self.emit("audio-ready")

    def get_waveform(self):
        if self.peakFilename == "":
            return
        f = open(self.peakFilename.decode('utf-8'), 'rb')
        dataFile = load(f)
        hiAudio = dataFile['arr_0']
        lowAudio = dataFile['arr_1']
        f.close()
        self.audio = Audio(hiAudio, lowAudio)
        self.video.calc_duration()
        self.ready = True
        self.emit("audio-ready")
