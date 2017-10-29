from numpy import exp
from math import floor, ceil
from utils import StretchableList

iround = lambda x: int(round(x))

class Audio(object):
    data = []
    cache = (0,0,0,[])
    maxv = 0

    def __init__(self, hiAudio, lowAudio):
        if len(hiAudio) == 0 or len(lowAudio) == 0:
            return
        self.__hiData = hiAudio
        self.__lowData = lowAudio
        self.width = 100
        self.hiData = self.__hiData.copy()
        self.lowData = self.__lowData.copy()
        self.dataSize = len(self.hiData)

    def set_scale(self, type, value):
        if type == 'linear':
            self.hiData = self.__hiData * value
            self.hiData[self.hiData > 1] = 1
            self.lowData = self.__lowData * value
            self.lowData[self.lowData > 1] = 1
            self.cache = (0,0,0,[])
        if type == 'logarithmic':
            for i in xrange(10):
                self.hiData[i] = 0
            self.hiData = exp(self.__hiData * value)
            self.hiData = self.hiData / max(self.hiData)
            for i in xrange(10):
                self.lowData[i] = 0
            self.lowData = exp(self.__lowData * value)
            self.lowData = self.lowData / max(self.lowData)
            self.cache = (0,0,0,[])

    def set_width(self, width):
        self.width = width

    def get_width(self):
        return self.width

    def get_data(self, lower, upper):
        if self.width == 0:
            return
        VSS_DIFF = 0.5
        if (lower, upper, self.width) == self.cache[:3]:
            return self.cache[3]
        res = []
        lowerIDX = lower * self.dataSize + VSS_DIFF
        upperIDX = upper * self.dataSize + VSS_DIFF
        spp = float(upperIDX - lowerIDX) / self.width
        for i in xrange(iround(self.width)):
            lidx = int(floor(lowerIDX + (i - 0.5 ) * spp))
            hidx = int(ceil(lowerIDX + (i + 0.5) * spp))
            lidx = lidx if lidx > 0 else 0
            hidx = hidx if hidx < len(self.hiData) else len(self.hiData)

            hiPeak = self.hiData[lidx : hidx]
            lowPeak = self.lowData[lidx : hidx]
            hiPeak = hiPeak.mean() if len(hiPeak) > 0 else 0
            lowPeak = lowPeak.mean() if len(lowPeak) > 0 else 0

            res.append((hiPeak, lowPeak))
        self.cache = (lower, upper, self.width, res)
        return res
