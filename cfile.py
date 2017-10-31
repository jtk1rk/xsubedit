from os.path import exists as fileExists, join, split, normpath, splitext, abspath as absolutepath, relpath as relativepath
from os import stat, remove, rename
from shutil import copy as copyfile
import platform

#DIR_DELIMITER = '/' if platform.system() == 'Linux' else '\\'

def get_rel_path(refpath, filename):
    tmpstr = ''
    if filename == '':
        return ''
    if platform.system() == 'Windows' and filename[1] != ':':
        tmpstr = absolutepath(filename)
        tmpstr = tmpstr[:2]
    return join(relativepath(split(tmpstr+filename)[0], tmpstr+refpath), split(tmpstr+filename)[1])

class cfile:

    def __init__(self, filename, refpath = ''):
        self._full_path = filename.decode('utf-8')
        self._path, self._filename = split(self._full_path)
        self._base, self._ext = splitext(self._filename)
        self._ref_path = normpath(refpath.decode('utf-8'))

    # Path and name properties

    @property
    def abspath(self):
        if self._path != '' and self._path[0] == '.' and self._ref_path != '':
            return join(normpath(self._ref_path), normpath(self._path) if self._path != '.' else '')
        return self._path

    @property
    def ext(self):
        return self._ext

    @property
    def base(self):
        return self._base

    @property
    def filename(self):
        return self.base + self.ext

    @property
    def full_path(self):
        if self.filename == '':
            return ''
        if normpath(self.abspath) == '.':
            return self.filename
        return join(self.abspath, self.filename) if self.filename != '' else ''

    # relative path

    @property
    def relpath(self):
        if self.abspath == '' or normpath(self._ref_path) == normpath(self.abspath) :
            return ''
        elif self.abspath[0] == '.':
            return self.abspath
        return normpath(get_rel_path(self._ref_path, self.abspath))

    @property
    def relfull(self):
        return join(normpath(self.relpath), self.filename) if self.filename != '' else ''

    # File entity properties

    @property
    def exists(self):
        return fileExists(self.full_path)

    @property
    def size(self):
        return stat(self.full_path).st_size

    @property
    def isEmpty(self):
        return self.size == 0

    # Methods

    def rename(self, newName):
        os.rename(self.full_path, join(self.path, newName))

    def delete(self):
        os.remove(self.full_path)

    def copy(self, newFile):
        copyfile(self.full_path, newFile)

    def read_data(self):
        # Usually virtual
        with open(self.full_path, 'r') as f:
            res = f.read()
        return res

    def write_data(self, data):
        # virtual
        pass

    def change_ext(self, newExt):
        self._ext = newExt

    def change_base(self, newBase):
        self._base = newBase