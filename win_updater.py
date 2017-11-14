# Windows xSubEdit Project Updater

import urllib.request
import os
from os.path import split
from filelist_generator import gen_filelist

BASE_URL = 'http://dropboxuser.com/dlgsdjk/'

def get_file(url, filename):
    urllib.request.urlretrieve(url, filename)

def read_filelist(filename):
    with open(filename, 'r') as f:
        return f.readlines()

def main():
    gen_filelist()
    os.remove('remote-filelist.txt')
    get_file(BASE_URL+'/filelist.txt', 'remote-filelist.txt')

    local_list = read_filelist('filelist.txt')
    remote_list = read_filelist('remote-filelist.txt')
    local_dict = {}
    remote_dict = {}
    for line in remote_list:
        filename, md5 = line.split('|')
        filename = filename.strip()
        md5 = md5.strip()
        remote_dict[filename] = md5
    for line in local_list:
        filename, md5 = line.split('|')
        filename = filename.strip()
        md5 = md5.strip()
        local_dict[filename] = md5

    dl = []
    for key in remote_dict:
        if not (key in local_dict) or local_dict[key] != remote_dict[key]:
            dl.append((BASE_URL+'/'+key[1:], key))

    for idx, item in enumerate(dl):
        print ('Downloading: %s (%.2f)' % (split(item[1])[1], idx / len(dl) ) ,)
        get_file(item[0], item[1])

main()
