from numpy import exp, hstack
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
        self.hiData = hstack(([0] * 4, self.hiData))
        self.lowData = hstack(([0] * 4, self.lowData))
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
        if lower == self.cache[0] and upper == self.cache[1] and self.width == self.cache[2]:
            return self.cache[3]
        else:
            res = []
            lowerIDX = lower * self.dataSize
            upperIDX = upper * self.dataSize
            spp = float(upperIDX - lowerIDX) / self.width
            if iround(self.width) <= upperIDX - lowerIDX:
                for i in xrange(iround(self.width)):
                    idx = lowerIDX + i * spp
                    if iround(idx) > self.dataSize:
                        continue
                    hiPeak = self.hiData[iround(idx) : iround(idx + spp) ].max()
                    lowPeak = self.lowData[iround(idx) : iround(idx + spp) ].max()
                    res.append((hiPeak, lowPeak))
            else:
                r = self.width / float(upperIDX - lowerIDX)
                for i in xrange(self.width):
                    if iround(lowerIDX + i /r) >= len(self.hiData):
                        continue
                    res.append( ( self.hiData[iround(lowerIDX + i / r)], self.lowData[iround(lowerIDX + i / r)] ) )
            self.cache = (lower, upper, self.width, res)
            return res
