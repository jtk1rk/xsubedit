# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from subtitles import subRec, timeStamp
from bisect import bisect
from time import time
import cairo


class cSyncAudioWidget(Gtk.EventBox):
    __gsignals__ = {       'viewpos-update': (GObject.SIGNAL_RUN_LAST, None, (int,)),
                              'sub-updated': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              'right-click': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              'dragged-sub': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
                              'vertical-scale-update': (GObject.SIGNAL_RUN_LAST, None, (float,)),
                              'active-sub-changed' : (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              }

    def __init__(self):
        # Inits
        super(cSyncAudioWidget, self).__init__()
        self.drawingArea = Gtk.DrawingArea()
        self.add(self.drawingArea)
        self.set_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.cursorLeftMargin = Gdk.Cursor(Gdk.CursorType.LEFT_SIDE)
        self.cursorRightMargin = Gdk.Cursor(Gdk.CursorType.RIGHT_SIDE)

        # Class constants and internal variables
        self.BUTTON_LEFT = 1
        self.BUTTON_RIGHT = 2
        self.SINGLE_CLICK = 1
        self.DOUBLE_CLICK = 2
        self.dragging = False
        self.dragging_sub = None
        self.mouse_button = None
        self.mouse_click_coords = None
        self.mouse_click_type = None
        self.mouse_event = None
        self.mouse_last_event = None
        self.mouse_last_click_coords = None
        self.ms_to_coord_factor = 0
        self.low_ms_coord = 0
        self.mode = None

        # Creating internal properties
        self.__viewportLower = None
        self.__viewportUpper = None
        self.__overSub = None
        self.__width = None
        self.__pos = None
        self.__cursor = None
        self.__videoDuration = None
        self.__highms = None
        self.__lowms = None
        self.__subs = None
        self.__audioData = None
        self.__audioModel = None
        self.__activeSub = None
        self.__scale_linear_audio = 1

        # Init Class Variables
        self.scale_linear_audio = 1
        self.waveformBuffer = None
        self.canvasBuffer = None
        self.carret_position = 0
        self.subList = set()
        self.activeSub = None
        self.overSub = None
        self.isReady = False
        self.audioModel = None
        self.viewportLower = 0
        self.viewportUpper = 0.05
        self.isWaveformBufferValid = False
        self.isCanvasBufferValid = False
        self.isParametersValid = False
        self.videoDuration = 0
        self.grayms = 120.0
        self.pos = 0
        self.cursor = 0
        self.lowms = 0
        self.highms = 0
        self.mspp = 0
        self.grayarea = 0
        self.subtitlesModel = None
        self.audioData = None
        self.videoSegment = None
        self.stickZoom = False
        self.scenes = []

        # Connections
        self.drawingArea.connect('draw', self.on_draw)
        self.drawingArea.connect('size-allocate', self.on_size_allocate)
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('scroll-event', self.on_scroll)
        self.connect('motion-notify-event', self.on_motion_notify)

    def set_scenes(self, ref):
        self.scenes = ref

    def on_button_press(self, widget, event):
        if self.videoDuration == 0:
            return
        self.mouse_click_coords = (event.x, event.y)
        self.mouse_last_click_coords = self.mouse_click_coords
        self.mouse_last_event = event
        if event.button == 1:
            self.mouse_button = self.BUTTON_LEFT
            if event.type == Gdk.EventType._2BUTTON_PRESS:
                self.mouse_click_type = self.DOUBLE_CLICK
            else:
                self.mouse_click_type = self.SINGLE_CLICK
        elif event.button == 3:
            self.mouse_button = self.BUTTON_RIGHT
            self.mouse_event = event

    def check_click(self):
        if self.mouse_click_type == self.DOUBLE_CLICK and self.overSub != None:
            self.activeSub = self.overSub
            self.isCanvasBufferValid = False
            self.queue_draw()

        if self.mouse_button == self.BUTTON_LEFT:
            self.activeSub = None
            self.cursor = self.get_mouse_msec(self.mouse_click_coords[0])
            self.isCanvasBufferValid = False
            self.queue_draw()

        if self.mouse_click_type == self.DOUBLE_CLICK and self.overSub != None:
            self.overSub = None
            for sub in self.subList:
                if sub.startTime - self.mspp * 2 <= self.get_mouse_msec(self.mouse_click_coords[0]) <= sub.stopTime + self.mspp * 2:
                    self.overSub = sub
                    break
            self.activeSub = self.overSub
            self.isCanvasBufferValid = False
            self.queue_draw()

        if self.mouse_button == self.BUTTON_RIGHT:
            self.emit('right-click', self.mouse_event)

    def on_button_release(self, widget, event):
        if not self.dragging:
            self.check_click()
        else:
            if self.dragging_sub != None:
                self.emit('dragged-sub', self.dragging_sub, self.overSub)
        self.mouse_button = None
        self.mouse_click_coords =(None, None)
        self.mouse_click_type = None
        self.mouse_event = None
        self.dragging = False
        self.dragging_sub = None
        if self.mode == 'SCM-Move-One' or self.mode == 'SCM-Move-All' or self.mode == 'SCM-Move-All-After':
            self.mode = None
        subs = self.subtitlesModel.get_sub_list()
        for sub in subs:
            sub.stopTime_orig = int(sub.stopTime)
            sub.startTime_orig = int(sub.startTime)

    def on_dragging(self, origmsec, msec):
        if self.overSub == None:
            return

        if self.mode == 'SCM-Move-One':
            self.overSub.startTime = int(self.overSub.startTime_orig) + (msec - origmsec)
            self.overSub.stopTime = int(self.overSub.stopTime_orig) + (msec - origmsec)
        elif self.mode == 'SCM-Move-All':
            for sub in self.subtitlesModel.get_sub_list():
                sub.startTime = int(sub.startTime_orig) + (msec - origmsec)
                sub.stopTime = int(sub.stopTime_orig) + (msec - origmsec)
        elif self.mode == 'SCM-Move-All-After':
            subs = self.subtitlesModel.get_sub_list()
            for sub in subs[subs.index(self.overSub):]:
                sub.startTime = int(sub.startTime_orig) + (msec - origmsec)
                sub.stopTime = int(sub.stopTime_orig) + (msec - origmsec)
        elif self.mode == 'SCM-Strech-Selected':
            subs = self.subtitlesModel.get_sub_list()
            self.overSub.startTime = int(self.overSub.startTime_orig) + (msec - origmsec)
            self.overSub.stopTime = int(self.overSub.stopTime_orig) + (msec - origmsec)
            factor = (int(self.overSub.startTime) - int(subs[0].startTime)) / float( int(self.overSub.startTime_orig) - int(subs[0].startTime) )
            for sub in subs[:subs.index(self.overSub)]: # calculate strech here
                sub.startTime = int( (int(sub.startTime_orig) - int(subs[0].startTime)) * factor + int(subs[0].startTime) )
                sub.stopTime = int( (int(sub.stopTime_orig) - int(subs[0].startTime)) * factor + int(subs[0].startTime) )

        if not (self.mode is None):
            self.isCanvasBufferValid = False
            self.queue_draw()
            self.emit('sub-updated', self.overSub)

    def on_motion_notify(self, widget, event):
        if self.videoDuration == 0:
            return

        mouse_msec = self.get_mouse_msec(event.x)
        if self.mouse_button == self.BUTTON_LEFT and mouse_msec != self.mouse_click_coords[0] and not self.dragging:
            self.dragging = True

        if self.dragging:
            target_msec = mouse_msec
            target_msec = target_msec if target_msec < self.highms else self.highms
            target_msec = target_msec if target_msec > self.lowms else self.lowms
            self.on_dragging(self.get_mouse_msec(self.mouse_click_coords[0]), target_msec)
        else:
            self.overSub = None
            # bisect here if needed
            # Check if we are over a sub
            for sub in self.subList:
                if sub.startTime - self.mspp * 2 <= mouse_msec <= sub.stopTime + self.mspp * 2:
                    self.overSub = sub
                    break

    def zoom(self, direction, xcoord):
        if self.stickZoom:
            return
        if self.videoDuration == 0:
            return

        na = self.viewportLower * 100
        nb = self.viewportUpper * 100

        center = xcoord / float(self.width)
        a = self.viewportLower * 100
        b = self.viewportUpper * 100
        c = a + (b-a) * center
        factor = 0.1

        if direction == Gdk.ScrollDirection.UP:
            na = c - (1 - factor) * ( c - a )
            nb = c + (1 - factor) * ( b - c)
            if abs(na-nb) < 0.002:
                return

        if direction == Gdk.ScrollDirection.DOWN:
            na = c - (1 + factor) * (c - a)
            nb = c + (1 + factor) * (b - c)
            if abs(na-nb) > 50:
                return
            na = 0 if na < 0 else na
            nb = 100 if nb > 100 else nb

        self.viewportLower = min(na, nb) / 100
        self.viewportUpper = max(na, nb) / 100
        self.queue_draw()

    def on_scroll(self, widget, event):
        if self.videoDuration == 0:
            return

        if event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.direction == Gdk.ScrollDirection.UP:
                self.scale_linear_audio += 0.2
            elif event.direction == Gdk.ScrollDirection.DOWN:
                self.scale_linear_audio -= 0.2
            return

        if event.state & Gdk.ModifierType.SHIFT_MASK:
            self.zoom(event.direction, event.x)
            return

        moveval = 25 * self.mspp
        if event.direction == Gdk.ScrollDirection.DOWN and self.highms < self.videoDuration + moveval:
            self.viewportLower = (self.lowms + moveval) / float(self.videoDuration)
            self.viewportUpper = (self.highms + moveval) / float(self.videoDuration)
        elif event.direction == Gdk.ScrollDirection.UP and self.lowms > moveval:
            self.viewportLower = (self.lowms - moveval) / float(self.videoDuration)
            self.viewportUpper = (self.highms - moveval) / float(self.videoDuration)

        self.queue_draw()

    def invalidateCanvas(self):
        self.isCanvasBufferValid = False
        self.isParametersValid = False

    @property
    def overSub(self):
        return self.__overSub

    @overSub.setter
    def overSub(self, val):
        self.__overSub = val

    @property
    def scale_linear_audio(self):
        return self.__scale_linear_audio

    @scale_linear_audio.setter
    def scale_linear_audio(self, value):
        if value == self.__scale_linear_audio:
            return
        else:
            self.__scale_linear_audio = value if value > 0 else 0
            self.audioModel.set_scale('linear', self.__scale_linear_audio)
            self.isWaveformBufferValid = False
            self.queue_draw()
            self.emit('vertical-scale-update', self.__scale_linear_audio)

    @property
    def width(self):
        return self.__width

    @width.setter
    def width(self, val):
        if self.__width != val:
            self.isParametersValid = False
            self.isWaveformBufferValid = False
            self.isCanvasBufferValid = False
            if self.audioModel != None:
                self.audioModel.set_width(val)
        self.__width = val

    @property
    def viewportLower(self):
        return self.__viewportLower

    @viewportLower.setter
    def viewportLower(self, val):
        if self.__viewportLower != val:
            self.isParametersValid = False
            self.isWaveformBufferValid = False
            self.isCanvasBufferValid = False
        self.__viewportLower = val

    @property
    def viewportUpper(self):
        return self.__viewportUpper

    @viewportUpper.setter
    def viewportUpper(self, val):
        if self.__viewportUpper != val:
            self.isParametersValid = False
            self.isWaveformBufferValid = False
            self.isCanvasBufferValid = False
        self.__viewportUpper = val

    @property
    def audioModel(self):
        return self.__audioModel

    @audioModel.setter
    def audioModel(self, val):
        if val != None:
            self.__audioModel = val
            self.__audioModel.set_width(self.get_allocation().width)
            self.audioData = self.__audioModel.get_data(self.viewportLower, self.viewportUpper)

    @property
    def audioData(self):
        return self.__audioData

    @audioData.setter
    def audioData(self, val):
        if val != None:
            self.isReady = self.videoDuration != 0
            self.isParametersValid = False
            self.isWaveformBufferValid = False
            self.isCanvasBufferValid = False
        self.__audioData = val

    @property
    def pos(self):
        return self.__pos

    @pos.setter
    def pos(self, val):
        if self.__pos != val:
            self.queue_draw()
        self.__pos = val

    @property
    def cursor(self):
        return self.__cursor

    @cursor.setter
    def cursor(self, val):
        if self.__cursor != val:
            self.videoSegment = (val, self.videoDuration)
            self.queue_draw()
        self.__cursor = val

    @property
    def videoDuration(self):
        return self.__videoDuration

    @videoDuration.setter
    def videoDuration(self, val):
        if val != 0:
            self.__videoDuration = val
            self.isParamtersValid = False
            self.isCanvasBufferValid = False
            self.isWaveformBufferValid = False
            self.isReady = self.audioData != None
            self.videoSegment = (0, val)
        else:
            self.__videoDuration = val

    @property
    def activeSub(self):
        return self.__activeSub

    @activeSub.setter
    def activeSub(self, val):
        if val != None:
            self.videoSegment = (int(val.startTime), int(val.stopTime))
        else:
            self.videoSegment = (self.cursor, self.videoDuration)
        if self.__activeSub != val:
            self.emit('active-sub-changed', val)
        self.__activeSub = val

    @property
    def subs(self):
        return self.__subs

    @subs.setter
    def subs(self, val):
        self.__subs = val

    @property
    def lowms(self):
        return self.__lowms

    @lowms.setter
    def lowms(self, val):
        self.__lowms = val

    @property
    def highms(self):
        return self.__highms

    @highms.setter
    def highms(self, val):
        self.__highms = val

    def get_mouse_msec(self, pos):
        return int(self.lowms + (pos / float(self.width)) * (self.highms - self.lowms))

    def get_viewport_pos_from_ms(ms):
        return (ms / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) * widget.get_allocation().width

    def calc_parameters(self):
        self.lowms = self.viewportLower * self.videoDuration
        self.highms = self.viewportUpper * self.videoDuration
        self.mspp = (self.highms - self.lowms) / float(self.width)
        self.grayarea = self.grayms / self.mspp
        if self.subtitlesModel != None:
            self.subList = set(self.subtitlesModel.list_subs_overlapping_window(self.lowms - 120, self.highms))
        self.ms_to_coord_factor = self.width / (float(self.viewportUpper - self.viewportLower) * self.videoDuration)
        self.low_ms_coord  = (self.viewportLower * self.width) / float(self.viewportUpper - self.viewportLower)

    def center_active_sub(self):
        low = int(self.activeSub.startTime)
        high = int(self.activeSub.stopTime)
        msdur = (high - low) / 2
        if self.stickZoom:
            vpwidthms = (self.viewportUpper - self.viewportLower) * float(self.videoDuration)
            centerms = (low + msdur)
            lms = (centerms - (vpwidthms / 2))
            ums = (centerms + (vpwidthms / 2))
            if lms < 0:
                ums += abs(lms)
                lms = 0
            elif ums > self.videoDuration:
                lms -= ums - self.videoDuration
                ums = self.videoDuration
            self.viewportLower = lms / float(self.videoDuration)
            self.viewportUpper = ums / float(self.videoDuration)
        else:
            if msdur < 1000:
                msdur = 1000
            low -= msdur
            high += msdur
            if low < 0:
                low = 0
            if high > self.videoDuration:
                high = self.videoDuration
            self.viewportLower = (low / float(self.videoDuration))
            self.viewportUpper = (high / float(self.videoDuration))

        self.isCanvasBufferValid = False
        self.cursor = low
        self.queue_draw()
        self.videoSegment = (int(self.activeSub.startTime), int(self.activeSub.stopTime))
        self.emit('viewpos-update', int(100 * low / float(self.videoDuration)))

    def center_multiple_active_subs(self, startTime, stopTime):
        self.videoSegment = (int(startTime), int(stopTime))
        subWidthPerc = (stopTime - startTime) / float(self.videoDuration)
        lowPerc = startTime / float(self.videoDuration) - subWidthPerc * 0.8
        highPerc = stopTime / float(self.videoDuration) + subWidthPerc * 0.8
        self.viewportLower = lowPerc if lowPerc >= 0 else 0
        self.viewportUpper = highPerc if highPerc <= 1 else 1
        self.queue_draw()
        self.emit('viewpos-update', int(lowPerc * 100))

    def draw_buffers(self, widget):
        if not self.isReady:
            return False

        height = widget.get_allocation().height
        height *= 0.98

        if self.isParametersValid == False:
            self.calc_parameters()
            self.isParametersValid = True

        # Draw Waveform Buffer (if invalidated)
        if not self.isWaveformBufferValid:
            self.audioData = self.audioModel.get_data(self.viewportLower, self.viewportUpper)
            self.isWaveformBufferValid = True
            cc = cairo.Context(self.waveformBuffer)
            cc.set_source_rgb(0,0,0)
            cc.paint()
            cc.set_source_rgba(0.0329, 0.122, 0.301, 0.9)
            cc.set_line_width(1)
            for i in xrange(len(self.audioData)):
                cc.move_to(i, height / 2.0 - self.audioData[i][0] * height / 2.0)
                cc.line_to(i, height / 2.0 + self.audioData[i][1] * height / 2.0)
            cc.stroke()

        # Draw Cavnas Buffer (if invalidated)
        if self.isCanvasBufferValid and self.isWaveformBufferValid:
            return True
        self.isCanvasBufferValid = True

        cc = cairo.Context(self.canvasBuffer)
        cc.set_source_rgb(0, 0, 0)
        cc.paint()

        # Draw Subtitles
        height = widget.get_allocation().height

        for sub in self.subList:
            paintlow = sub.startTime * self.ms_to_coord_factor - self.low_ms_coord if sub.startTime >= self.lowms else 0
            painthigh = sub.stopTime * self.ms_to_coord_factor - self.low_ms_coord if sub.stopTime <= self.highms else self.width
            if sub == self.activeSub:
                cc.set_source_rgba(0.9, 0.9, 0.9, 0.5)
            else:
                cc.set_source_rgba(0.9, 0.9, 0.9, 0.3)
            cc.rectangle(paintlow, 2, painthigh - paintlow, height - 4)
            cc.fill()
            if painthigh < self.width :
                cc.set_source_rgba(0.3, 0.3, 0.3, 0.7)
                cc.rectangle(painthigh, 2, self.grayarea if painthigh + self.grayarea + 1 <= self.width else self.width - painthigh - 1, height - 4)
                cc.fill()
            cc.set_source_rgba(0.9, 0.4, 0.3, 0.7)
            cc.set_dash([6, 6, 6, 4])
            if sub.startTime >= self.lowms and sub.startTime <= self.highms:
                cc.move_to(paintlow, 2)
                cc.line_to(paintlow, height - 2)
                cc.move_to(paintlow+1, 2)
                cc.line_to(paintlow+1, height - 2)
            if sub.stopTime >= self.lowms and sub.stopTime <= self.highms:
                cc.move_to(painthigh, 2)
                cc.line_to(painthigh, height - 2)
                cc.move_to(painthigh-1, 2)
                cc.line_to(painthigh-1, height - 2)
            cc.stroke()

            # Draw Subtitle Text
            fontSize = 10
            if self.viewportLower != self.viewportUpper:
                zoom = 1 / float(self.viewportUpper - self.viewportLower)
                fontSize = fontSize if not 10 <= zoom <= 15 else zoom + 1
                fontSize = 16 if zoom > 15 else fontSize
            cc.set_font_size(fontSize)
            cc.set_source_rgba(0.8, 0.8, 0, 1)
            tmpText = sub.text.splitlines()
            if tmpText != []:
                tmpSize = cc.text_extents(max(tmpText, key=len))
                if tmpSize[2] < painthigh - paintlow:
                    for i in xrange(len(tmpText)):
                        cc.move_to(paintlow+2, 20 + i * (tmpSize[3] + 5))
                        cc.show_text(tmpText[i])

        # Draw Scene Lines
        tmplines = self.scenes[ bisect(self.scenes, self.lowms) : bisect(self.scenes, self.highms) ]
        for line_ms in tmplines:
            viewportPos = line_ms * self.ms_to_coord_factor  - self.low_ms_coord
            cc.set_source_rgba(0.894, 0.553, 0.329, 0.7)
            cc.set_dash([1,2])
            cc.move_to(viewportPos, 0)
            cc.line_to(viewportPos, height)
        cc.stroke()

        return True

    def on_size_allocate(self, widget, allocation):
        self.waveformBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, allocation.width, allocation.height)
        self.canvasBuffer = cairo.ImageSurface(cairo.FORMAT_ARGB32, allocation.width, allocation.height)
        self.width = allocation.width
        if self.audioModel != None:
            self.audioModel.set_width(self.width)
        self.isWaveformBufferValid = False
        self.isCanvasBufferValid = False
        self.isParametersValid = False
        return True

    def on_draw(self, widget, cc):
        if not self.draw_buffers(widget):
            return
        cc.set_source_surface(self.canvasBuffer, 0, 0)
        cc.paint()
        cc.set_operator(cairo.OPERATOR_ADD)
        cc.set_source_surface(self.waveformBuffer, 0, 0)
        cc.paint()

        width = widget.get_allocation().width
        height = widget.get_allocation().height

        # Draw Position
        viewportPos = self.pos * self.ms_to_coord_factor - self.low_ms_coord
        if 0 <= viewportPos <= self.width:
            cc.set_source_rgba(0.8, 0.8, 0.1, 0.7)
            cc.move_to(viewportPos, 0)
            cc.line_to(viewportPos, height)
            cc.stroke()

        # Draw Cursor
        viewportPos = self.cursor * self.ms_to_coord_factor - self.low_ms_coord
        if 0 <= viewportPos <= self.width:
            cc.set_source_rgba(0.8, 0.8, 0.8, 1)
            cc.set_dash([1,3])
            cc.move_to(viewportPos, 0)
            cc.line_to(viewportPos, height)
            cc.stroke()

