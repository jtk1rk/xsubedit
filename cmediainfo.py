from os import popen
import platform

class cMediaInfo:
    def __init__(self, filename):
        if platform.system() == 'Windows':
            self.exec_cmd1 = 'mediainfo "%s"' % filename#.decode('utf-8').encode('cp1253')
            self.exec_cmd2 = 'mediainfo --Inform="Audio;%%CodecID%%" "%s"' % filename#.decode('utf-8').encode('cp1253')
        else:
            self.exec_cmd1 = 'mediainfo "%s"' % filename
            self.exec_cmd2 = 'mediainfo --Inform="Audio;%%CodecID%%" "%s"' % filename
        self.packed = False
        self.audio_codec = None

    def run(self):
        output = popen(self.exec_cmd1).read()
        if 'Packed bitstream' in output:
            self.packed = True
        output = popen(self.exec_cmd2).read()
        self.audio_codec = output.strip()
