#!/usr/bin/python
# -*- coding: UTF-8 -*-

def ts2ms(ts):
# converts  hh:mm:ss,msc (msc=miliseconds) to miliseconds
    tmp = int(ts[9:12])
    tmp += int(ts[6:8])*1000
    tmp += int(ts[3:5])*60*1000
    tmp += int(ts[:2])*60*60*1000
    return tmp

def ms2ts(ms):
# converts miliseconds to hh:mm:ss,msc (msc=miliseconds)
    tsec = int(ms / 1000)
    hh = tsec / 3600
    mm = (tsec - hh * 3600) / 60
    ss = (tsec - hh * 3600 - mm * 60)
    mil= ms - tsec * 1000
    tmp = str(hh).zfill(2)+":"+str(mm).zfill(2)+":"+str(ss).zfill(2)+","+str(mil).zfill(3)
    return tmp

def duration(start, end):
    return ts2ms(end)-ts2ms(start)

def is_timestamp(string):
    if len(string) != 12:
        return False
    try:
        a = int(string[0:2])
        b = int(string[3:5])
        c = int(string[6:8])
        d = int(string[9:12])
    except:
        return False
    if b > 60 or c > 60:
        return False
    return True

def ts_greater(a, b):
    return ts2ms(a) > ts2ms(b)