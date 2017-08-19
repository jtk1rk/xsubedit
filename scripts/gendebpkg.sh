ver=$(cat ~/git/xsubedit/__main__.py | grep xSubEdit | sed 's/.*Edit //' | sed 's/\x27.*//')
targetdir=$(echo -n xSubEdit_$ver-pepper)

rm -rf ~/xsubedit.gen
git clone http://github.com/jtk1rk/xsubedit.git ~/xsubedit.gen
cd ~/xsubedit.gen
rm -rf ~/xsubedit.gen/scripts

mkdir -p ~/$targetdir
cd ~/$targetdir

mkdir -p ~/$targetdir/DEBIAN
mkdir -p ~/$targetdir/usr/bin
mkdir -p ~/$targetdir/usr/share/applications
mkdir -p ~/$targetdir/usr/share/icons/hicolor/128x128/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/16x16/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/22x22/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/24x24/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/256x256/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/32x32/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/48x48/apps
mkdir -p ~/$targetdir/usr/share/icons/hicolor/64x64/apps
mkdir -p ~/$targetdir/usr/share/xsubedit

cp ~/xsubedit.gen/share/xsubedit.desktop ~/$targetdir/usr/share/applications/
cp ~/xsubedit.gen/share/xsubedit-16.png ~/$targetdir/usr/share/icons/hicolor/16x16/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-22.png ~/$targetdir/usr/share/icons/hicolor/22x22/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-24.png ~/$targetdir/usr/share/icons/hicolor/24x24/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-32.png ~/$targetdir/usr/share/icons/hicolor/32x32/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-48.png ~/$targetdir/usr/share/icons/hicolor/48x48/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-64.png ~/$targetdir/usr/share/icons/hicolor/64x64/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-128.png ~/$targetdir/usr/share/icons/hicolor/128x128/apps/xsubedit.png
cp ~/xsubedit.gen/share/xsubedit-256.png ~/$targetdir/usr/share/icons/hicolor/256x256/apps/xsubedit.png
cp ~/xsubedit.gen/share/thesaurus.pz ~/$targetdir/usr/share/xsubedit

rm -rf ~/xsubedit.gen/share
rm ~/xsubedit.gen/thesaurus.pz

cd ~/xsubedit.gen
zip -r xsubedit.zip *
echo '#!/usr/bin/env python2' > xsubedit
cat xsubedit.zip >> xsubedit
chmod +x xsubedit

cp ~/xsubedit.gen/xsubedit ~/$targetdir/usr/bin

echo "Package: xSubEdit
Version: $ver
Architecture: all
Maintainer: James T. Kirk
Depends: python2.7, python-enchant, python-numpy, gir1.2-gtkspell3-3.0, python-regex, mediainfo, ffmpeg, myspell-el-gr, gstreamer1.0-alsa, gstreamer1.0-plugins-base, gstreamer1.0-plugins-good, gstreamer1.0-plugins-bad, gstreamer1.0-plugins-ugly, gstreamer1.0-tools, gstreamer1.0-libav, python-appdirs, python-requests, python-bs4, gir1.2-gstreamer-1.0, gir1.2-gst-plugins-base-1.0, python-gi-cairo
Homepage: http://xsubedit.blogspot.gr
Description: Greek Subtitle Editor
 xSubEdit is a subtitle editor made specifically for creating/translating subtitles into the Greek language.
 With minor modifications it can be made to work for any language.
 This program is intended to be used by the xsubs.tv group." >> ~/$targetdir/DEBIAN/control

chmod +x ~/$targetdir/DEBIAN/control

cd ~
dpkg-deb --build $targetdir

rm -rf ~/xsubedit.gen
rm -rf ~/$targetdir