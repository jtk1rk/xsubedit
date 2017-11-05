import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk
from os.path import exists, split
import pickle
import platform
import time
import itertools
from mparser import MarkupParser, Tag
from mgen import MarkupGenerator
from os import popen

RUN_TIMESTAMP = time.time()
UTF8_BOM = '\xef\xbb\xbf'

iround = lambda x: int(round(x))

def common_part(str1, str2):
    res = ''
    minstr = srt1 if len(str1) < len(str2) else str2
    for i in xrange(len(minstr)):
        if str1[i] != str2[i]:
            break
        res += minstr[i]
    return res

class StretchableList(list):
    def stretch(self, newlen):
        old = [ (i * (newlen-1), self[i]) for i in range(len(self)) ]
        new = [ i * (len(self)-1) for i in range(newlen) ]
        self[:] = []
        for n in new:
            while len(old) > 1 and n >= old[1][0]:
                old.pop(0)
            if old[0][0] == n:
                self.append(old[0][1])
            else:
                self.append( old[0][1] + \
                             float((n-old[0][0]))/(old[1][0]-old[0][0]) * \
                             (old[1][1]-old[0][1]) )
        return self

class brList(list):
    def append(self, index, item):
        if index < len(self):
            self[:] = self[:index]
        super(brList, self).append(item)

class cPreferences:
    def __init__(self,  filename):
        self.filename = filename.decode('utf-8')
        self.data =  {'Encoding': 'Windows-1253', 'Incremental_Backups': True, 'Autosave': True}

    def load(self):
        try:
            if exists(self.filename):
                self.data = pickle.load( open(self.filename,  'rb') )
        except:
            pass

    def save(self):
        try:
            pickle.dump( self.data,  open(self.filename,  'wb'), protocol = pickle.HIGHEST_PROTOCOL )
        except:
            pass

    def keys(self):
        return self.data.keys()

    def get_data(self):
        return self.data.copy()

    def set_data(self,  prefs):
        self.data = prefs.copy()

    def update_mru(self, value):
        if not 'MRU' in self.data.keys():
            self.data['MRU'] = [value]
        else:
            tmpValue = None
            for item in self.data['MRU']:
                if split(item)[1] == split(value)[1]:
                    tmpValue = item
                    break
            if tmpValue:
                self.data['MRU'].remove(tmpValue)
            self.data['MRU'] = [value] + self.data['MRU']
            try:
                self.data['MRU'] = [ item.decode('utf-8') for idx, item in enumerate(self.data['MRU']) if exists(item.decode('utf-8')) and (idx<10) ]
            except:
                pass

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self,  key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

def RGB_to_hex(rgb):
    return Gdk.Color(rgb[0]*65535, rgb[1]*65535, rgb[2]*65535).to_string()

def calc_info_color(value):
    """ Calculate subtitle score color
        Compatible with VSS """
    if value == 'Inf':
        return ('TOO FAST!', RGB_to_hex((1,  0.6, 0.6)))
    if float(value) >= 35:
        return ('TOO FAST!', RGB_to_hex((1,  0.6, 0.6)))
    elif 31 <= float(value) < 35:
        return ('Fast, Acceptable.', RGB_to_hex((1, 0.8, 0.6)))
    elif 27 <= float(value) < 31:
        return ('A bit fast.', RGB_to_hex((1, 1, 0.6)))
    elif 23 <= float(value) < 27:
        return ('Good.', RGB_to_hex((0.8, 1, 0.6)))
    elif 15 <= float(value) < 23:
        return ('Perfect.', RGB_to_hex((0.6, 1, 0.6)))
    elif 13 <= float(value) < 15:
        return ('Good.', RGB_to_hex((0.6, 1, 0.8)))
    elif 10 <= float(value) < 13:
        return ('A bit slow.', RGB_to_hex((0.6,  1,  1)))
    elif 5 <= float(value) < 10:
        return ('Slow, Acceptable.', RGB_to_hex((0.6, 0.8, 1)))
    elif float(value) < 5:
        return ('TOO SLOW!', RGB_to_hex((0.6, 0.6, 1)))

def set_process_name():
    import random
    import string
    from ctpyes import cdll, create_string_buffer, byref
    """ This works only in Linux.
        I would avoid using it because it depends on an external library (libc.so.6),
        but I do not know any other way (without external depedencies) to change
        the name of the process. """
    if platform.system() != 'Linux':
        return
    rndext = ''.join(random.choice(string.ascii_lowercase) for i in xrange(5))
    name = 'xSubEdit-' + rndext
    libc = cdll.LoadLibrary('/lib/libc.so.6')
    buff = create_string_buffer(len(name) + 1)
    buff.value = name
    libc.prctl(15, byref(buff), 0, 0, 0)

def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

def triplewise(iterable):
    a, b, c = itertools.tee(iterable, 3)
    next(b, None)
    next(c, None)
    next(c, None)
    return itertools.izip(a, b, c)

def isfloat(item):
    try:
        float(item)
        return True
    except ValueError:
        return False

def isint(item):
    try:
        int(item)
        if int(item) == float(item):
            return True
        else:
            return False
    except ValueError:
        return False

def isNumber(item):
    return isfloat(item) or isint(item)

def find_all_str(s, substring):
    """Finds all occurences of a substring in a string
       and returns the result as a list of tuples (begin, end)"""
    res = []
    pos = s.find(substring)
    while pos >= 0:
       res.append((pos, pos + len(substring)))
       pos = s.find(substring, res[-1][1])
    return res

def do_all(f, iterable):
    for item in iterable:
        f(item)

def grad(A0, B0, A, B, x):
    if A0 == B0:
        raise ValueError('ValueError: Division By Zero')
    return ( (A - B) / float(A0 - B0) ) * (x - B0) + B

def bisect(clist, key, value):
    """ Example: bisect(objectlist, lambda x: x.value, value) """
    a = 0
    b = len(clist) - 1
    c = (a+b) // 2
    while b-a > 1:
        if value > key(clist[c]):
            a = c
        else:
            b = c
        c = (a+b) // 2
    return b if (key(clist[b]) <= value) else a

def filter_markup(text):
    m = MarkupParser(text)
    keeptags = []
    for tag in m.tags:
        if tag.name.upper() in ['B', 'I']:
            keeptags.append(tag)
        if tag.name.upper() == 'FONT' and 'COLOR' in [attr.upper() for attr in tag.attributes]:
            keeptags.append(Tag('span', tag.start, tag.stop, {'foreground': tag.attributes['color']}))
    g = MarkupGenerator(m.text, keeptags)
    return g.markup

def untagged_text(text):
    try:
        m = MarkupParser(text)
    except:
        return text
    return m.text

def mediaDur(filename):
    if platform.system() == 'Windows':
        exec_cmd = 'mediainfo --Inform="Video;%%Duration%%" "%s"' % filename.decode('utf-8').encode('cp1253')
    else:
        exec_cmd = 'mediainfo --Inform="Video;%%Duration%%" "%s"' % filename
    output = popen(exec_cmd).read().strip()
    return float(output) if isNumber(output) else None

def mean(arr):
    if len(arr) == 0:
        raise ValueError('Cannot calculate the mean value of an empty array.')
    return sum(arr) / len(arr)
