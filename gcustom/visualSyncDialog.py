# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from subtitles import subRec, timeStamp
from bisect import bisect
from time import time
import cairo

class sSubRec:
    def __init__(self, _obj, _startTime, _stopTime):
        self.obj = _obj
        self.startTime = _startTime
        self.stopTime = _stopTime

class cSyncAudioWidget(Gtk.EventBox):
    __gsignals__ = {       'sync-viewpos-update': (GObject.SIGNAL_RUN_LAST, None, (int,)),
                              'sync-sub-updated': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              'sync-right-click': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              'sync-dragged-sub': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)),
                              'sync-vertical-scale-update': (GObject.SIGNAL_RUN_LAST, None, (float,)),
                              'sync-active-sub-changed' : (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              }

    def __init__(self, container, replaceWidget):
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
        self.mouse_button = None
        self.mouse_click_coords = None
        self.mouse_click_type = None
        self.mouse_event = None
        self.mouse_last_event = None
        self.mouse_last_click_coords = None
        self.ms_to_coord_factor = 0
        self.low_ms_coord = 0
        self.mode = None
        self._container = container
        self._replaceWidget = replaceWidget
        self.save = False
        self.dragging_sub = None
        self.dragging_sublist = []
        self.dragging_dict = {}

        # Creating internal properties
        self.__viewportLower = None
        self.__viewportUpper = None
        self.__overSub = None
        self.__width = None
        self.__pos = None
        self.__cursor = None
        self.__audioDuration = None
        self.__highms = None
        self.__lowms = None
        self.__subs = None
        self.__audioData = None
        self.__audioModel = None
        self.__activeSub = None
        self.__scale_linear_audio = 1

        # Init Class Variables
        self.mouse_over_sub = None
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
        self.audioDuration = 0
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

        self.SCM = {}
        self.SCM['SCM-Menu'] = Gtk.Menu()
        self.SCM['SCM-Move-One'] = Gtk.MenuItem('Move selected subtitle')
        self.SCM['SCM-Move-All'] = Gtk.MenuItem('Move all Subtitles')
        self.SCM['SCM-Move-All-After'] = Gtk.MenuItem('Move subtitle and all after selected')
        self.SCM['SCM-Strech-Selected'] = Gtk.MenuItem('Stretch subtitles to follow selected')
        self.SCM['SCM-Goto-First-Sub'] = Gtk.MenuItem('Go to First Subtitle')
        self.SCM['SCM-Goto-Last-Sub'] = Gtk.MenuItem('Go to Last Subtitle')
        self.SCM['SCM-Full-View'] = Gtk.MenuItem('Full View')
        self.SCM['SCM-Save-Exit'] = Gtk.MenuItem('Accept & Exit Sync Mode')
        self.SCM['SCM-Cancel-Exit'] = Gtk.MenuItem('Discard & Exit Sync Mode')
        sep1 = Gtk.SeparatorMenuItem()
        sep2 = Gtk.SeparatorMenuItem()
        sep3 = Gtk.SeparatorMenuItem()
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-One'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-All'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Move-All-After'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Strech-Selected'])
        self.SCM['SCM-Menu'].add(sep1)
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Goto-First-Sub'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Goto-Last-Sub'])
        self.SCM['SCM-Menu'].add(sep2)
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Full-View'])
        self.SCM['SCM-Menu'].add(sep3)
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Save-Exit'])
        self.SCM['SCM-Menu'].add(self.SCM['SCM-Cancel-Exit'])

        self.SCM['SCM-Move-One'].show()
        self.SCM['SCM-Move-All'].show()
        self.SCM['SCM-Move-All-After'].show()
        self.SCM['SCM-Strech-Selected'].show()
        self.SCM['SCM-Goto-Last-Sub'].show()
        self.SCM['SCM-Goto-First-Sub'].show()
        self.SCM['SCM-Full-View'].show()
        sep1.show()
        sep2.show()
        sep3.show()
        self.SCM['SCM-Save-Exit'].show()
        self.SCM['SCM-Cancel-Exit'].show()

        self.SCM['SCM-Move-One'].connect('activate', self.on_SCM, 'SCM-Move-One')
        self.SCM['SCM-Move-All'].connect('activate', self.on_SCM, 'SCM-Move-All')
        self.SCM['SCM-Move-All-After'].connect('activate', self.on_SCM, 'SCM-Move-All-After')
        self.SCM['SCM-Strech-Selected'].connect('activate', self.on_SCM, 'SCM-Strech-Selected')
        self.SCM['SCM-Goto-First-Sub'].connect('activate', self.on_SCM, 'SCM-Goto-First-Sub')
        self.SCM['SCM-Goto-Last-Sub'].connect('activate', self.on_SCM, 'SCM-Goto-Last-Sub')
        self.SCM['SCM-Full-View'].connect('activate', self.on_SCM, 'SCM-Full-View')
        self.SCM['SCM-Save-Exit'].connect('activate', self.on_SCM, 'SCM-Save-Exit')
        self.SCM['SCM-Cancel-Exit'].connect('activate', self.on_SCM, 'SCM-Cancel-Exit')

        # Connections
        self.drawingArea.connect('draw', self.on_draw)
        self.drawingArea.connect('size-allocate', self.on_size_allocate)
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('scroll-event', self.on_scroll)
        self.connect('motion-notify-event', self.on_motion_notify)

        self._container.pack_start(self, True, True, 0)
        self.show()
        self.show_all()
        self._replaceWidget.hide()

    def set_scenes(self, ref):
        self.scenes = ref

    def on_button_press(self, widget, event):
        if self.audioDuration == 0:
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

            if self.mode == None:
                self.SCM['SCM-Menu'].popup(None, None, None, None, event.button, event.time)

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
            self.emit('sync-right-click', self.mouse_event)

    def over_sub_check(self, mousex):
        # bisect
        self.mouse_over_sub = None
        for sub in self.subList:
            if sub.startTime - self.mspp * 2 <= self.get_mouse_msec(mousex) <= sub.stopTime + self.mspp * 2:
                self.mouse_over_sub = sub
                break

    def on_button_release(self, widget, event):
        if not self.dragging:
            self.check_click()
        else:
            if self.dragging_sub != None:
                self.emit('sync-dragged-sub', self.dragging_sub, self.overSub)
        self.mouse_button = None
        self.mouse_click_coords =(None, None)
        self.mouse_click_type = None
        self.mouse_event = None
        self.dragging = False
        self.dragging_sub = None
        self.mode = None

        for item in self.dragging_sublist:
            item.obj.startTime = item.startTime
            item.obj.stopTime = item.stopTime
        self.dragging_sublist = []
        self.dragging_dict = {}

    def on_dragging(self, origmsec, msec):
        if self.overSub == None:
            return

        if self.dragging_sublist == []:
            if self.mode == 'SCM-Move-One':
                self.dragging_sublist = [ sSubRec(self.overSub, int(self.overSub.startTime), int(self.overSub.stopTime)) ]
            elif self.mode == 'SCM-Move-All':
                self.dragging_sublist = [ sSubRec(sub, int(sub.startTime), int(sub.stopTime)) for sub in self.subtitlesModel.get_sub_list() ]
            elif self.mode == 'SCM-Move-All-After':
                lst = self.subtitlesModel.get_sub_list()
                self.dragging_sublist = [ sSubRec(sub, int(sub.startTime), int(sub.stopTime)) for sub in lst[lst.index(self.overSub):] ]
            elif self.mode == 'SCM-Strech-Selected':
                lst = self.subtitlesModel.get_sub_list()
                self.dragging_sublist = [ sSubRec(sub, int(sub.startTime), int(sub.stopTime)) for sub in lst[:lst.index(self.overSub) + 1] ]
            for item in self.dragging_sublist:
                self.dragging_dict[item.obj] = item

        if self.mode == 'SCM-Strech-Selected':
            subs = self.dragging_sublist
            subs[-1].startTime = int(subs[-1].obj.startTime) + (msec - origmsec)
            subs[-1].stopTime = int(subs[-1].obj.stopTime) + (msec - origmsec)
            factor = (subs[-1].startTime - subs[0].startTime) / float( int(subs[-1].obj.startTime) - subs[0].startTime)
            for sub in subs[:-1]: # calculate strech here
                sub.startTime = int( (int(sub.obj.startTime) - subs[0].startTime) * factor + subs[0].startTime )
                sub.stopTime = int( (int(sub.obj.stopTime) - subs[0].startTime) * factor + subs[0].startTime )
            subs[-1].stopTime = int( (int(subs[-1].obj.stopTime) - subs[0].startTime) * factor + subs[0].startTime )
        else:
            for sub in self.dragging_sublist:
                sub.startTime = int(sub.obj.startTime) + (msec - origmsec)
                sub.stopTime = int(sub.obj.stopTime) + (msec - origmsec)

        if not (self.mode is None):
            self.isCanvasBufferValid = False
            self.queue_draw()
            self.emit('sync-sub-updated', self.overSub)

    def on_motion_notify(self, widget, event):
        if self.audioDuration == 0:
            return

        mos = self.mouse_over_sub
        self.over_sub_check(event.x)
        if mos != self.mouse_over_sub:
            self.queue_draw()

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
        if self.audioDuration == 0:
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
        if self.audioDuration == 0:
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
        if event.direction == Gdk.ScrollDirection.DOWN and self.highms + moveval < self.audioDuration:
            self.viewportLower = (self.lowms + moveval) / float(self.audioDuration)
            self.viewportUpper = (self.highms + moveval) / float(self.audioDuration)
        elif event.direction == Gdk.ScrollDirection.UP and self.lowms > moveval:
            self.viewportLower = (self.lowms - moveval) / float(self.audioDuration)
            self.viewportUpper = (self.highms - moveval) / float(self.audioDuration)

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
            self.emit('sync-vertical-scale-update', self.__scale_linear_audio)

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
            self.orig_audioModel_width = val.get_width()
            self.__audioModel = val
            self.__audioModel.set_width(self.get_allocation().width)
            self.audioData = self.__audioModel.get_data(self.viewportLower, self.viewportUpper)

    @property
    def audioData(self):
        return self.__audioData

    @audioData.setter
    def audioData(self, val):
        if val != None:
            self.isReady = self.audioDuration != 0
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
            self.videoSegment = (val, self.audioDuration)
            self.queue_draw()
        self.__cursor = val

    @property
    def audioDuration(self):
        return self.__audioDuration

    @audioDuration.setter
    def audioDuration(self, val):
        if val != 0:
            self.__audioDuration = val
            self.isParamtersValid = False
            self.isCanvasBufferValid = False
            self.isWaveformBufferValid = False
            self.isReady = self.audioData != None
            self.videoSegment = (0, val)
        else:
            self.__audioDuration = val

    @property
    def activeSub(self):
        return self.__activeSub

    @activeSub.setter
    def activeSub(self, val):
        if val != None:
            self.videoSegment = (int(val.startTime), int(val.stopTime))
        else:
            self.videoSegment = (self.cursor, self.audioDuration)
        if self.__activeSub != val:
            self.emit('sync-active-sub-changed', val)
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
        return (ms / self.audioDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) * widget.get_allocation().width

    def calc_parameters(self):
        self.lowms = self.viewportLower * self.audioDuration
        self.highms = self.viewportUpper * self.audioDuration
        self.mspp = (self.highms - self.lowms) / float(self.width)
        self.grayarea = self.grayms / self.mspp
        if self.subtitlesModel != None:
            self.subList = set(self.subtitlesModel.list_subs_overlapping_window(self.lowms - 120, self.highms))
        self.ms_to_coord_factor = self.width / (float(self.viewportUpper - self.viewportLower) * self.audioDuration)
        self.low_ms_coord  = (self.viewportLower * self.width) / float(self.viewportUpper - self.viewportLower)

    def center_active_sub(self):
        low = int(self.activeSub.startTime)
        high = int(self.activeSub.stopTime)
        msdur = (high - low) / 2
        if self.stickZoom:
            vpwidthms = (self.viewportUpper - self.viewportLower) * float(self.audioDuration)
            centerms = (low + msdur)
            lms = (centerms - (vpwidthms / 2))
            ums = (centerms + (vpwidthms / 2))
            if lms < 0:
                ums += abs(lms)
                lms = 0
            elif ums > self.audioDuration:
                lms -= ums - self.audioDuration
                ums = self.audioDuration
            self.viewportLower = lms / float(self.audioDuration)
            self.viewportUpper = ums / float(self.audioDuration)
        else:
            if msdur < 1000:
                msdur = 1000
            low -= msdur
            high += msdur
            if low < 0:
                low = 0
            if high > self.audioDuration:
                high = self.audioDuration
            self.viewportLower = (low / float(self.audioDuration))
            self.viewportUpper = (high / float(self.audioDuration))

        self.isCanvasBufferValid = False
        self.cursor = low
        self.queue_draw()
        self.videoSegment = (int(self.activeSub.startTime), int(self.activeSub.stopTime))
        self.emit('sync-viewpos-update', int(low * 100.0 / self.audioDuration))

    def center_multiple_active_subs(self, startTime, stopTime):
        self.videoSegment = (int(startTime), int(stopTime))
        subWidthPerc = (stopTime - startTime) / float(self.audioDuration)
        lowPerc = startTime / float(self.audioDuration) - subWidthPerc * 0.8
        highPerc = stopTime / float(self.audioDuration) + subWidthPerc * 0.8
        self.viewportLower = lowPerc if lowPerc >= 0 else 0
        self.viewportUpper = highPerc if highPerc <= 1 else 1
        self.queue_draw()
        self.emit('sync-viewpos-update', int(lowPerc * 100))

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
            dsub = sub
            if sub in self.dragging_dict.keys():
                dsub = self.dragging_dict[sub]
            paintlow = dsub.startTime * self.ms_to_coord_factor - self.low_ms_coord if dsub.startTime >= self.lowms else 0
            painthigh = dsub.stopTime * self.ms_to_coord_factor - self.low_ms_coord if dsub.stopTime <= self.highms else self.width
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
            if dsub.startTime >= self.lowms and dsub.startTime <= self.highms:
                cc.move_to(paintlow, 2)
                cc.line_to(paintlow, height - 2)
                cc.move_to(paintlow+1, 2)
                cc.line_to(paintlow+1, height - 2)
            if dsub.stopTime >= self.lowms and dsub.stopTime <= self.highms:
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

        # Draw subtitle under mouse
        if not (self.mouse_over_sub is None):
            fontSize = 14
            cc.set_font_size(fontSize)
            cc.set_source_rgba(0.8, 0.8, 0.0, 1)
            tmpText = self.mouse_over_sub.text.splitlines()
            if tmpText != []:
                tmpSize = cc.text_extents(max(tmpText, key=len))
                for i in xrange(len(tmpText)):
                    cc.move_to(2, 20 + i * (tmpSize[3] + 5))
                    cc.show_text(tmpText[i])

    def on_SCM(self, sender, value):
        if value in ['SCM-Move-All', 'SCM-Move-One', 'SCM-Move-All-After', 'SCM-Strech-Selected']:
            self.mode = value
            subs = self.subtitlesModel.get_sub_list()
        elif value == 'SCM-Goto-First-Sub':
            sub = self.subtitlesModel.get_sub_list()[0]
            self.stickZoom = True
            self.activeSub = sub
            self.center_active_sub()
            self.stickZoom = False
        elif value == 'SCM-Goto-Last-Sub':
            sub = self.subtitlesModel.get_sub_list()[-1]
            self.stickZoom = True
            self.activeSub = sub
            self.center_active_sub()
            self.stickZoom = False
        elif value == 'SCM-Full-View':
            self.viewportUpper = 1
            self.viewportLower = 0
            self.invalidateCanvas()
            self.queue_draw()
        elif value == 'SCM-Save-Exit':
            self.save = True
            self.destroy()
        elif value == 'SCM-Cancel-Exit':
            self.save = False
            self.destroy()

    def on_destroy(self, sender):
        self.hide()
        self._container.remove(self)
        self.audioModel.set_width(self.orig_audioModel_width)
