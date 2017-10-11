# -*- coding: utf-8 -*-
from numpy import array, argmin
from scipy import signal
import numpy as np
from math import floor, ceil

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
    d = (np.abs(ar)).max()
    if d == 0:
        return ar
    return ar / float(d)

def distance(v1, v2):
    tmp = v1 - v2
    return np.sqrt( (tmp**2).sum() )

def normalize_nxn(ar):
    res = ar[:,:]
    for i in xrange(ar.shape[1]):
        res[:, i] = keep_peaks(normalize(moving_average(ar[:, i],3)))
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

def stat_test(minimum, std, mean):
    return abs(minimum - mean) / std > 5

def gen_match_array(slc, spec):
    res = []
    for i in xrange(spec[2].shape[1] - slc.shape[1]):
        if i % 200 == 0 and i > 0:
            tmp = array(res)
            if stat_test(tmp.min(), tmp.std(), tmp.mean()):
                return tmp
            print '%d out of %d' % (i, spec[2].shape[1] - slc.shape[1])
        res.append( compute_match( slc, spec[2][:, i : i + slc.shape[1] ] ) )
    return array(res)

def get_spec_slice(start_msec, stop_msec, spec):
    start_sec = start_msec / 1000.0
    stop_sec = stop_msec / 1000.0
    td = spec[1][1] - spec[1][0]
    low = int(floor(start_sec / float(td)))
    high = int(ceil(stop_sec / float(td)))
    return (spec[0], spec[1][low:high], spec[2][:, low:high])

def match(src_spec, dst_spec, start_ms, stop_ms):
    src_spec_slice = normalize_spec(get_spec_slice(start_ms, stop_ms, src_spec))
    dist = gen_match_array(src_spec_slice[2], dst_spec)
    if stat_test(dist.min(), dist.std(), dist.mean()):
        td = (dst_spec[1][1] - dst_spec[1][0])
        return (td * argmin(dist), td * (argmin(dist)+src_spec_slice[2].shape[1]))

def get_spect(filename):
    return signal.spectrogram( open_data(filename), 8000, scaling = 'spectrum' )

if __name__ == "__main__":
    # Open data and generate spectrums
    print "reading spec1"
    spec1 = get_spect('g.raw')
    print "reading spec2"
    spec2 = get_spect('G.raw')

    print 'Normalizing spec2'
    spec2 = normalize_spec(spec2)
    print 'calc matching'
    print match(spec1, spec2, 21500, 22500)

