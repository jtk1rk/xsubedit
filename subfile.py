from subtitles import subRec
from utils import UTF8_BOM
import chardet
import re

class srtFile:
    def __init__(self, fileName):
        self.fileName = fileName
        self.timeLine = re.compile("[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}")
        self.digitLine = re.compile("[0-9]+")

    def encoding_detection(self, data):
        if self.file_has_BOM():
            return 'UTF-8'
        encoding = {}
        for line in data:
            if len(self.digitLine.findall(line)) > 0 or len(self.timeLine.findall(line)) > 0:
                continue
            line_encoding = chardet.detect(line)['encoding']
            encoding[line_encoding] = 1 if line_encoding not in encoding.keys() else encoding[line_encoding] + 1
        encoding.pop('ascii', None)
        if len(encoding) == 0:
            return 'ascii'
        else:
            return max(encoding, key=encoding.get)

    def file_has_BOM(self):
        has_BOM = False
        with open(self.fileName.decode('utf-8'), 'rb') as f:
            has_BOM = f.read(3) == '\xef\xbb\xbf'
        return has_BOM

    def convert_to_utf8(self, data, encoding):
        tmp = []
        for line in data:
            tmp.append(line.decode(encoding).encode('utf-8'))
        return tmp

    def write_to_file(self, subs, encoding = 'Windows-1253'):
        f = open(self.fileName.decode('utf-8'), "w")
        if encoding == 'UTF-8 BOM':
            f.write(UTF8_BOM)
        for i in enumerate(subs):
            f.write(str(i[0]+1) + '\n')
            lines = str(i[1][0]).splitlines()
            for line in lines:
                if encoding == 'Windows-1253':
                    f.write(line.decode('utf-8').encode(encoding = 'Windows-1253', errors = 'ignore') + '\n')
                elif encoding == 'UTF-8 BOM':
                    f.write(line + '\n')
            f.write('\n')
        f.close()

    def read_from_file(self):
        f = open(self.fileName.decode('utf-8'), "r")
        data = f.readlines()
        f.close()

        encoding = self.encoding_detection(data)
        if not ('UTF' in encoding.upper() or 'ASCII' in encoding.upper()):
            data = self.convert_to_utf8(data, 'windows-1253')

        subs = []
        state = [0,"",[]]
        stateIdx = 0
        for line in data:
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
            if stateIdx == 2 and (line.strip() == "" or line == data[-1]):
                timeCode = state[1].split(" --> ")
                text = ""
                for item in state[2]:
                    text += item + '\n'
                text = text[:-1]
                subs.append(subRec(timeCode[0], timeCode[1], text.decode("utf-8", "ignore")))
                state = [0, "", []]
                stateIdx = 0
        return subs
