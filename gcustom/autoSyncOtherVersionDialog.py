import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from rawGenerationDialog import cRawGenerationDialog
from progressBarDialog import cProgressBarDialog
from utils import isint
from os.path import split, splitext, join, exists
from subfile import srtFile
from subtitles import subRec
import autoSyncTools
import subfile

iround = lambda x: int(round(x))

def explode_path(fname):
    path, filename = split(fname)
    base, ext = splitext(filename)
    return (path, base, ext)

class cAutoSyncOtherVersionDialog(Gtk.Window):
    def __init__(self, parent, orig_video_filename, subs):
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
        self.src_v_fname = orig_video_filename
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
        self.dst_v_fname = filename

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
        if not hasattr(self, 'dst_v_fname'):
            self.close()
            return

        # Create raw filenames
        path = explode_path(self.src_v_fname)[0]
        sraw = join(path,'src-xsubedit.raw')
        draw = join(path,'dst-xsubedit.raw')

        # Generate Src Raw Audio
        #rdlg = cRawGenerationDialog(self, self.src_v_fname, sraw)
        #rdlg.run()

        # Generate Dst Raw Audio
        #rdlg = cRawGenerationDialog(self, self.dst_v_fname, draw)
        #rdlg.run()

        # Load Src, Dst spectrums
        if not exists(sraw) or not exists(draw):
            return
        src_spec = autoSyncTools.get_spect_from_file(sraw)
        dst_spec = autoSyncTools.get_spect_from_file(draw)

        # Normalize spectrums
        dst_spec = autoSyncTools.normalize_spec(dst_spec)
        src_spec = autoSyncTools.normalize_spec(src_spec)

        # create a new empty sublist
        dst_sublist = []
        missing_subs = []

        # match subs
        pb = cProgressBarDialog(self, 'Matching subtitles...', 'Matching subtitle 0 / %d' % len(self.subs))
        pb.set_progress(idx / float(len(self.subs)))
        pb.update_info('Matching subtitle %d / %d' % (idx, len(self.subs)))

        last_failed = False
        for sub_enum in enumerate(self.subs[1:]):
            (idx, sub) = sub_enum
            self.process_messages()
            # Calc offset
            if len(dst_sublist) >= 2 and abs(int(dst_sublist[-1].startTime - dst_sublist[-2].startTime)) > 5000:
                offset = int(dst_sublist[-2].startTime)
            else:
                offset = int(dst_sublist[-1].startTime) if len(dst_sublist) > 0 else 0
            # Calc break_limit
            _break_limit = int(self.subs[idx - 1].startTime - sub.startTime) * 5 if len(self.subs) > 1 and idx > 1 and not last_failed else -1
            res = autoSyncTools.match(src_spec, dst_spec, int(sub.startTime), int(sub.stopTime), offset, break_limit = _break_limit)

            if not(res is None):
                last_failed = False
                dst_sublist.append(subRec(int(res[0]), int(res[1]), sub.text))
                print res
                print dst_sublist[-1]
            else:
                last_failed = True
                print '----Failed----'
                print sub
                print '--------------'
                missing_subs.append(sub)
                if idx > 1:
                    exit()
        pb.close()

        # save new sublist
        if len(dst_sublist) > 0:
            pd = explode_path(self.dst_v_fname)
            srt = subfile.srtFile( join(pd[0], pd[1] + '.srt') )
            srt.write_to_file(dst_sublist)

        # Finally delete raw files
        #os.remove(draw)
        #os.remove(sraw)

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
