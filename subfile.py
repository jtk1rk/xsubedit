from subtitles import subRec
import chardet
import re

class srtFile:
    def __init__(self, fileName):
        self.fileName = fileName
        self.timeLine = re.compile("[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}")
        self.digitLine = re.compile("[0-9]+")

    def encoding_detection(self, data):
        encoding = chardet.detect(data)
        encoding.pop('ascii', None)
        if len(encoding) == 0:
            return 'ascii'
        else:
            return encoding['encoding'] if encoding['encoding'] != 'ISO-8859-7' else 'Windows-1253'

    def write_to_file(self, subs, encoding = 'Windows-1253'):
        f = open(self.fileName, "w", encoding = encoding, errors = 'ignore')
        for i in enumerate(subs):
            f.write(str(i[0]+1) + '\r\n')
            lines = str(i[1]).splitlines()
            for line in lines:
                f.write(line + '\r\n')
            f.write('\r\n')
        f.close()

    def read_from_file(self):
        f = open(self.fileName, "rb")
        _data = f.read()
        f.close()

        encoding = self.encoding_detection(_data)
        f = open(self.fileName, "r", encoding=encoding, errors = 'ignore')
        data = f.readlines()
        f.close()

        subs = []
        state = [0,"",[]]
        stateIdx = 0

        for idx, line in enumerate(data):
            if stateIdx == 0 and len(self.digitLine.findall(line)) > 0:
                state[0] = line.strip()
                stateIdx = 1
                continue
            if stateIdx == 1 and len(self.timeLine.findall(line)) > 0:
                state[1] = line.strip()
                stateIdx = 2
                continue
            if stateIdx == 2 and line.strip() != "":
                state[2].append(line.strip())
            if stateIdx == 2 and (line.strip() == "" or idx == len(data)-1):
                timeCode = state[1].split(" --> ")
                text = ""
                for item in state[2]:
                    text += item + '\n'
                text = text[:-1]
                subs.append(subRec(timeCode[0], timeCode[1], text))
                state = [0, "", []]
                stateIdx = 0

        return subs

def gen_timestamp_srt_from_source(source, destination):
    src = srtFile(source)
    dst = srtFile(destination)
    subs = src.read_from_file()
    for sub in subs:
        sub.text = ''
    dst.write_to_file(subs)
