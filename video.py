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

    videoFilename = None
    videoDuration = 0
    videoPosition = 0
    ready = False
    play_update_handle = None

    def __init__(self):
        super(Video, self).__init__()
        Gst.init(None)
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
        #self.textoverlay.set_property("font-desc", 'Arial 25')
        self.playbus.add_signal_watch()
        self.playbus.connect('message', self.on_message)
        #self.playbus.enable_sync_message_emission()
        #self.playbus.connect("sync-message::element", self.on_sync_message)

    #def on_sync_message(self, bus, message):
    #    print "sync_message"

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.pause()
            self.position_update()
        elif t == Gst.MessageType.WARNING:
            err,  debug = message.parse_warning()
            print 'Error %s ' % err, debug

    def set_segment(self, segment):
        if segment != self.__last_segment:
            self.playbin.seek(1.0, Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, Gst.SeekType.SET, segment[0] * 1000000, Gst.SeekType.SET, segment[1] * 1000000)
            self.__last_segment = segment

    def set_video_widget(self, widget):
        self.sink.set_window_handle(widget._xid)

    def set_video_filename(self, filename):
        self.videoFilename = filename;
        self.playbin.set_property('uri', 'file:///'+filename)
        self.playbin.set_state(Gst.State.PAUSED)
        if self.playbin.get_state(0)[0] == Gst.StateChangeReturn.FAILURE:
            return
        self.ready = True
        self.playing = False
        self.playbin.set_state(Gst.State.PLAYING)
        self.playbin.get_state(Gst.CLOCK_TIME_NONE)
        self.calc_duration()
        self.playbin.set_state(Gst.State.PAUSED)

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
            self.emit("videoDuration-Ready", self.videoDuration)
        except:
            pass

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
        self.videoPosition = nsec / float(self.videoDuration)
        self.emit("position-update", self.videoPosition)
        return True

    def set_subtitle(self, text):
        self.textoverlay.set_property("text", text)

    def set_videoPosition(self, pos):
        if self.videoDuration == 0:
            self.calc_duration()
#        self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT, self.videoDuration * pos)
        self.playbin.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, self.videoDuration * pos)
        self.videoPosition = pos
        self.__last_segment = None
        self.emit("position-update", self.videoPosition)

    def get_videoDuration(self):
        return self.videoDuration

    def get_videoPosition(self):
        return self.videoPosition
