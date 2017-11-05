# -*- coding: utf-8 -*-
from numpy import array, argmin, argmax
from scipy import signal
import numpy as np
from math import floor, ceil
#from matplotlib import pyplot as plt
from subutils import ms2ts
from collections import deque
from random import random
import pickle

get_random_in_range = lambda a,b: int(a + random() * b)
iround = lambda v: int(round(v))

def open_data(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    return array(map(lambda x: ord(x)-127, data))

def moving_average(ar, n):
    return np.convolve(ar, np.ones((n,))/n, mode='same')

# Spectral Functions

def distance(v1, v2):
    tmp = v1 - v2
    return np.sqrt( (tmp**2).mean() )

def compute_match(fs1, fs2):
    match = []
    n = fs1.shape[1]
    if fs1.shape[1] != fs2.shape[1]:
        return -1
    for i in xrange(n):
        match.append(distance(fs1[:, i], fs2[:, i]))
    return sum(match)

def stat_test(lst):
    ar = array(lst)
    grad = np.gradient(ar)
    gmin_idx = argmin(grad)
    gmax_idx = argmax(grad)
    poi = (gmin_idx + gmax_idx) / 2
    # fast tests
    tests = [ False ] * 6
    tests[0] = grad[gmin_idx] < 0
    tests[1] = grad[gmax_idx] > 0
    tests[2] = abs(grad[gmin_idx] - grad[gmax_idx]) > grad.mean() + 10 * grad.std()
    tests[3] = abs(grad[gmin_idx] - grad[gmax_idx]) > 10
    tests[4] = ar[poi] < ar.mean() - 2 * ar.std()
    tests[5] = abs(gmin_idx - gmax_idx) < 4

    return all(tests)

def gen_match_array(slc, spec, doffset, break_limit):
    res = deque(maxlen = 250)
    offset = doffset - 1 if doffset > 1 else 0
    dropped = 0
    for i in xrange(spec[2].shape[1] - slc.shape[1] - offset):
        res.append( compute_match( slc, spec[2][:, i + offset : i + offset + slc.shape[1] ] ) )
        if i % 250 == 0 and i > 0 and __name__ == '__main__' and False:
            tst = array(res)
            #plt.plot(tst)
            #plt.plot([tst.mean()] * len(tst))
            #plt.plot([tst.mean() - tst.std()] * len(tst))
            #plt.plot([tst.mean() + tst.std()] * len(tst))
            #plt.plot(np.gradient(tst))
            #print ms2ts(idx2ms(offset + dropped, spec))
            #plt.show()
        dropped += 0 if i < 250 else 1
        if (i % 25 == 0 and i > 100 and stat_test(res)) or (0 < break_limit < i):
            break

    if __name__ == '__main__' and stat_test(res):
        res = array(res)
#        plt.plot(res)
#        plt.plot([res.mean()] * len(res))
#        plt.plot(np.gradient(res))
        grad = np.gradient(res)
        gmin_idx = argmin(grad)
        gmax_idx = argmax(grad)
        print abs(grad[gmin_idx] - grad[gmax_idx]), grad.mean(), grad.std()
#        plt.show()

    res = array(res)
    grad = np.gradient(res)
    return None if not stat_test(res) else ((argmin(grad) + argmax(grad)) / 2) + offset + dropped

def hundred_sum(slc, dst, offset):
    res = []
    for i in xrange(100):
        res.append( compute_match( slc, dst[2][:, i + offset : i + offset + slc.shape[1] ]) )
    return res

def get_mean_sum_value(slc, dst):
    ridx = [ get_random_in_range(0, dst[2].shape[1] - slc.shape[1]) for i in xrange(3) ]
    res = []
    for offset in ridx:
        res.append(hundred_sum(slc, dst, offset))
    return array(res).mean()

def get_min_match_size(src, dst, start_ms, stop_ms):
    duration = stop_ms - start_ms
    for k in xrange(5):
        slc = get_spec_slice(start_ms, start_ms + duration + k * 1500, src)[2]
        res = get_mean_sum_value(slc, dst)
        if res >= 180:
            return start_ms + duration + k * 1500
    return start_ms + duration + 1500 * 7

def get_last_msec(spec):
    return spec[1][-1] * 1000

def get_spec_slice(start_msec, stop_msec, spec):
    start_sec = start_msec / 1000.0
    stop_sec = stop_msec / 1000.0
    td = spec[1][1] - spec[1][0]
    low = int(floor(start_sec / float(td)))
    high = int(ceil(stop_sec / float(td)))
    return (spec[0], spec[1][low:high], spec[2][:, low:high])

def idx2ms(offset, spec):
    td = (spec[1][1] - spec[1][0])
    return td * offset * 1000

def ms2idx(ms, spec):
    td = spec[1][1] - spec[1][0]
    return int(floor(ms / (td * 1000.0)))

def match(src_spec, dst_spec, _start_ms, _stop_ms, offset = 0, break_limit = -1):
    print "match(src, dst, start_ms=%s, stop_ms=%s, offset=%s)" % ( ms2ts(_start_ms), ms2ts(_stop_ms), ms2ts(offset) )
    start_ms = _start_ms
    stop_ms = max(_stop_ms, start_ms + 8000)
    src_spec_slice = get_spec_slice(start_ms, stop_ms, src_spec)
    _break_limit = -1 if break_limit == -1 else round(int(break_limit / 28.0))
    _break_limit = 250 if 1 < break_limit < 250 else _break_limit
    res = gen_match_array(src_spec_slice[2], dst_spec, ms2idx(offset, dst_spec), _break_limit)
    return None if res is None else ( idx2ms(res, dst_spec), idx2ms(res, dst_spec) + (_stop_ms - _start_ms) )

def get_spect(data, audio_rate = 8000):
    return signal.spectrogram( data, audio_rate, scaling = 'spectrum' )

def get_spect_from_file(filename, audio_rate = 8000):
    return signal.spectrogram( open_data(filename), audio_rate, scaling = 'spectrum' )

def normalize_spec(spec):
    spec_data = spec[2] - spec[2].mean()
    spec_data /= spec_data.std()
    return (spec[0], spec[1], spec_data)

def t_slice(arr, startms, stopms):
    startidx = iround(startms / 8.0)
    stopidx = iround(stopms / 8.0)
    return arr[startidx:stopidx]

if __name__ == "__main__":
    from subutils import ts2ms

    src_data = open_data('/home/phantome/tmp2/src-xsubedit.raw')
    dst_data = open_data('/home/phantome/tmp2/dst-xsubedit.raw')
    #spec1 = normalize_spec(get_spect(src_data))
    #spec2 = normalize_spec(get_spect(dst_data))

    #print 'calc matching'
    #res = match(spec1, spec2, ts2ms('00:10:20,005'), ts2ms('00:10:22,743'), ts2ms('00:09:00,000'))
    print CDM(t_slice(src_data, ts2ms('00:10:20,005'), ts2ms('00:10:22,743')), t_slice(dst_data, ts2ms('00:12:24,372'), ts2ms('00:12:27,110')))

    #if not (res is None):
    #    print res, ms2ts(int(res[0])), ms2ts(int(res[1]))
