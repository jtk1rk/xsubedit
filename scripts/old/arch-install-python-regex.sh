#!/bin/bash

sudo pacman -S binutils wget fakeroot gcc git

rn=$RANDOM
dname='python-regex-'$rn
mkdir $dname
cd $dname
wget https://aur.archlinux.org/cgit/aur.git/snapshot/python-regex.tar.gz
tar -zxvf python-regex.tar.gz
cd python-regex
makepkg -s -i
cd ../..
rm -rf $dname


