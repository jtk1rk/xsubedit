import gi
gi.require_version('GObject', '2.0')
from gi.repository import GObject
from utils import brList

class cHistory(GObject.GObject):
    __gsignals__ = { 'history-update': (GObject.SIGNAL_RUN_LAST, None, (int, )) }
    HIST_EMPTY = 1
    HIST_AT_LAST_ELEMENT = 2
    HIST_AT_INTERMEDIATE_ELEMENT = 3
    HIST_AT_FIRST_ELEMENT = 4

    def __init__(self):
        super(cHistory,  self).__init__()
        self.index = 0
        self.data = brList()
        self.tmpItem = None
        self.emit_state()

    def is_at_first_element(self):
        return self.index == 0

    def is_at_last_element(self):
        return self.index == len(self.data)

    def is_at_intermediate_element(self):
        return 0 < self.index < len(self.data)

    def is_empty(self):
        return len(self.data) == 0

    def back(self):
        tmp = self.data[self.index - 1]
        self.index -= 1
        self.emit_state()
        return tmp

    def forward(self):
        tmp = self.data[self.index]
        self.index +=1
        self.emit_state()
        return tmp

    def emit_state(self):
        if self.is_empty():
            self.emit('history-update', self.HIST_EMPTY)
            return
        if self.is_at_intermediate_element():
            self.emit('history-update', self.HIST_AT_INTERMEDIATE_ELEMENT)
        elif self.is_at_first_element():
            self.emit('history-update', self.HIST_AT_FIRST_ELEMENT)
        elif self.is_at_last_element():
            self.emit('history-update', self.HIST_AT_LAST_ELEMENT)

    def add(self,  value):
        self.data.append(self.index, value)
        self.index += 1
        self.emit_state()
