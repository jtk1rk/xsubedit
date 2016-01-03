from bisect import bisect_right

class cVOReference(object):
    def __init__(self):
        self.start_data = []
        self.stop_data = []
        self.text_data = []

    def set_data(self, value):
        tmpData = []
        for sub in value:
            tmpData.append((sub.startTime, sub.stopTime, sub.text))
        tmpData.sort(key=lambda tup: tup[0])
        self.start_data, self.stop_data, self.text_data = zip(*tmpData)

    def get_subs_in_range(self, lowms, highms):
        res = []
        low_idx = bisect_right(self.stop_data, lowms)
        for i in xrange(low_idx, len(self.start_data)):
            if self.start_data[i] <= highms:
                res.append((self.start_data[i], self.stop_data[i], self.text_data[i]))
            else:
                break
        return res
