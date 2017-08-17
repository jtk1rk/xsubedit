#!/bin/bash
zypper addrepo -f http://packman.inode.at/suse/openSUSE_Leap_42.1/ packman
zypper addrepo -f http://download.opensuse.org/distribution/leap/42.1/repo/oss/ oss
zypper addrepo -f http://download.opensuse.org/distribution/leap/42.1/repo/non-oss/ non-oss
zypper addrepo -f http://download.opensuse.org/update/leap/42.1/oss/ oss-update
zypper addrepo -f http://download.opensuse.org/update/leap/42.1/non-oss/ non-oss-update
zypper addrepo http://download.opensuse.org/repositories/devel:/languages:/python/openSUSE_Leap_42.1/ devel-python
zypper ref
zypper up
zypper dup --from packman
zypper in --from packman gstreamer-plugins-base gstreamer-plugins-bad gstreamer-plugins-bad-orig-addon gstreamer-plugins-good gstreamer-plugins-ugly gstreamer-plugins-vaapi gstreamer-plugins-libav
zypper in python-regex
rm -rf ~/.cache/gstreamer-1.0