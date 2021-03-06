from os.path import exists as fileExists, join, split, normpath, splitext, abspath as absolutepath, relpath as relativepath, isdir
from os import stat, remove, rename, makedirs
from shutil import copy as copyfile
import platform
import hashlib

def generate_file_md5(filename, blocksize=2**20):
    m = hashlib.md5()
    with open( filename , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()

def get_rel_path(refpath, filename):
    tmpstr = ''
    if filename == '':
        return ''
    if platform.system() == 'Windows' and filename[1] != ':':
        tmpstr = absolutepath(filename)
        tmpstr = tmpstr[:2]
    return join(relativepath(split(tmpstr+filename)[0], tmpstr+refpath), split(tmpstr+filename)[1])

class cfile:

    def __init__(self, _file, refpath = ''):
        if isinstance(_file, cfile):
            self._full_path = _file._full_path
            self._path = _file._path
            self._filename = _file._filename
            self._base = _file._base
            self._ext = _file._ext
            self._ref_path = _file._ref_path
        else:
            self._full_path = _file
            self._path, self._filename = split(self._full_path)
            self._base, self._ext = splitext(self._filename)
            self._ref_path = normpath(refpath)

    # Path and name properties

    @property
    def abspath(self):
        if self._path != '' and self._path[0] == '.' and self._ref_path != '':
            return join(normpath(self._ref_path), normpath(self._path) if self._path != '.' else '')
        return self._path

    @property
    def ext(self):
        return self._ext.replace('.','')

    @property
    def base(self):
        return self._base

    @property
    def filename(self):
        if self.base == '':
            return ''
        return '.'.join([self.base, self.ext]) if self.ext != '' else self.base

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
        if self.filename == '':
            return False
        return fileExists(self.full_path)

    @property
    def path_exists(self):
        return isdir(self.abspath)

    @property
    def size(self):
        return stat(self.full_path).st_size

    @property
    def isEmpty(self):
        return self.size == 0

    @property
    def md5(self):
        return generate_file_md5(self.full_path)

    # Methods

    def __eq__(self, other):
        return self.full_path == other.full_path

    def __str__(self):
        return self.full_path

    def add_subdir(self, subdir):
        self._path = join(self._path, subdir)

    def obj_copy(self):
        return cfile(self._full_path, refpath = self._ref_path)

    def create_path(self):
        try:
            makedirs(self._path)
        except OSError as e:
            print(e)

    def rename(self, newName):
        rename(self.full_path, join(self.path, newName))

    def delete(self):
        remove(self.full_path)

    def copy(self, newFile):
        if isinstance(newFile, cfile):
            copyfile(self.full_path, newFile.full_path)
        else:
            copyfile(self.full_path, newFile)

    def read_data(self):
        # Usually virtual
        with open(self.full_path, 'r') as f:
            res = f.read()
        return res

    def touch(self):
        f = open(self.full_path, 'w')
        f.close()

    def write_data(self, data):
        # virtual
        pass

    def change_ext(self, newExt):
        self._ext = newExt.replace('.','')

    def change_base(self, newBase):
        self._base = newBase
