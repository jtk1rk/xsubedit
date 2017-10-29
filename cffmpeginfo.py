import subprocess, locale

class cffmpeginfo(object):
    def __init__(self, cmd, string_match):
        super(cffmpeginfo, self).__init__()
        self.exec_cmd = cmd
        self.string_match = string_match
        self.result = []

    def run(self):
        pipe = subprocess.Popen(self.exec_cmd.encode(locale.getpreferredencoding()), shell = True, stdout=subprocess.PIPE, stderr = subprocess.STDOUT, universal_newlines = True)
        line = ""
        while not (line == "" and pipe.poll() != None) :
            line = pipe.stdout.readline().strip()
            self.parse(line)

    def parse(self, line):
        if all([i in line for i in self.string_match]):
            self.result.append(line)
