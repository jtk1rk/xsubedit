import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, Gdk, GObject
from subtitles import subRec

class cAudioWidget(Gtk.EventBox):
    __gsignals__ = {       'viewpos-update': (GObject.SIGNAL_RUN_LAST, None, (int,)),
                              'sub-updated': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )), 
                              'right-click': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )), 
                              'dragged-sub': (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, GObject.TYPE_PYOBJECT)), 
                              'vertical-scale-update': (GObject.SIGNAL_RUN_LAST, None, (float,)), 
                              'active-sub-changed' : (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, )),
                              'tmpSub-update': (GObject.SIGNAL_RUN_LAST, None, ()), 
                              'handle-double-click' : (GObject.SIGNAL_RUN_LAST, None, (GObject.TYPE_PYOBJECT, int))
                              }

    def __init__(self):
        # Inits
        super(cAudioWidget, self).__init__()
        self.drawingArea = Gtk.DrawingArea()
        self.add(self.drawingArea)
        self.set_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.cursorLeftMargin = Gdk.Cursor(Gdk.CursorType.LEFT_SIDE)
        self.cursorRightMargin = Gdk.Cursor(Gdk.CursorType.RIGHT_SIDE)

        # Class constants and internal variables
        self.HANDLE_START = 1
        self.HANDLE_END = 2
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

        # Creating internal properties
        self.__viewportLower = None
        self.__viewportUpper = None
        self.__overSub = None
        self.__overHandle = None
        self.__width = None
        self.__pos = None
        self.__cursor = None
        self.__videoDuration = None
        self.__highms = None
        self.__lowms = None
        self.__tmpSub = None
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
        self.voList = []
        self.tmpSub = None
        self.activeSub = None
        self.overSub = None
        self.overHandle = None
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
        self.voModel = None

        # Connections
        self.drawingArea.connect('draw', self.on_draw)
        self.drawingArea.connect('size-allocate', self.on_size_allocate)
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('scroll-event', self.on_scroll)
        self.connect('motion-notify-event', self.on_motion_notify)

    def on_button_press(self, widget, event):
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
        if self.mouse_click_type == self.DOUBLE_CLICK and self.overHandle == self.HANDLE_END and self.overSub != self.tmpSub:
            if self.overSub.rs != 20:
                duration_diff = self.overSub.calc_target_duration() - int(self.overSub.duration)
                nextSub = self.subtitlesModel.get_next(self.overSub)
                next_ms = int(nextSub.startTime if nextSub != None else self.videoDuration)
                old_st = int(self.overSub.stopTime)
                if duration_diff < 0:
                    self.overSub.stopTime = int(self.overSub.stopTime) + duration_diff
                else:
                    self.overSub.stopTime = min((next_ms - 120), int(self.overSub.stopTime) + duration_diff)
                self.isCanvasBufferValid = False
                self.queue_draw()
                self.emit('sub-updated', self.overSub)
                self.emit('handle-double-click', self.overSub, old_st)

        if self.mouse_click_type == self.DOUBLE_CLICK and self.overHandle == None and self.overSub != None and self.overSub != self.tmpSub:
            self.activeSub = self.overSub
            self.isCanvasBufferValid = False
            self.queue_draw()

        if self.mouse_button == self.BUTTON_LEFT:
            self.tmpSub = None
            self.activeSub = None
            self.cursor = self.get_mouse_msec(self.mouse_click_coords[0])
            self.isCanvasBufferValid = False
            self.queue_draw()

        if self.mouse_click_type == self.DOUBLE_CLICK and self.overSub != None and self.overSub != self.tmpSub:
            self.tmpSub = None
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
            if self.tmpSub == None and self.dragging_sub != None:
                self.emit('dragged-sub', self.dragging_sub, self.overSub)
        self.mouse_button = None
        self.mouse_click_coords =(None, None)
        self.mouse_click_type = None
        self.mouse_event = None
        self.dragging = False
        self.dragging_sub = None

    def on_dragging(self, msec):
        if self.overHandle != None:
            if self.overSub != self.tmpSub:
                self.tmpSub = None
            # In this case we are dragging a subtitle handle
            target_time = None
            if self.dragging_sub == None:
                self.dragging_sub = subRec(int(self.overSub.startTime), int(self.overSub.stopTime), self.overSub.text)
            if self.overHandle == self.HANDLE_START:
                prevSub = self.subtitlesModel.get_prev(self.overSub)
                if prevSub == None:
                    target_time = msec if msec > 0 else None
                else:
                    target_time = msec if prevSub.stopTime + 120 <= msec else int(prevSub.stopTime + 120)
                target_time = target_time if target_time < self.overSub.stopTime else None
                if target_time:
                    self.activeSub = self.overSub
                    self.overSub.startTime = target_time
                    self.isCanvasBufferValid = False
                    self.queue_draw()
                    if self.overSub != self.tmpSub:
                        self.emit('sub-updated', self.overSub)
            elif self.overHandle == self.HANDLE_END:
                nextSub = self.subtitlesModel.get_next(self.overSub)
                if nextSub == None:
                    target_time = msec if msec < self.videoDuration - 120 else None
                else:
                    target_time = msec if nextSub.startTime - 120 >= msec else int(nextSub.startTime - 120)
                target_time = target_time if target_time > self.overSub.startTime else None
                if target_time:
                    self.activeSub = self.overSub
                    self.overSub.stopTime = target_time
                    self.isCanvasBufferValid = False
                    self.queue_draw()
                    if self.overSub != self.tmpSub:
                        self.emit('sub-updated', self.overSub)
        else:
            # In this case we are creating a temporary sub
            target_time = msec if self.lowms <= msec <= self.highms else None
            initial_msec = self.get_mouse_msec(self.mouse_click_coords[0])
            if self.tmpSub == None:
                if target_time and (abs(target_time - initial_msec) / self.mspp) > 6:
                    self.tmpSub = subRec(min(initial_msec, target_time), max(initial_msec, target_time), '')
                else:
                    if target_time:
                        self.cursor = target_time
                        self.isCanvasBufferValid = False
                        self.queue_draw()
            else:
                if target_time and (abs(target_time - initial_msec) / self.mspp) > 6:
                    self.tmpSub.startTime = min(initial_msec, target_time)
                    self.tmpSub.stopTime = max(initial_msec, target_time)
                    self.emit('tmpSub-update')
                    self.videoSegment = ( int(self.tmpSub.startTime), int(self.tmpSub.stopTime))
                    self.isCanvasBufferValid = False
                    self.queue_draw()
                else:
                    self.tmpSub = None
                    if target_time:
                        self.cursor = target_time
                        self.isCanvasBufferValid = False
                        self.queue_draw()

    def on_motion_notify(self, widget, event):
        if self.videoDuration == 0:
            return

        mouse_msec = self.get_mouse_msec(event.x)
        if self.mouse_button == self.BUTTON_LEFT and mouse_msec != self.mouse_click_coords[0]:
            self.dragging = True

        if self.dragging:
            target_msec = mouse_msec
            target_msec = target_msec if target_msec < self.highms else self.highms
            target_msec = target_msec if target_msec > self.lowms else self.lowms
            self.on_dragging(target_msec)
        else:
            self.overSub = None

            # Check if we are over a sub
            for sub in self.subList:
                if sub.startTime - self.mspp * 2 <= mouse_msec <= sub.stopTime + self.mspp * 2:
                    self.overSub = sub
                    break

            if self.tmpSub != None and self.tmpSub.startTime - self.mspp * 2 <= mouse_msec <= self.tmpSub.stopTime + self.mspp * 2:
                self.overSub = self.tmpSub

            # If we are over a sub, check if we are over a handle
            if self.overSub != None:
                if self.overSub.startTime - self.mspp * 2 <= mouse_msec <= self.overSub.startTime + self.mspp * 2:
                    self.overHandle = self.HANDLE_START
                elif self.overSub.stopTime - self.mspp * 2 <= mouse_msec <= self.overSub.stopTime + self.mspp * 2:
                    self.overHandle = self.HANDLE_END
                else:
                    self.overHandle = None
            if self.overSub == None:
                self.overHandle = None

    def zoom(self, direction, xcoord):
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

        self.calc_parameters()
        moveval = self.mspp
        if event.direction == Gdk.ScrollDirection.UP and self.highms < self.videoDuration + moveval:
            self.viewportLower = (self.lowms + moveval) / float(self.videoDuration)
            self.viewportUpper = (self.highms + moveval) / float(self.videoDuration)
        elif event.direction == Gdk.ScrollDirection.DOWN and self.lowms > moveval:
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
    def overHandle(self):
        return self.__overHandle

    @overHandle.setter
    def overHandle(self, val):
        window = self.get_window()
        if window != None:
            if val == None:
                window.set_cursor(None)
            else:
                current_cursor = window.get_cursor()
                if val == self.HANDLE_START and current_cursor != self.cursorLeftMargin:
                    window.set_cursor(self.cursorLeftMargin)
                if val == self.HANDLE_END and current_cursor != self.cursorRightMargin:
                    window.set_cursor(self.cursorRightMargin)
        self.__overHandle = val

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
    def tmpSub(self):
        return self.__tmpSub

    @tmpSub.setter
    def tmpSub(self, val):
        if val == None and self.__tmpSub != None:
            self.videoSegment = (int(self.__tmpSub.startTime), self.videoDuration)
        if val != None:
            self.videoSegment = (int(val.startTime), int(val.stopTime))
        self.emit('tmpSub-update')
        self.isCanvasBufferValid = False
        self.queue_draw()
        self.__tmpSub = val

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

    def calc_parameters(self):
        self.lowms = self.viewportLower * self.videoDuration
        self.highms = self.viewportUpper * self.videoDuration
        self.mspp = (self.highms - self.lowms) / float(self.width)
        self.grayarea = self.grayms / self.mspp
        if self.subtitlesModel != None:
            self.subList = set(self.subtitlesModel.list_subs_overlapping_window(self.lowms - 120, self.highms))
        self.voList = self.voModel.get_subs_in_range(self.lowms - 120, self.highms)

    def center_active_sub(self):
        vpdiff = 0.017
        low = int(self.activeSub.startTime)
        high = int(self.activeSub.stopTime)
        if low < 0:
            low = 0
        if high > self.videoDuration:
            high = self.videoDuration
        self.viewportLower = (low / float(self.videoDuration)) * (1-vpdiff)
        self.viewportUpper = (high / float(self.videoDuration)) * (1+vpdiff)
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
            cc.set_source_rgba(0.0702, 0.5616, 0.2808, 0.8)
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
            paintlow = ((sub.startTime / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if sub.startTime >= self.lowms else 0) * self.width
            painthigh = ((sub.stopTime / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if sub.stopTime <= self.highms else 1) * self.width
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

        for sub in self.voList:
            paintlow = ((sub[0] / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if sub[0] >= self.lowms else 0) * self.width
            painthigh = ((sub[1] / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if sub[1] <= self.highms else 1) * self.width
            cc.set_source_rgba(0.3, 0.4, 0.9, 0.7)
            cc.set_dash([6, 6, 6, 4])
            if sub[0] >= self.lowms and sub[0] <= self.highms:
                cc.move_to(paintlow, (2/3.0) * height)
                cc.line_to(paintlow, height - 2)
                cc.move_to(paintlow+1, (2/3.0) * height)
                cc.line_to(paintlow+1, height - 2)
            if sub[1] >= self.lowms and sub[1] <= self.highms:
                cc.move_to(painthigh, (2/3.0) * height)
                cc.line_to(painthigh, height - 2)
                cc.move_to(painthigh-1, (2/3.0) * height)
                cc.line_to(painthigh-1, height - 2)
            cc.stroke()

            # Draw Subtitle Text
            cc.set_source_rgba(0.5, 0.5, 0.8, 0.9)
            tmpText = sub[2].splitlines()
            if tmpText != []:
                tmpSize = cc.text_extents(max(tmpText, key=len))
                if tmpSize[2] < painthigh - paintlow:
                    linecount = len(tmpText)
                    for i in xrange(len(tmpText)):
                        cc.move_to(paintlow+2, height - (linecount * (tmpSize[3] + 2)) + i * (tmpSize[3] + 5))
                        cc.show_text(tmpText[i])

        # Draw tmpSub
        if self.tmpSub != None and ((self.lowms <= self.tmpSub.startTime <= self.highms) or (self.lowms <= self.tmpSub.stopTime <= self.highms)):
            paintlow = ((self.tmpSub.startTime / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if self.tmpSub.startTime >= self.lowms else 0) * self.width
            painthigh = ((self.tmpSub.stopTime / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower) if self.tmpSub.stopTime <= self.highms else 1) * self.width
            cc.set_source_rgba(1,1,1,0.7)
            cc.rectangle(paintlow, 2, painthigh - paintlow, height - 4)
            cc.fill()

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
        viewportPos = (self.pos / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower)
        if 0 <= viewportPos <= 1:
            cc.set_source_rgba(0.8, 0.8, 0.1, 0.7)
            cc.move_to(viewportPos*width, 0)
            cc.line_to(viewportPos*width, height)
            cc.stroke()

        # Draw Cursor
        viewportPos = (self.cursor / self.videoDuration - self.viewportLower) / float(self.viewportUpper - self.viewportLower)
        if 0 <= viewportPos <= 1:
            cc.set_source_rgba(0.8, 0.8, 0.8, 1)
            cc.set_dash([1,3])
            cc.move_to(viewportPos*width, 0)
            cc.line_to(viewportPos*width, height)
            cc.stroke()
