import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from utils import isint
from os.path import split, splitext, join
from subfile import srtFile

def ceildiv(a, b):
    return -(-a // b)

class cSplitSrtDialog(Gtk.Window):
    def __init__(self, parent, filename, subs):
        super(cSplitSrtDialog, self).__init__()
        self.parent = parent
        self.set_title('Split Subtitle')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        label = Gtk.Label('Split to parts...')
        self.combo = Gtk.ComboBoxText.new_with_entry()
        self.combo.append_text('2')
        self.combo.append_text('3')
        self.combo.append_text('4')
        self.combo.append_text('5')
        self.combo.append_text('6')
        self.combo.append_text('7')
        self.combo.append_text('8')
        self.combo.append_text('9')
        self.combo.append_text('10')
        self.combo.append_text('11')
        self.combo.append_text('12')
        self.combo.append_text('13')
        self.combo.append_text('14')
        self.combo.append_text('15')
        self.combo.set_active(0)
        vbox = Gtk.VBox(spacing = 2)
        vbox.add(label)
        vbox.add(self.combo)
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
        self.set_resizable(False)
        self.show_all()
        self.filename = filename.decode('utf-8')
        self.subs = subs
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.show()

    def on_btn_ok(self, sender):
        pnum = self.combo.get_active_text()
        if not isint(pnum):
            self.close()
            return
        path, filename = split(self.filename)
        basename, extension = splitext(filename)
        filenames = [join(path, '%s-part%s%s' % (basename, str(i+1).zfill(2), extension)) for i in xrange(int(pnum))]
        subs_per_part = ceildiv(len(self.subs), int(pnum))
        for idx, fname in enumerate(filenames):
            partfile = srtFile(fname)
            partfile.write_to_file(self.subs[(idx) * subs_per_part : (idx + 1) * subs_per_part])
        self.close()

    def on_btn_cnsl(self, sender):
        self.close()

    def on_key_release(self, sender, event):
        if event.keyval == Gdk.KEY_Escape:
            self.on_btn_cnsl(None)
        elif event.keyval == Gdk.KEY_Return:
            self.on_btn_ok(None)
