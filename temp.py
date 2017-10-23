# -*- coding: utf-8 -*-
from numpy import array, argmin, argmax
from scipy import signal
import numpy as np
from math import floor, ceil
from matplotlib import pyplot as plt
from subutils import ms2ts
from collections import deque
from random import random

get_random_in_range = lambda a,b: int(a + random() * b)

def open_data(filename):
    with open(filename, 'rb') as f:
        data = f.read()
    return array(map(lambda x: ord(x)-127, data))

def moving_average(ar, n):
    return np.convolve(ar, np.ones((n,))/n, mode='same')

def keep_peaks(ar):
    data = ar - ar.mean()
    data[data < 0] = 0
    return data

def normalize(ar):
    if len(ar) == 0:
        return []
    a = ar - ar.min()
    d = (np.abs(a)).max()
    return a if d == 0 else a / float(d)

def distance(v1, v2):
    tmp = v1 - v2
    return np.sqrt( (tmp**2).sum() )

def normalize_nxn(ar):
    res = ar[:,:]
    for i in xrange(ar.shape[1]):
        res[:, i] = normalize(ar[:, i])
    return res

def normalize_spec(spec):
    return (spec[0], spec[1], normalize_nxn(spec[2]))

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
    # tests
    tests = [ False ] * 5
    tests[0] = grad[gmin_idx] < 0 and grad[gmax_idx] > 0
    tests[1] = abs(grad[gmin_idx]) > grad.mean() + 5 * grad.std()
    tests[2] = abs(grad[gmax_idx]) > grad.mean() + 5 * grad.std()
    tests[3] = ar[poi] < ar.mean() - 1.5 * ar.std()
    tests[4] = abs(gmin_idx - gmax_idx) < 4
    return all(tests)

def stat_test_dbg(lst):
    ar = array(lst)
    grad = np.gradient(ar)
    gmin_idx = argmin(grad)
    gmax_idx = argmax(grad)
    poi = (gmin_idx + gmax_idx) / 2
    # tests
    tests = [ False ] * 5
    tests[0] = grad[gmin_idx] < 0 and grad[gmax_idx] > 0
    tests[1] = abs(grad[gmin_idx]) > grad.mean() + 5 * grad.std()
    tests[2] = abs(grad[gmax_idx]) > grad.mean() + 5 * grad.std()
    tests[3] = ar[poi] < ar.mean() - 1.5 * ar.std()
    tests[4] = abs(gmin_idx - gmax_idx) < 4
    return tests

def gen_match_array(slc, spec, doffset, break_limit):
    res = deque(maxlen = 250)
    offset = doffset - 1 if doffset > 1 else 0
    dropped = 0
    for i in xrange(spec[2].shape[1] - slc.shape[1] - offset):
        res.append( compute_match( slc, spec[2][:, i + offset : i + offset + slc.shape[1] ] ) )
        if i % 250 == 0 and i < 0:
            tst = array(res)
            plt.plot(tst)
            plt.plot([tst.mean()] * len(tst))
            plt.plot([tst.mean() - tst.std()] * len(tst))
            plt.plot([tst.mean() + tst.std()] * len(tst))
            #plt.plot(np.gradient(tst * 40))
            print ms2ts(idx2ms(offset + dropped, spec))
            print tst.mean(), tst.std()
            print stat_test_dbg(tst)
            plt.show()
        dropped += 0 if i < 250 else 1
        if (i % 25 == 0 and i > 100 and stat_test(res)) or (0 < break_limit < i):
            break

    if __name__ == '__main__' and stat_test(res):
        res = array(res)
        plt.plot(res)
        plt.plot([res.mean()] * len(res))
        plt.plot(np.gradient(res))
        plt.show()

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
        slc = normalize_spec(get_spec_slice(start_ms, start_ms + duration + k * 1500, src))[2]
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
    start_ms = _start_ms
    stop_ms = max(_stop_ms, start_ms + 5000)
    #stop_ms = get_min_match_size(src_spec, dst_spec, _start_ms, stop_ms)
    src_spec_slice = normalize_spec(get_spec_slice(start_ms, stop_ms, src_spec))
    res = gen_match_array(src_spec_slice[2], dst_spec, ms2idx(offset, dst_spec), break_limit)
    return None if res is None else ( idx2ms(res, dst_spec), idx2ms(res, dst_spec) + (_stop_ms - _start_ms) )

def get_spect(filename, audio_rate = 8000):
    return signal.spectrogram( open_data(filename), audio_rate, scaling = 'spectrum' )

if __name__ == "__main__":
    from subutils import ts2ms
    # Open data and generate spectrums
    spec1 = get_spect('/home/phantome/tmp/test/src-xsubedit.raw')
    spec2 = get_spect('/home/phantome/tmp/test/dst-xsubedit.raw')
    spec2 = normalize_spec(spec2)

    print 'calc matching'
    #res = match(spec1, spec2, ts2ms('00:11:12,785'), ts2ms('00:12:12,785'))
    res = match(spec1, spec2, 215350, 218307)


    if not (res is None):
        print res, ms2ts(int(res[0])), ms2ts(int(res[1]))
