# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, GObject
from mparser import markup_escape
import subutils, utils
import time

INFO_COLORS = ['#ff0000', '#ff9900', '#99cc00', '#339966', '#33cccc', '#3366ff', '#800080', '#969696', '#993300', '#ff99cc']

class timeStamp(GObject.GObject):

    def __init__(self, timeData = 0):
        super(timeStamp, self).__init__()
        self.__msec = 0
        self.msec = timeData
        self.changed = False

    @property
    def msec(self):
        return int(self.__msec)

    @msec.setter
    def msec(self, timeData):
        if type(timeData) == isinstance(timeData, timeStamp):
            if self.__msec != timeData.__msec:
                self.changed = True
            self.__msec = timeData.__msec
        if (type(timeData) == int) or (type(timeData) == float) or (type(timeData) == long):
            if self.__msec != timeData:
                self.changed = True
            self.__msec = timeData
        if type(timeData) == str and subutils.is_timestamp(timeData):
            if self.__msec != subutils.ts2ms(timeData):
                self.changed = True
            self.__msec = subutils.ts2ms(timeData)

    def __str__(self):
        return subutils.ms2ts(int(self.__msec))

    def __eq__(self, other):
        return self.msec == other.msec

    def __ne__(self,  other):
        return self.msec != other.msec

    def __gt__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return self.__msec > other
        if isinstance(other, timeStamp):
            return self.__msec > other.__msec
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return self.__msec > subutils.ts2ms(other)

    def __lt__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return self.__msec < other
        if isinstance(other, timeStamp):
            return self.__msec < other.__msec
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return self.__msec < subutils.ts2ms(other)

    def __ge__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return self.__msec >= other
        if isinstance(other, timeStamp):
            return self.__msec >= other.__msec
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return self.__msec >= subutils.ts2ms(other)

    def __le__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return self.__msec <= other
        if isinstance(other, timeStamp):
            return self.__msec <= other.__msec
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return self.__msec <= subutils.ts2ms(other)

    def __add__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return timeStamp(self.__msec + other)
        if isinstance(other, timeStamp):
            return timeStamp(self.__msec + other.__msec)
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return timeStamp(self.__msec + subutils.ts2ms(other))

    def __sub__(self, other):
        if type(other) == int or type(other) == long or type(other) == float:
            return timeStamp(self.__msec - other)
        if isinstance(other, timeStamp):
            return timeStamp(self.__msec - other.__msec)
        if type(other) == str:
            if not subutils.is_timestamp(other):
                raise Exception("Expected Integer, Timestamp or Timestamp class object")
            return timeStamp(self.__msec - subutils.ts2ms(other))

    def __trunc__(self):
        return int(self.__msec)

    def __mul__(self, other):
        return self.__msec * other

    def __div__(self, other):
        return self.__msec / other

