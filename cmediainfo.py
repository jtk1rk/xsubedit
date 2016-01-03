from os import popen
import platform

class cMediaInfo:
    def __init__(self, filename):
        if platform.system() == 'Windows':
            self.exec_cmd = 'mediainfo\mediainfo "' + filename.decode('utf-8').encode('cp1253') +'"'
        else:
            self.exec_cmd = 'mediainfo "' + filename + '"'
        self.packed = False

    def run(self):
        output = popen(self.exec_cmd).read()
        if 'Packed bitstream' in output:
            self.packed = True