class cVisualSyncDialog(Gtk.Dialog):
    def __init__(self, parent, subsModel, audioModel, sceneModel, videoModel, videoDuration):
        super(cVisualSyncDialog, self).__init__()
        self.parent = parent
        self.set_title = 'Visual Sync'
        self.set_modal(True)
        self.response = None
        self.videoModel = videoModel
        self.videoDuration = videoDuration
        #self.set_transient_for(parent)
        #self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.set_size_request(1000, 320)
        self.set_resizable(True)
        self.textview = Gtk.TextView()
        self.textview.set_size_request(-1, 50)
        self.audioWidget = cSyncAudioWidget()
        self.audioWidget.subtitlesModel = subsModel
        self.audioWidget.videoDuration = videoDuration / 1000000.0
        self.audioWidget.audioModel = audioModel
        self.audioWidget.sceneModel = sceneModel
        self.audioWidget.set_size_request(1000,320)
        button_cancel = Gtk.Button('Cancel')
        button_ok = Gtk.Button('OK')
        vbox = Gtk.VBox()
        hbox = Gtk.HBox()
        vbox.pack_start(self.audioWidget, True, True, 3)
        vbox.pack_end(hbox, False, False, 1)
        hbox.pack_end(button_cancel, False, False, 1)
        hbox.pack_end(button_ok, False, False, 1)
        hbox.pack_start(self.textview, False, False, 1)
        self.vbox.pack_start(vbox, True, True, 1)
        self.SCM = {}
        self.SCM['SCM-Menu'] = Gtk.Menu()
        self.SCM['SCM-Move-One'] = Gtk.MenuItem('Move selected subtitle')
        self.SCM['SCM-Move-All'] = Gtk.MenuItem('Move all Subtitles')
        self.SCM['SCM-Move-All-After'] = Gtk.MenuItem('Move subtitle and all after selected')
        self.SCM['SCM-Strech-Selected'] = Gtk.MenuItem('Stretch subtitles to follow selected')
        self.SCM['SCM-Goto-First-Sub'] = Gtk.MenuItem('Go to First Subtitle')
        self.SCM['SCM-Goto-Last-Sub'] = Gtk.MenuItem('Go to Last Subtitle')
        self.SCM['SCM-Full-View'] = Gtk.MenuItem('Full View')
        sep1 = Gtk.SeparatorMenuItem()
        sep2 = Gtk.SeparatorMenuItem()
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-One'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-All'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-All-After'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Strech-Selected'])
        self.SCM['SCM-Menu'].add(sep1)
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Goto-First-Sub'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Goto-Last-Sub'])
        self.SCM['SCM-Menu'].add(sep2)
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Full-View'])

        self.SCM['SCM-Move-One'].show()
        self.SCM['SCM-Move-All'].show()
        self.SCM['SCM-Move-All-After'].show()
        self.SCM['SCM-Strech-Selected'].show()
        self.SCM['SCM-Goto-Last-Sub'].show()
        self.SCM['SCM-Goto-First-Sub'].show()
        self.SCM['SCM-Full-View'].show()
        sep1.show()
        sep2.show()

        self.connect('button-release-event', self.on_button_release)
        self.connect('key-press-event', self.on_key_press_event)
        self.connect('key-release-event', self.on_key_release_event)
        self.SCM['SCM-Move-One'].connect('activate', self.on_SCM, 'SCM-Move-One')
        self.SCM['SCM-Move-All'].connect('activate', self.on_SCM, 'SCM-Move-All')
        self.SCM['SCM-Move-All-After'].connect('activate', self.on_SCM, 'SCM-Move-All-After')
        self.SCM['SCM-Strech-Selected'].connect('activate', self.on_SCM, 'SCM-Strech-Selected')
        self.SCM['SCM-Goto-First-Sub'].connect('activate', self.on_SCM, 'SCM-Goto-First-Sub')
        self.SCM['SCM-Goto-Last-Sub'].connect('activate', self.on_SCM, 'SCM-Goto-Last-Sub')
        self.SCM['SCM-Full-View'].connect('activate', self.on_SCM, 'SCM-Full-View')
        self.videoModel.connect('position-update', self.on_video_position)
        button_ok.connect('clicked', self.on_button_clicked, 'ok')
        button_cancel.connect('clicked', self.on_button_clicked, 'cancel')
        self.show_all()
        self.show()

    def on_button_clicked(self, widget, value):
        if value == 'ok':
            self.response = Gtk.ResponseType.OK
        if value == 'cancel':
            self.response = Gtk.ResponseType.CANCEL
        else:
            self.result = Gtk.ResponseType.NONE
        self.close()

    def on_key_press_event(self, sender, event):
        return True

    def on_key_release_event(self, sender, event):
        if event.keyval in [Gdk.KEY_F12, Gdk.KEY_F, Gdk.KEY_f, 2006, 2038] and not event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.videoDuration == 0:
                return
            if self.videoModel.is_playing():
                self.videoModel.pause()
            else:
                self.videoModel.set_videoPosition(int(self.audioWidget.videoSegment[0]) / float(self.videoDuration))
                self.videoModel.set_segment((self.audioWidget.videoSegment[0],  self.videoDuration))
                self.videoModel.play()
        elif event.keyval == Gdk.KEY_F1:
            if self.videoDuration == 0:
                return
            self.videoModel.set_videoPosition(int(self.audioWidget.videoSegment[0]) / float(self.videoDuration))
            self.videoModel.set_segment(self.audioWidget.videoSegment)
            self.videoModel.play()
        elif event.keyval == Gdk.KEY_Escape:
            self.videoModel.pause()
        return

    def on_button_release(self, sender, event):
        if event.button == 3 and self.audioWidget.mode == None:
            self.SCM['SCM-Menu'].popup(None, None, None, None, event.button, event.time)

    def on_SCM(self, sender, value):
        if value in ['SCM-Move-All', 'SCM-Move-One', 'SCM-Move-All-After', 'SCM-Strech-Selected']:
            self.audioWidget.mode = value
            subs = self.audioWidget.subtitlesModel.get_sub_list()
            for sub in subs:
                sub.startTime_orig = int(sub.startTime)
                sub.stopTime_orig = int(sub.stopTime)
        elif value == 'SCM-Goto-First-Sub':
            sub = self.audioWidget.subtitlesModel.get_sub_list()[0]
            self.audioWidget.stickZoom = True
            self.audioWidget.activeSub = sub
            self.audioWidget.center_active_sub()
            self.audioWidget.stickZoom = False
        elif value == 'SCM-Goto-Last-Sub':
            sub = self.audioWidget.subtitlesModel.get_sub_list()[-1]
            self.audioWidget.stickZoom = True
            self.audioWidget.activeSub = sub
            self.audioWidget.center_active_sub()
            self.audioWidget.stickZoom = False
        elif value == 'SCM-Full-View':
            self.audioWidget.viewportUpper = 1
            self.audioWidget.viewportLower = 0
            self.audioWidget.invalidateCanvas()
            self.audioWidget.queue_draw()

    def on_video_position(self, sender, position):
        self.audioWidget.pos = self.parent['audio'].pos

        # Follow video position in audioview
        pos = self.audioWidget.pos / float(self.audioWidget.videoDuration)
        vup = self.audioWidget.viewportUpper
        vlow = self.audioWidget.viewportLower
        vdiff = vup - vlow
        if pos > vlow + vdiff * 0.98 and vup < 1:
            if pos - vdiff * 0.90 < 1:
                self.audioWidget.viewportLower = pos - vdiff * 0.10
                self.audioWidget.viewportUpper = pos + vdiff * 0.90
            else:
                self.audioWidget.viewportUpper = 1
                self.audioWidget.viewportLower = 1 - vdiff
            self.audioWidget.queue_draw()
        if pos < vlow:
            if pos - vdiff * 0.10 > 0:
                self.audioWidget.viewportLower = pos - vdiff * 0.10
                self.audioWidget.viewportUpper = pos + vdiff * 0.90
            else:
                self.audioWidget.viewportLower = 0
                self.audioWidget.viewportUpper = vdiff
            self.audioWidget.queue_draw()