class subRec(GObject.GObject):
    __gsignals__ = { 'updated': (GObject.SIGNAL_RUN_LAST, None, (str, )) }

    def __init__(self, startTime, stopTime, text):
        super(subRec, self).__init__()
        # Cache
        self.cache = {}
        # Internal Attributes
        self.__text = None
        self.__startTime = min(timeStamp(startTime), timeStamp(stopTime))
        self.__stopTime = max(timeStamp(startTime), timeStamp(stopTime))
        self.__info = {}
        self.__info_audio_str = ''
        self.__info_text_str = ''
        self.__rs = 0
        self.__rs_str = ''
        self.__duration_str = ''
        self.__duration = timeStamp(0)
        self.__char_count = []
        self.__char_count_str = ''
        self.__vo = ''
        # Attributes
        self.modified_timestamp = 0
        self.changed = False
        self.startTime = startTime
        self.stopTime = stopTime
        self.text = text
        self.update_data()

    @property
    def vo(self):
        return self.__vo

    @vo.setter
    def vo(self, value):
        if self.__vo != value:
            self.__vo = value
            self.emit('updated', 'vo')
        else:
            self.__vo = value

    @property
    def duration_str(self):
        return self.__duration_str

    @property
    def rs_str(self):
        return self.__rs_str

    @property
    def char_count_str(self):
        return self.__char_count_str

    @property
    def rs(self):
        return self.__rs

    @rs.setter
    def rs(self, value):
        if self.__rs != value:
            self.__rs = value
            self.__rs_str = '<span background="'+ utils.calc_info_color(self.rs)[1] +'" foreground="black">' + self.rs + '</span>'
            self.emit('updated', 'rs')
        else:
            self.__rs = value

    @property
    def duration(self):
        return self.__duration

    @duration.setter
    def duration(self, value):
        if self.__duration != value:
            self.__duration = value
            self.__duration_str = '<span foreground="#4ccc4ccc4ccc" background="'+(utils.RGB_to_hex((1,0.5,0.5)) if int(self.duration) < 1000 else utils.RGB_to_hex((1,1,1)))+'">'+str(self.duration)+'</span>'
            self.emit('updated','duration')

    @property
    def char_count(self):
        return self.__char_count

    @char_count.setter
    def char_count(self, value):
        if self.__char_count != value:
            self.__char_count = value
            limit = 40 if len(self.__char_count) > 1 else 30
            hex_color = utils.RGB_to_hex((1, 0.5, 0.5)) if max(self.char_count) > limit else utils.RGB_to_hex((1, 1, 1))
            self.__char_count_str = '\n'.join(['<span foreground="#4ccc4ccc4ccc" background="'+hex_color+'">'+str(ln)+'</span>' for ln in self.__char_count])
            self.emit('updated', 'char_count')
        else:
            self.__char_count = value

    @property
    def info(self):
        return self.__info

    def check_shared_interval(self, list1, list2):
        for item1 in list1:
            for item2 in list2:
                if not(item1[1] < item2[0] or item2[1] < item1[0]):
                    return True

    @info.setter
    def info(self, value):
        if value == {}:
            self.__info_text_str = ''
            self.__info_audio_str = ''
            self.__info = {}
            return
        if not self.__info.has_key(value[0]) or self.__info[value[0]] != value[1]:
            if value[1] == '': 
                if self.__info.has_key(value[0]):
                    self.__info.pop(value[0])
            else:
                self.__info[value[0]] = value[1]
            text_key_list = [key for key in self.__info if key.startswith('Text')]
            for i in xrange(len(text_key_list)):
                key = text_key_list[i]
                prev_color = None
                for j in xrange(0, i):
                    jkey = text_key_list[j]
                    if self.check_shared_interval(self.__info[key][1], self.__info[jkey][1]):
                        prev_color = self.__info[jkey][2]
                self.__info[key] = (self.__info[key][0], self.__info[key][1], prev_color if prev_color != None else INFO_COLORS[i % 10])
            tmp_text_color = [(self.__info[tmp_key][0], self.__info[tmp_key][2]) for tmp_key in text_key_list]
            self.__info_text_str = '\n'.join('<span foreground="black" background="' + line_color[1] + '">' + str(i+1) + '.' + '</span>' + ' ' + markup_escape(line_color[0]) for i, line_color in enumerate(tmp_text_color))
            self.__info_audio_str = '\n'.join(self.__info[key][0] for key in self.__info if key.startswith('Audio'))
            self.emit('updated', 'info')

    @property
    def info_text_str(self):
        return self.__info_text_str

    @property
    def info_audio_str(self):
        return self.__info_audio_str

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        if self.__text != value:
            self.__text = value
            self.emit('updated', 'text')
            self.changed = True
            self.modified_timestamp = time.time() - utils.RUN_TIMESTAMP
            self.update_data()
        else:
            self.__text = value

    @property
    def startTime(self):
        return self.__startTime

    @startTime.setter
    def startTime(self, value):
        if self.__startTime != timeStamp(value):
            self.__startTime.msec = value
            self.changed = True
            self.modified_timestamp = time.time() - utils.RUN_TIMESTAMP
            self.emit('updated', 'startTime')
            self.update_data()
        else:
            self.__startTime.msec = value

    @property
    def stopTime(self):
        return self.__stopTime

    @stopTime.setter
    def stopTime(self, value):
        if self.__stopTime != timeStamp(value):
            self.__stopTime.msec = value
            self.changed = True
            self.modified_timestamp = time.time() - utils.RUN_TIMESTAMP
            self.emit('updated', 'stopTime')
            self.update_data()
        else:
            self.__stopTime.msec = value

    def is_changed(self):
        return self.changed or self.startTime.changed or self.stopTime.changed

    def clear_changed(self):
        self.changed = False
        self.startTime.changed = False
        self.stopTime.changed = False

    def __str__(self):
        return (str(self.startTime) + " --> " + str(self.stopTime) + '\n' + self.text + '\n').encode("utf-8")

    def calc_char_count(self):
        if self.text == None or self.text == '':
            return [0]
        if 'char-count-text' in self.cache and self.text == self.cache['char-count-text']:
            self.char_count = self.cache['char-count-value']
            return
        lines_length = []
        lines = self.text.splitlines()
        for line in lines:
            lines_length.append(len(utils.untagged_text(line)))
        self.char_count = lines_length
        self.cache['char-count-text'] = self.text
        self.cache['char-count-value'] = lines_length

    def calc_target_duration(self):
        duration = 1000
        totalLength = sum(self.char_count) - 10 if sum(self.char_count) > 10 else 0
        duration += totalLength * 50
        duration += (len(self.char_count) - 1) * 100 if len(self.char_count) > 0 else 0
        return duration

    def calc_duration(self):
        self.duration = (self.stopTime - self.startTime) if self.stopTime >= self.startTime else (self.startTime - self.stopTime)

    def calc_rs(self):
        duration = int(self.duration) / 1000.0
        target_duration = self.calc_target_duration()
        self.rs = str(round((40 * target_duration / 1000.0 - 20) / float(2 * duration - 1),1)) if duration > 0.5 else "Inf"

    def update_data(self):
        self.calc_char_count()
        self.calc_duration()
        self.calc_rs()

