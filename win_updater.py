# Windows xSubEdit Project Updater

import urllib.request
import requests
import os
from os.path import split
from filelist_generator import gen_filelist
from cfile import cfile

BASE_URL = 'https://raw.githubusercontent.com/jtk1rk/xsubedit/master'

def get_file(url, filename):
    urllib.request.urlretrieve(url, filename)

def read_remote_file(url):
    return requests.get(url).text.split()

def read_filelist(filename):
    with open(filename, 'r') as f:
        return f.readlines()

def main():
    local_list = gen_filelist(write_file = False)
    print(BASE_URL+'/filelist.txt')
    remote_list = read_remote_file(BASE_URL+'/filelist.txt')

    local_dict = {}
    remote_dict = {}
    for line in remote_list:
        print(line)
        filename, md5 = line.split('|')
        filename = filename.strip()
        md5 = md5.strip()
        remote_dict[filename] = md5
    for line in local_list:
        print(line)
        filename, md5 = line.split('|')
        filename = filename.strip()
        md5 = md5.strip()
        local_dict[filename] = md5

    dl = []
    for key in remote_dict:
        if not (key in local_dict) or local_dict[key] != remote_dict[key]:
            dl.append((BASE_URL+'/'+key[1:], key))

    for idx, item in enumerate(dl):
        print ('Downloading: %s (%.2f)' % (split(item[1])[1], idx+1 / len(dl) ) ,)
        #f = cfile(item[1])
        #if not f.path_exists:
        #    f.create_path()
        #get_file(item[0], item[1])

main()
