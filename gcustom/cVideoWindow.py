import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class cMouseHandler(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.button  = None
        self.dragging = False
        self.orig_x = None
        self.orig_y = None
        self.x = None
        self.y = None

    def update_event(self, event_type, event):
        if event_type == 'release':
            self.clear()
        elif event_type == 'press':
            self.clear()
            self.button = event.button
            self.orig_x = event.x
            self.orig_y = event.y
            self.x = event.x
            self.y = event.y
        elif event_type  == 'motion':
            if self.button == 1:
                self.dragging = True
                self.x_dist = self.x - self.orig_x
                self.y_dist = self.y - self.orig_y
            self.x = event.x
            self.y = event.y

class cVideoWindow(Gtk.Window):
    def __init__(self, parent, controller):
        super(cVideoWindow, self).__init__()
        self.parent = parent
        self.set_keep_above(True)
        self.set_size_request(200, 100)
        self.resize(480, 240)
        self.set_decorated(False)
        self.mouse = cMouseHandler()

        self.DrawingArea = Gtk.DrawingArea()
        EventBox = Gtk.EventBox()
        EventBox.set_events(Gdk.EventMask.POINTER_MOTION_MASK)
        EventBox.add(self.DrawingArea)
        self.add(EventBox)
        self.controller = controller
        self.VCM = Gtk.Menu()
        VCM_Close = Gtk.MenuItem('Close')
        self.VCM_Lock = Gtk.CheckMenuItem('Lock')
        self.VCM.add(VCM_Close)
        self.VCM.add(self.VCM_Lock)
        self.VCM.show_all()
        self.override_background_color(0, Gdk.RGBA(0,0,0,1))

        EventBox.connect('button-release-event', self.on_drawingarea_button_release)
        EventBox.connect('button-press-event', self.on_drawingarea_button_press)
        EventBox.connect('motion-notify-event', self.on_motion_notify)
        self.connect('key-release-event', self.on_key_release)
        VCM_Close.connect('activate', self.on_close_window)

        self.show_all()
        self.cursorBottomMargin = Gdk.Cursor(Gdk.CursorType.BOTTOM_SIDE)
        self.cursorRightMargin = Gdk.Cursor(Gdk.CursorType.RIGHT_SIDE)
        self.cursorCorner = Gdk.Cursor(Gdk.CursorType.BOTTOM_RIGHT_CORNER)
        self.cusrorDefault = self.get_window().get_cursor()
        self.resizing = False

    def update_cursor(self, current_cursor, new_cursor):
        if new_cursor != current_cursor:
            self.get_window().set_cursor(new_cursor)

    def update_size(self, x = None, y = None):
        self.resizing = True
        allocation = self.get_allocation()
        origin = self.get_window().get_root_origin()
        new_width = allocation.width if x is None else x - origin.x
        new_height = allocation.height if y is None else y - origin.y
        self.resize(new_width, new_height)

    def on_motion_notify(self, sender, event):
        if self.VCM_Lock.get_active():
            return
        self.mouse.update_event('motion', event)
        at_right_margin = event.x > self.get_allocation().width - 5
        at_bottom_margin = event.y > self.get_allocation().height - 5
        at_corner = at_bottom_margin and at_right_margin

        # Managing Cursor
        if not self.resizing:
            cursor = self.get_window().get_cursor()
            if at_corner:
                self.update_cursor(cursor, self.cursorCorner)
            elif at_bottom_margin:
                self.update_cursor(cursor, self.cursorBottomMargin)
            elif at_right_margin:
                self.update_cursor(cursor, self.cursorRightMargin)
            else:
                self.update_cursor(cursor, self.cusrorDefault)

        if not self.mouse.dragging:
            return

        # Check if resizing
        if self.mouse.click_at_corner:
            self.update_size(x = event.x_root, y = event.y_root)
        elif self.mouse.click_at_bottom_margin:
            self.update_size(y = event.y_root)
        elif self.mouse.click_at_right_margin:
            self.update_size(x = event.x_root)

        # if not resizing, move the window
        if not self.resizing:
            self.move(event.x_root - self.mouse.orig_x, event.y_root - self.mouse.orig_y)

    def on_key_release(self, sender, event):
        self.controller.on_key_release(sender, event)

    def on_drawingarea_button_press(self, sender, event):
        self.mouse.update_event('press', event)
        if event.button == 1:
            self.mouse.click_at_right_margin = event.x > self.get_allocation().width - 5
            self.mouse.click_at_bottom_margin = event.y > self.get_allocation().height - 5
            self.mouse.click_at_corner = self.mouse.click_at_bottom_margin and self.mouse.click_at_right_margin

    def on_drawingarea_button_release(self, sender, event):
        self.mouse.update_event('release', event)
        self.resizing = False
        self.mouse.click_at_right_margin = False
        self.mouse.click_at_bottom_margin = False
        self.mouse.click_at_corner = False
        if event.button == 3:
            self.VCM.popup(None, None, None, None, event.button, event.time)

    def on_close_window(self, sender):
        self.destroy()
