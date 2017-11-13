from bisect import bisect_right
from subfile import srtFile
from subtitles import subRec

class cVOReference(object):
    def __init__(self):
        self.filename = ''
        self.start_data = []
        self.stop_data = []
        self.text_data = []

    def set_data(self, value):
        tmpData = []
        for sub in value:
            tmpData.append((sub.startTime, sub.stopTime, sub.text))
        tmpData.sort(key=lambda tup: tup[0])
        self.start_data, self.stop_data, self.text_data = zip(*tmpData)
        self.start_data = list(self.start_data)
        self.stop_data = list(self.stop_data)
        self.text_data = list(self.text_data)

    def get_subs_in_range(self, lowms, highms):
        res = []
        low_idx = bisect_right(self.stop_data, lowms)
        for i in range(low_idx, len(self.start_data)):
            if self.start_data[i] <= highms:
                res.append((self.start_data[i], self.stop_data[i], self.text_data[i]))
            else:
                break
        return res

    def get_indexes_in_range(self, lowms, highms):
        res = []
        low_idx = bisect_right(self.stop_data, lowms)
        for i in range(low_idx, len(self.start_data)):
            if self.start_data[i] <= highms:
                res.append(i)
            else:
                break
        return res

    def get_line(self, idx):
        return [idx, self.start_data[idx], self.stop_data[idx], self.text_data[idx]]

    def save(self):
        if self.filename == '':
            return
        subList = [subRec(self.start_data[i].msec, self.stop_data[i].msec, self.text_data[i]) for i in range(len(self.text_data))]
        f = srtFile(self.filename)
        f.write_to_file(subList)