class Subtitles(GObject.GObject):
    __gsignals__ = { 'buffer-changed': (GObject.SIGNAL_RUN_LAST, None, ()) }

    path_lookup = {}
    COL_SUB = 0
    COL_IDX = 1
    COL_SUB_START_TIME = 2
    COL_SUB_STOP_TIME = 3
    COL_SUB_DURATION = 4
    COL_SUB_REFERENCE = 5
    COL_SUB_CHAR_COUNT = 6
    COL_SUB_RS = 7
    COL_SUB_TEXT = 8
    COL_SUB_INFO = 9
    subs = Gtk.ListStore(subRec.__gtype__, str, str, str, str, str, str, str, str, str)
    sub_connections = {}

    def __init__(self):
        super(Subtitles, self).__init__()
        self.__last_edited = None

    @property
    def last_edited(self):
        return self.__last_edited

    @last_edited.setter
    def last_edited(self, value):
        if self.__last_edited is not None and self.__last_edited != value:
            self.__last_edited.info = ('Audio-Last_Edited', '')
        self.__last_edited = value
        self.__last_edited.info = ('Audio-Last_Edited', ('<span foreground="black" background="'+utils.RGB_to_hex((0.6, 0.6, 0.8))+'">Last Edited/Saved</span>', []))

    def get_model(self):
        return self.subs

    def index(self, sub):
        # apo lookup
        res = None
        for i in xrange(len(self.subs)):
            if self.subs[i][self.COL_SUB] == sub:
                res = i
                break
        return res 

    def inside_sub_old(self, msec):
        # allagh me bisect sto search
        tmpSub = None
        for item in self.subs:
            if item[self.COL_SUB].startTime <= msec <= item[self.COL_SUB].stopTime:
                tmpSub = item[self.COL_SUB]
                break
        return tmpSub

    def inside_sub(self, msec):
        idx = utils.bisect(self.subs, lambda x: x[self.COL_SUB].startTime, msec)
        sub = self.subs[idx][self.COL_SUB]
        return sub if sub.startTime <= msec <= sub.stopTime else None

    def get_sub_before_timeStamp(self, timeStamp):
        #bisect
        tmpSub = None
        for item in self.subs:
            if item[self.COL_SUB].startTime < timeStamp:
                tmpSub = item[self.COL_SUB]
            if item[self.COL_SUB].startTime > timeStamp:
                break
        return tmpSub

    def get_sub_after_timeStamp(self, timeStamp):
        #bisect
        tmpSub = None
        for item in self.subs:
            if item[self.COL_SUB].startTime > timeStamp:
                tmpSub = item[self.COL_SUB]
                break
        return tmpSub

    def get_prev(self, sub):
        idx = self.index(sub)
        return self.subs[idx - 1][self.COL_SUB] if (idx != None) and (idx > 0) else None

    def get_next(self, sub):
        idx = self.index(sub)
        return self.subs[idx + 1][self.COL_SUB] if (idx != None) and (idx < len(self.subs) - 1) else None

    def is_empty(self):
        return len(self.subs) == 0

    def clear(self):
        self.subs.clear()
        self.emit('buffer-changed')

    def append(self, sub):
        self.insert_sub(sub)

    def get_sub_from_path(self,path):
        if len(self.subs) == 0:
            return None
        return self.subs[path][self.COL_SUB]

    def get_sub(self, idx):
        if int(idx) > len(self.subs)-1:
            return None
        return self.subs[idx][self.COL_SUB]

    def get_sub_path(self, sub):
        try:
            if self.subs[self.path_lookup[sub]][self.COL_SUB] == sub:
                return self.path_lookup[sub]
        except:
            pass
        res = None
        for i in self.subs:
            if sub == i[self.COL_SUB]:
                res = i
                break;
        if res != None:
            self.path_lookup[sub] = res.path
            return res.path
        else:
            return None

    def insert_sub(self, sub):
        idx = 0
        if (len(self.subs) == 0) or (sub.startTime > self.subs[-1][0].startTime):
            listIter = self.subs.append()
            idx = len(self.subs) - 1
        else:
            for i in xrange(len(self.subs)):
                if sub.startTime < self.subs[i][0].startTime:
                    idx = i
                    break;
            listIter = self.subs.insert(idx)
        self.subs.set_value(listIter, self.COL_SUB, sub)
        self.subs.set_value(listIter, self.COL_IDX, str(idx+1))
        self.subs.set_value(listIter, self.COL_SUB_START_TIME, '<span foreground="#4ccc4ccc4ccc">'+str(sub.startTime)+'</span>')
        self.subs.set_value(listIter, self.COL_SUB_STOP_TIME, '<span foreground="#4ccc4ccc4ccc">'+str(sub.stopTime)+'</span>')
        self.subs.set_value(listIter, self.COL_SUB_DURATION, sub.duration_str)
        self.subs.set_value(listIter, self.COL_SUB_REFERENCE, utils.filter_markup(sub.vo))
        self.subs.set_value(listIter, self.COL_SUB_CHAR_COUNT, sub.char_count_str)
        self.subs.set_value(listIter, self.COL_SUB_RS, sub.rs_str)
        self.subs.set_value(listIter, self.COL_SUB_TEXT, utils.filter_markup(sub.text))
        self.subs.set_value(listIter, self.COL_SUB_INFO, sub.info_audio_str)
        self.sub_connections[sub] = sub.connect('updated', self.on_sub_update)
        if idx != len(self.subs) - 1:
            self.recalc_idx_col()
        self.emit('buffer-changed')

    def recalc_idx_col(self):
        for idx, row in enumerate(self.subs):
            row[self.COL_IDX] = str(idx+1)

    def remove_sub(self, sub):
        for row in self.subs:
            if row[self.COL_SUB] == sub:
                if sub in self.sub_connections.keys():
                    sub.disconnect(self.sub_connections[sub])
                self.subs.remove(row.iter)
                break
        self.recalculate_path_lookup()
        self.recalc_idx_col()
        self.emit('buffer-changed')

    def modify_sub(self, sub, newSub):
        self.subs.remove_sub(sub)
        self.subs.insert_sub(newSub)
        self.emit('buffer-changed')

    def is_changed(self):
        changed = False
        for row in self.subs:
            changed = changed or row[0].is_changed()
        return changed

    def clear_changed(self):
        for row in self.subs:
            row[self.COL_SUB].clear_changed()

    def list_subs_overlapping_window(self, timeLow, timeHigh):
        tl = timeStamp(timeLow)
        th = timeStamp(timeHigh)
        res = []
        for item in self.subs:
            if (tl <= item[self.COL_SUB].startTime <= th) or (tl <= item[self.COL_SUB].stopTime <= th) or ((item[self.COL_SUB].startTime <= tl) and (item[self.COL_SUB].stopTime >= th)):
                res.append(item[self.COL_SUB])
        return res

    def get_time_dict(self):
        tmpDict = {}
        for item in self.subs:
            tmpDict[(item[self.COL_SUB].startTime, item[self.COL_SUB].stopTime)] = ''
        return tmpDict

    def get_last_modified_row(self):
        res = (-1,  0)
        for item in enumerate(self.subs):
            if item[1][self.COL_SUB].modified_timestamp > res[1]:
                res = (item[0]+1, item[1][self.COL_SUB].modified_timestamp)
        return res[0]

    def clear_all_modified(self):
        for item in self.subs:
            item[self.COL_SUB].info = ('Audio-Last_Edited', '')

    def clear_all_modified_timestamps(self):
        for item in self.subs:
            item[0].modified_timestamp = 0

    def load_vo_data(self, voReference):
        for item in self.subs:
            res = voReference.get_subs_in_range(int(item[0].startTime), (item[0].stopTime))
            if res != []:
                item[self.COL_SUB].vo = '\n'.join(voItem[2].strip() for voItem in res)
            else:
                item[self.COL_SUB].vo = ''

    def recalculate_path_lookup(self):
        for i in self.subs:
            self.path_lookup[i[self.COL_SUB]] = i.path

    def calc_hash(self):
        return hash(''.join(row[self.COL_SUB].text for row in self.subs))

    def on_sub_update(self, sub, attr):
        path = self.get_sub_path(sub)
        if attr == 'startTime':
            self.subs[path][self.COL_SUB_START_TIME] = '<span foreground="#4ccc4ccc4ccc">'+str(sub.startTime)+'</span>'
            self.last_edited = sub
        elif attr == 'stopTime':
            self.subs[path][self.COL_SUB_STOP_TIME] = '<span foreground="#4ccc4ccc4ccc">'+str(sub.stopTime)+'</span>'
            self.last_edited = sub
        elif attr == 'duration':
            self.subs[path][self.COL_SUB_DURATION] = sub.duration_str
        elif attr == 'vo':
            self.subs[path][self.COL_SUB_REFERENCE] = utils.filter_markup(sub.vo)
        elif attr == 'char_count':
            self.subs[path][self.COL_SUB_CHAR_COUNT] = sub.char_count_str
        elif attr == 'rs':
            self.subs[path][self.COL_SUB_RS] = sub.rs_str
        elif attr == 'text':
            self.subs[path][self.COL_SUB_TEXT] = utils.filter_markup(sub.text)
            self.last_edited = sub
        elif attr == 'info':
            self.subs[path][self.COL_SUB_INFO] = sub.info_audio_str
