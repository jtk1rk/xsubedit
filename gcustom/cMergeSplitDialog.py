import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from splitSrtDialog import cSplitSrtDialog
from subfile import srtFile
from cfile import cfile
from utils import common_part

class cMergeSplitDialog(Gtk.Window):
    def __init__(self, parent):
        super(cMergeSplitDialog, self).__init__()
        self.parent = parent
        self.set_title('Merge / Split Subtitles')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        vbox = Gtk.VBox(spacing = 2)
        btn_merge = Gtk.Button('Merge Subtitles')
        btn_split = Gtk.Button('Split Subtitle')
        vbox.add(btn_merge)
        vbox.add(btn_split)
        hbox = Gtk.HBox()
        btn_close = Gtk.Button('Close')
        hbox.pack_end(btn_close, False, False, 2)
        vbox.add(hbox)
        self.add(vbox)
        btn_close.connect('clicked', self.on_btn_close)
        btn_merge.connect('clicked', self.on_btn_merge)
        btn_split.connect('clicked', self.on_btn_split)
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)
        self.show()

    def on_btn_split(self, sender):
        dialog = Gtk.FileChooserDialog("Subtitle", self.parent, Gtk.FileChooserAction.OPEN, ("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('Subtitle File')
        filter.add_pattern('*.srt')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ""
        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename == '':
            return

        subs = srtFile(filename).read_from_file()
        if len(subs) > 0:
            dialog = cSplitSrtDialog(self, filename, subs)
        dialog.connect('destroy', self.child_destroy)

    def child_destroy(self, sender):
        self.close()

    def on_btn_merge(self, sender):
        dialog = Gtk.FileChooserDialog('Subtitle', self.parent, Gtk.FileChooserAction.OPEN, ('_Cancel', Gtk.ResponseType.CANCEL, '_Open', Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_select_multiple(True)
        filter = Gtk.FileFilter()
        filter.set_name('Subtitle File')
        filter.add_pattern('*.srt')
        dialog.add_filter(filter)
        res = dialog.run()
        filenames = []
        if res == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
        dialog.destroy()
        if len(filenames) == 1:
            return

        subs = []
        for fn in filenames:
            subs.extend(srtFile(fn).read_from_file())
        subs.sort(key=lambda x: int(x.startTime))

        inf1 = cfile(filenames[0])
        inf2 = cfile(filenames[1])
        outf = common_part(inf1.full_path, inf2.full_path)
        if len(outf) == 0:
            outf = 'merged.srt'
        else:
            outf += '-merged.srt'
        srtFile(outf).write_to_file(subs)
        self.close()

    def on_btn_close(self, sender):
        self.close()

    def on_key_release(self, sender, event):
        if event.keyval == Gdk.KEY_Escape:
            self.on_btn_close(None)
