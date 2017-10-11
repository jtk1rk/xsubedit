import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from utils import isint
from os.path import split, splitext, join
from subfile import srtFile
from video import vobj
from numpy import load, correlate
from waveformGenerationDialog import cWaveformGenerationDialog
import scipy
import numpy

iround = lambda x: int(round(x))

def gen_pkf_fname(vfname):
    path, filename = split(vfname)
    base, ext = splitext(filename)
    return join(path, base+'.pkf')

def get_peak_data(filename):
    f = open(filename.decode('utf-8'), 'rb')
    dataFile = load(f)
    hiAudio = dataFile['arr_0'] + 1.0
    f.close()
    for i in xrange(1, len(hiAudio)-1):
        segment = hiAudio[(i-2) if i >= 2 else 0:i+2]
        avg = sum(segment) / len(segment)
        hiAudio[i] /= avg
    avg = sum(hiAudio) / len(hiAudio)
    return hiAudio / avg

class cAutoSyncOtherVersionDialog(Gtk.Window):
    def __init__(self, parent, orig_video_filename, orig_duration, subs):
        super(cAutoSyncOtherVersionDialog, self).__init__()
        self.parent = parent
        self.set_title('Auto Sync Other Version')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        label = Gtk.Label('Select another version of the video')
        self.entry = Gtk.Entry()
        vbox = Gtk.VBox(spacing = 2)

        vbox.add(label)

        hbox_entry = Gtk.HBox(spacing = 2)
        file_chooser_button = Gtk.Button()
        file_chooser_button.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON))
        hbox_entry.add(self.entry)
        hbox_entry.add(file_chooser_button)
        vbox.add(hbox_entry)

        hbox = Gtk.HBox(spacing = 2)
        btn_ok = Gtk.Button('OK')
        btn_cnsl = Gtk.Button('Cancel')
        hbox.add(btn_ok)
        hbox.add(btn_cnsl)

        vbox.add(hbox)
        self.add(vbox)

        btn_ok.connect('clicked', self.on_btn_ok)
        btn_cnsl.connect('clicked', self.on_btn_cnsl)
        self.connect('key-release-event', self.on_key_release)
        file_chooser_button.connect('clicked', self.on_file_chooser_button)
        self.entry.connect('changed', self.on_entry_change)

        self.set_resizable(False)
        self.show_all()
        self.subs = subs
        self.orig_duration = orig_duration
        self.orig_video_filename = orig_video_filename
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.show()

    def on_entry_change(self, sender):
        self.filename = self.entry.get_text()

    def on_file_chooser_button(self, sender):
        dialog = Gtk.FileChooserDialog("Video", self.parent, Gtk.FileChooserAction.OPEN, ("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('Video File')
        filter.add_pattern('*.avi')
        filter.add_pattern('*.asf')
        filter.add_pattern('*.dvx')
        filter.add_pattern('*.divx')
        filter.add_pattern('*.flv')
        filter.add_pattern('*.f4v')
        filter.add_pattern('*.h264')
        filter.add_pattern('*.mkv')
        filter.add_pattern('*.mp4')
        filter.add_pattern('*.mov')
        filter.add_pattern('*.m4v')
        filter.add_pattern('*.mpg')
        filter.add_pattern('*.mpeg')
        filter.add_pattern('*.mpe')
        filter.add_pattern('*.ogm')
        filter.add_pattern('*.ogv')
        filter.add_pattern('*.rm')
        filter.add_pattern('*.webm')
        filter.add_pattern('*.wmv')
        filter.add_pattern('*.yuv')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ""
        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename == '':
            return
        self.entry.set_text(filename)
        self.filename = filename

    def on_btn_ok(self, sender):
        self.run()
        self.close()

    def on_btn_cnsl(self, sender):
        self.close()

    def on_key_release(self, sender, event):
        if event.keyval == Gdk.KEY_Escape:
            self.on_btn_cnsl(None)
        elif event.keyval == Gdk.KEY_Return:
            self.on_btn_ok(None)

    def run(self):
        # Prepare Peaks

        # First Target Peak
        vid = vobj(self.filename)
        path = split(self.filename)[0]
        target_duration = vid.get_videoDuration()
        if target_duration == 0:
            return
        #wgDialog = cWaveformGenerationDialog(self, self.filename, join(path, 'target.pkf'), target_duration, 8000)
        #wgDialog.run()

        # Next, orig peak
        #wgDialog = cWaveformGenerationDialog(self, self.orig_video_filename, join(path, 'orig.pkf'), self.orig_duration, 8000)
        #wgDialog.run()

        # setup variables
        target_subs = []
        target_duration = vid.get_videoDuration() / 1000000.0
        orig_duration = self.orig_duration / 1000000.0

        # Load peaks into target_peak and orig_peak
        target_peak = get_peak_data(join(path, 'target.pkf'))
        orig_peak = get_peak_data(join(path, 'orig.pkf'))

        # For each sub calculate the position data of source peak
        # and try to match them on target, if the confidence of target position
        # is high enough then save create a new subRec in the 'target_subs' list

        #for sub in self.subs:
        #    pass

        sub = self.subs[0]
        pstart = int(sub.startTime) / float(orig_duration)
        pstop = int(sub.stopTime) / float(orig_duration)
        olen = len(orig_peak)
        orig_segment = orig_peak[max(iround(olen * pstart)-2000, 0) : iround(olen * pstop)+2000]

        #a = numpy.correlate(target_peak, orig_segment)
        a = []

        for i in xrange(len(target_peak) - len(orig_segment) + 1):
            result = target_peak[i : i+len(orig_segment)]  * orig_segment
            a.append( sum(result) / len(result) )

        print 'len(a)=%d, len(target_peak)=%d, len(orig_segment)= %d, argmax(a)=%d' %(len(a), len(target_peak), len(orig_segment), numpy.argmax(a))

        with open('a.csv', 'w') as f:
            for i in a:
                f.write('%s\n' % str(i))

        with open('target_peak.csv', 'w') as f:
            for i in target_peak:
                f.write('%s\n' % str(i))

        with open('orig_peak.csv', 'w') as f:
            for i in orig_peak:
                f.write('%s\n' % str(i))


        #for i in xrange(len(target_peak) - len(orig_segment)):

        # Save target_sub list in an appropriate filename
        pass
