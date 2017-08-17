import os
import site
import sys
import glob

#cx_freeze
from cx_Freeze import setup, Executable

siteDir = site.getsitepackages()[1]
includeDllPath = os.path.join(siteDir, "gnome")

# This is the list of dll which are required by PyGI.
# I get this list of DLL using http://technet.microsoft.com/en-us/sysinternals/bb896656.aspx
#   Procedure: 
#    1) Run your from from your IDE
#    2) Command for using listdlls.exe
#        c:/path/to/listdlls.exe python.exe > output.txt
#    3) This would return lists of all dll required by you program 
#       in my case most of dll file were located in c:\python27\Lib\site-packages\gnome 
#       (I am using PyGI (all in one) installer)
#    4) Below is the list of gnome dll I recevied from listdlls.exe result. 

# If you prefer you can import all dlls from c:\python27\Lib\site-packages\gnome folder
#missingDLL = glob.glob(includeDllPath + "\\" + '*.dll')

# List of dll I recevied from listdlls.exe result
missingDLL = ['libffi-6.dll',
              'libgraphene-1.0-0.dll',
              'libaerial-0.dll',
              #'uxtheme.dll',
              'libenchant-1.dll',
              #'libenchant_ispell.dll',
              #'libenchant_myspell.dll',
              'libjasper-1.dll',
              'libtiff-5.dll',
              'libgstapp-1.0-0.dll',
              'libgstriff-1.0-0.dll',
              'libgstrtp-1.0-0.dll',
              'libgstfft-1.0-0.dll',
              'liborc-test-0.4-0.dll',
              'libgstbasecamerabinsrc-1.0-0.dll',
              'libgstbadvideo-1.0-0.dll',
              'libgstrtsp-1.0-0.dll',
              'libgstphotography-1.0-0.dll',
              'libidn-11.dll',
              'libgstgl-1.0-0.dll',
              'libgstsdp-1.0-0.dll',
              'libsqlite3-0.dll',
              'libcurl-4.dll',
              'libgsturidownloader-1.0-0.dll',
              'libfluidsynth-1.dll',
              'libjack.dll',
              'libvisual-0.4-0.dll',
              'libgstcodecparsers-1.0-0.dll',
              'libgstmpegts-1.0-0.dll',
              'libfftw3.dll',
              'libopenexr-2.dll',
              'libgstbadbase-1.0-0.dll',
              'libopenjp2.dll',
              'libgstnet-1.0-0.dll',
              'libsoup-2.4-1.dll',
              'libgstreamer-1.0-0.dll',
              'lib\\gstreamer-1.0\\libgstwildmidi.dll',
              'libgstbase-1.0-0.dll',
              'libWildMidi-1.dll',
              'lib\\gstreamer-1.0\\libgstpango.dll',
              'libgstvideo-1.0-0.dll',
              'liborc-0.4-0.dll',
              'lib\\gstreamer-1.0\\libgstd3dvideosink.dll',
              'libgirepository-1.0-1.dll',
              'lib\\gstreamer-1.0\\libgstplayback.dll',
              'libgstaudio-1.0-0.dll',
              'libgsttag-1.0-0.dll',
              'libgstpbutils-1.0-0.dll',
              'libgio-2.0-0.dll',
              'libglib-2.0-0.dll',
              'libintl-8.dll',
              'libgmodule-2.0-0.dll',
              'libgobject-2.0-0.dll',
              'libzzz.dll',
              'libwinpthread-1.dll',
              'libgtk-3-0.dll',
              'libgdk-3-0.dll',
              'libcairo-gobject-2.dll',
              'libfontconfig-1.dll',
              'libxmlxpat.dll',
              'libfreetype-6.dll',
              'libpng16-16.dll',
              'libgdk_pixbuf-2.0-0.dll',
              'libjpeg-8.dll',
              #'libopenraw-7.dll',
              'librsvg-2-2.dll',
              'libpango-1.0-0.dll',
              'libpangocairo-1.0-0.dll',
              'libpangoft2-1.0-0.dll',
              'libharfbuzz-gobject-0.dll',
              'libharfbuzz-0.dll',
              'libpangowin32-1.0-0.dll',
              'libwebp-5.dll',
              'libatk-1.0-0.dll',
              #'libgnutls-26.dll',
              'libproxy.dll',
              'libp11-kit-0.dll',
              #'libepoxy-0.dll',
              'libgnutls-28.dll'
              #'libavcodec-56.dll',
              #'libgcrypt-11.dll',
              #'libgstadaptivedemux-1.0-0.dll',
              #'libopenssl.dll',
              #'libstdc++-6.dll',
              #'libgstvalidate-1.0-0.dll',
              #'libgstvalidatevideo-1.0-0.dll',
              #'libavutil-54.dll',
              #'libswresample-1.dll',
              #'libavformat-56.dll'
              ]


includeFiles = []
for DLL in missingDLL:
    includeFiles.append((os.path.join(includeDllPath, DLL), DLL))
    #includeFiles.append(DLL) 

# You can import all Gtk Runtime data from gtk folder              
#gtkLibs= ['etc','lib','share']

# You can import only important Gtk Runtime data from gtk folder  
gtkLibs = ['lib\\gdk-pixbuf-2.0',
           'lib\\girepository-1.0',
           'share\\glib-2.0',
           'share\\fontconfig',
           'share\\fonts',
           'share\\icons',
           'etc\\fonts',
           'share\\enchant',
           #'lib\\gtk-3.0',
           'lib\\gstreamer-1.0']


for lib in gtkLibs:
    includeFiles.append((os.path.join(includeDllPath, lib), lib))

lib = 'enchant'
includeFiles.append((os.path.join(siteDir, lib), lib))

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name = "xSubEdit",
    version = "1.0",
    description = "Subtitle Editor for xSubs",
    options = {'build_exe' : {
#        'compressed': True,
        'includes': ["gi",'numpy.core._methods','numpy.lib.format'],
        'excludes': [],#['wx', 'email', 'pydoc_data', 'curses', 'tk'],
        'packages': ["gi", 'idna'],
        'include_files': includeFiles
    }},
    executables = [
        Executable("main.py",
                   base=base
                   )
    ]
)
