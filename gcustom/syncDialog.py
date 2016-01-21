# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
from utils import isfloat, grad

class cSyncDialog(Gtk.Window):
    def __init__(self, parent, subtitleModel, treeview, changeList):
        super(cSyncDialog, self).__init__()
        self.parent = parent
        self.set_title('Time Sync Dialog')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.set_resizable(False)
        self.subtitleModel = subtitleModel
        self.res = {}
        self.tvSelectionList = []
        self.treeview = treeview
        self.res['applyToSubs'] = None
        self.res['ms1'] = None
        self.res['ms2'] = None
        self.res['op1'] = None
        self.res['op2'] = None
        self.changeList = changeList
        self.setup_ui()
        self.connect('key-release-event', self.on_key_release)
        self.show()

    def on_key_release(self, sender, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()

    def get_tv_selection(self):
        widget = self.treeview
        (model, pathlist) = widget.get_selection().get_selected_rows()
        self.tvSelectionList= []
        for path in pathlist:
            tree_iter = model.get_iter(path)
            self.tvSelectionList.append(model.get_value(tree_iter, 0))

    def setup_ui(self):
        # Main Buttons
        button_ok = Gtk.Button('OK')
        button_cancel = Gtk.Button('Cancel')
        button_ok.connect('clicked', self.on_main_button_click, 'OK')
        button_cancel.connect('clicked', self.on_main_button_click, 'Cancel')
        buttonBox = Gtk.HBox(spacing = 3)
        buttonBox.pack_start(button_cancel, False, False, 2)
        buttonBox.pack_end(button_ok, False, False, 2)

        # Apply to what?
        selectionHBox = Gtk.HBox()
        selectionBox = Gtk.ComboBoxText()
        selectionBox.append_text('all lines')
        selectionBox.append_text('selected lines')
        selectionBox.connect('changed', self.on_combo_changed, 'applyToSubs')
        selectionHBox.pack_start(Gtk.Label('Apply changes to '), False, False, 3)
        selectionHBox.pack_start(selectionBox, False, False, 3)

        # Operations
        line1 = Gtk.HBox()
        line2 = Gtk.HBox()

        op1 = Gtk.ComboBoxText()
        op1.append_text('Add')
        op1.append_text('Remove')
        ms1 = Gtk.Entry()
        ms2 = Gtk.Entry()
        op2 = Gtk.ComboBoxText()
        op2.append_text('Add')
        op2.append_text('Remove')
        op1.connect('changed', self.on_combo_changed, 'op1')
        op2.connect('changed', self.on_combo_changed, 'op2')
        ms1.connect('changed', self.on_entry_changed, 'ms1')
        ms2.connect('changed', self.on_entry_changed, 'ms2')

        line1.pack_start(op1, False, False, 3)
        line1.pack_start(ms1, False, False, 3)
        line1.pack_start(Gtk.Label('milliseconds to/from beginning'), False, False, 3)
        line2.pack_start(op2, False, False, 3)
        line2.pack_start(ms2, False, False, 3)
        line2.pack_start(Gtk.Label('milliseconds to/from end'), False, False, 3)

        # Add layouts
        vbox = Gtk.VBox()
        vbox.pack_start(selectionHBox, False, False, 3)
        vbox.pack_start(line1, False, False, 3)
        vbox.pack_start(line2, False, False, 3)
        vbox.pack_start(buttonBox, False, False, 3)
        self.add(vbox)

        # Finally show all widgets
        self.show_all()

    def on_combo_changed(self, sender, sender_name):
        self.res[sender_name] = sender.get_model()[sender.get_active()][0]

    def on_entry_changed(self, sender, sender_name):
        self.res[sender_name] = sender.get_text()

    def on_main_button_click(self, sender, sender_name):
        if sender_name != 'OK':
            self.destroy()
            return

        if not( isfloat(self.res['ms1']) and isfloat(self.res['ms2']) ):
            return

        ms1 = int(self.res['ms1'])
        ms2 = int(self.res['ms2'])

        # Create list of subtitles to apply changes
        applyItems = []
        if self.res['applyToSubs'] == 'all lines':
            for item in self.subtitleModel.get_model():
                applyItems.append(item[0])
        else:
            self.get_tv_selection()
            if len(self.tvSelectionList) == 0:
                self.destroy()
                return
            applyItems = self.tvSelectionList[:]

        A0 = int(applyItems[0].startTime)
        B0 = int(applyItems[-1].startTime)
        A = int(applyItems[0].startTime) + ms1 * (1 if self.res['op1'] == 'Add' else -1)
        B = int(applyItems[-1].startTime) + ms2 * (1 if self.res['op2'] == 'Add' else -1)

        if A0 == B0:
            return
            
        for item in applyItems:
            duration = int(item.duration)
            new_start_time = int( grad(A0, B0, A, B, int(item.startTime)) )
            new_stop_time = int(new_start_time) + duration
            self.changeList.append( (item, int(item.startTime), int(item.stopTime), int(new_start_time), int(new_stop_time)) )
            item.startTime = new_start_time
            item.stopTime = new_stop_time

        self.destroy()
