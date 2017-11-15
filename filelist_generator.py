# Update Generator for Windows

import os
import os.path
import hashlib
from cfile import cfile

def keywords_in_str(kw_lst, string):
    if any([i in string for i in kw_lst]):
        return True
    return False

def get_file_list(exclude_dirs = []):
    res = []
    for dirpath, dirnames, filenames in os.walk('.'):
        if keywords_in_str(exclude_dirs, dirpath) :
            continue
        for filename in [f for f in filenames]:
            res.append(os.path.join(dirpath, filename))
    return res

def generate_file_md5(filename, blocksize=2**20):
    m = hashlib.md5()
    with open( filename , "rb" ) as f:
        while True:
            buf = f.read(blocksize)
            if not buf:
                break
            m.update( buf )
    return m.hexdigest()

def gen_filelist(write_file = True):
    exclude_dirs = ['.git', '__pycache__', 'scripts']

    if cfile('filelist.txt').exists:
        os.remove('filelist.txt')

    res = []
    for filename in get_file_list(exclude_dirs):
        res.append(filename + '|' + generate_file_md5(filename))

    if not write_file:
        return res

    with open('filelist.txt', 'w') as f:
        for line in res:
            f.write(line + '\n')

if __name__ == '__main__':
    gen_filelist()
