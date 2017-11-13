import gi
gi.require_version('Gst', '1.0')
gi.require_version('GObject', '2.0')
gi.require_version('GdkX11', '3.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GdkX11, GstVideo, GObject
import platform

class Video(GObject.GObject):
    __gsignals__ = { 'position-update': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,)),  # float
                     'videoDuration-Ready' : (GObject.SIGNAL_RUN_LAST, GObject.TYPE_PYOBJECT, (GObject.TYPE_PYOBJECT,)) # long
                     }

    def __init__(self):
        super(Video, self).__init__()
        Gst.init(None)

        self.videoFilename = None
        self.videoDuration = 0
        self.videoPosition = 0
        self.ready = False
        self.play_update_handle = None
        self.__last_segment = None
        gstbin = Gst.Bin.new('my-gstbin')
        self.textoverlay = Gst.ElementFactory.make('textoverlay')
        gstbin.add(self.textoverlay)
        pad = self.textoverlay.get_static_pad('video_sink')
        ghostpad = Gst.GhostPad.new('sink', pad)
        gstbin.add_pad(ghostpad)
        if platform.system() == 'Windows':
            self.sink = Gst.ElementFactory.make('d3dvideosink')
        else:
            self.sink = Gst.ElementFactory.make('xvimagesink')
        gstbin.add(self.sink)
        self.textoverlay.link(self.sink)
        self.playbin = Gst.ElementFactory.make('playbin')
        self.playbin.set_property('video-sink', gstbin)
        self.sink.set_property('force-aspect-ratio', True)
        self.playbus = self.playbin.get_bus()
        self.textoverlay.set_property("font-desc", 'Verdana 24')
        self.playbus.add_signal_watch()
        self.playbus.connect('message', self.on_message)

    def set_duration(self, value):
        if self.videoDuration == 0:
            self.videoDuration = value * 10**3

    def set_sub_font(self, font):
        if font == '':
            return
        self.textoverlay.set_property('font-desc', font)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pause()
            self.position_update()
        elif t == Gst.MessageType.WARNING:
            err,  debug = message.parse_warning()
            print('Error %s ' % err, debug)
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print('Error %s ' % err, debug)

    def set_segment(self, segment):
        if segment != self.__last_segment:
            self.playbin.seek(1.0, Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, Gst.SeekType.SET, segment[0] * 10**6, Gst.SeekType.SET, segment[1] * 10**6)
            self.__last_segment = segment

    def set_video_widget(self, widget):
        self.sink.set_window_handle(widget._xid)

    def set_video_filename(self, filename):
        self.videoFilename = filename;
        self.playbin.set_property('current-text', -1)
        self.playbin.set_property('uri', 'file:///' + filename)
        self.playbin.set_state(Gst.State.PAUSED)
        if self.playbin.get_state(0)[0] == Gst.StateChangeReturn.FAILURE:
            return
        self.ready = True
        self.playing = False

    def set_audio_resolution(self, resolution):
        self.audio_resolution = resolution

    def pause(self):
        if self.is_playing():
            self.playbin.set_state(Gst.State.PAUSED)
        if self.play_update_handle:
            GObject.source_remove(self.play_update_handle)
            self.play_update_handle = None

    def calc_duration(self):
        try:
            self.videoDuration = self.playbin.query_duration(Gst.Format.TIME)[1]
            if self.videoDuration != 0:
                self.emit("videoDuration-Ready", self.videoDuration)
        except:
            print("Error querying video duration")

    def play(self):
        if self.videoDuration == 0:
            self.calc_duration()
        self.playbin.set_state(Gst.State.PLAYING)
        if self.play_update_handle:
            GObject.source_remove(self.play_update_handle)
            self.play_update_handle = None
        self.play_update_handle = GObject.timeout_add(45, self.position_update)

    def is_playing(self):
        return self.playbin.get_state(0)[1] == Gst.State.PLAYING

    def is_ready(self):
        return self.ready

    def position_update(self):
        if self.playbin.get_state(0)[0] == Gst.StateChangeReturn.ASYNC:
            return True
        if not self.is_playing() or self.videoDuration == 0:
            self.play_update_handle = None
            return False
        nsec = self.playbin.query_position(Gst.Format.TIME)[1]
        self.videoPosition = nsec / self.videoDuration
        self.emit("position-update", self.videoPosition)
        return True

    def set_subtitle(self, text):
        self.textoverlay.set_property("text", text)

    def set_videoPosition(self, pos):
        if self.videoDuration == 0:
            self.calc_duration()
        self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, pos * 10**3)
        self.__last_segment = None
        self.position_update()

    def get_videoDuration(self):
        return self.videoDuration

    def get_videoPosition(self):
        return self.videoPosition
