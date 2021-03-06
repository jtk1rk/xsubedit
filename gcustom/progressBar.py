import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class cProgressBar(Gtk.DrawingArea):
    def __init__(self, width=-1, height=20, request_size=True):
        self.__position = 0
        super(cProgressBar, self).__init__()
        if request_size:
            self.set_size_request(width, height)
        self.connect('draw', self.on_draw)
        self.show()

    @property
    def position(self):
        return self.__position

    @position.setter
    def position(self, value):
        self.__position = value
        self.queue_draw()

    def set_fraction(self, value):
        self.position = value

    def on_draw(self, widget, cc):
        width = widget.get_allocation().width
        height = widget.get_allocation().height
        cc.set_source_rgba(0.2, 0.2, 0.8, 1)
        cc.rectangle(0, height * 0.1, width * self.position, height * 0.80)
        cc.fill()
