from numpy import exp

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

class Audio(object):
    data = []
    width = 100
    cache = (0,0,0,[])
    maxv = 0

    def __init__(self, hiAudio, lowAudio):
        if len(hiAudio) == 0 or len(lowAudio) == 0:
            return
        self.__hiData = hiAudio
        self.__lowData = lowAudio
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
            if self.width <= upperIDX - lowerIDX:
                for i in xrange(self.width):
                    hiPeak = self.hiData[round(lowerIDX + i * spp) : round(lowerIDX + (i+1) * spp)].max()
                    lowPeak = self.lowData[round(lowerIDX + i * spp) : round(lowerIDX + (i+1) * spp)].max()
                    res.append((hiPeak, lowPeak))
            else:
                r = self.width / float(upperIDX - lowerIDX)
                for i in xrange(self.width):
                    if round(lowerIDX + i /r) >= len(self.hiData):
                        continue
                    res.append( ( self.hiData[round(lowerIDX + i / r)], self.lowData[round(lowerIDX + i / r)] ) )
            self.cache = (lower, upper, self.width, res)
            return res

