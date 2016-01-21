# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
from utils import isfloat

class cTimeChangeDialog(Gtk.Window):
    def __init__(self, parent, subtitleModel, treeview, changeList):
        super(cTimeChangeDialog, self).__init__()
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
        self.res['milliseconds1'] = None
        self.res['milliseconds2'] = None
        self.res['operation1'] = None
        self.res['operation2'] = None
        self.res['applyToTime1'] = None
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

        # Operation 1
        cdHBox1 = Gtk.HBox()
        msEntry1 = Gtk.Entry()
        opCombo1 = Gtk.ComboBoxText()
        opCombo1.append_text('add')
        opCombo1.append_text('remove')
        objCombo1 = Gtk.ComboBoxText()
        objCombo1.append_text('Start Time')
        objCombo1.append_text('Stop Time')
        objCombo1.append_text('Both Start and Stop Times')

        cdHBox1.pack_start(opCombo1, False, False, 2)
        cdHBox1.pack_start(msEntry1, False, False, 2)
        cdHBox1.pack_start(Gtk.Label('millisecond(s)'), False, False, 2)
        cdHBox1.pack_start(Gtk.Label('to'), False, False, 2)
        cdHBox1.pack_start(objCombo1, False, False, 2)

        opCombo1.connect('changed', self.on_combo_changed, 'operation1')
        msEntry1.connect('changed', self.on_entry_changed, 'milliseconds1')
        objCombo1.connect('changed', self.on_objCombo1_changed)

        # Operation 2
        self.cdHBox2 = Gtk.HBox()
        msEntry2 = Gtk.Entry()
        opCombo2 = Gtk.ComboBoxText()
        opCombo2.append_text('add')
        opCombo2.append_text('remove')

        self.cdHBox2.pack_start(opCombo2, False, False, 2)
        self.cdHBox2.pack_start(msEntry2, False, False, 2)
        self.cdHBox2.pack_start(Gtk.Label('millisecond(s)'), False, False, 2)
        self.cdHBox2.pack_start(Gtk.Label('to Stop Time'), False, False, 2)

        opCombo2.connect('changed', self.on_combo_changed, 'operation2')
        msEntry2.connect('changed', self.on_entry_changed, 'milliseconds2')

        # Apply to what?
        selectionHBox = Gtk.HBox()
        selectionBox = Gtk.ComboBoxText()
        selectionBox.append_text('all lines')
        selectionBox.append_text('selected lines')
        selectionBox.connect('changed', self.on_combo_changed, 'applyToSubs')
        selectionHBox.pack_start(Gtk.Label('of'), False, False, 3)
        selectionHBox.pack_start(selectionBox, False, False, 3)

        # Add layouts
        info = u'Δεν πρόκειται να μετακινήσει γραμμή αν αυτό παραβιάζει το κενό των 120ms.'
        vbox = Gtk.VBox()
        vbox.pack_start(Gtk.Label(info), False, False, 6)
        vbox.pack_start(cdHBox1, False, False, 4)
        vbox.pack_start(self.cdHBox2, False, False, 4)
        vbox.pack_start(selectionHBox, False, False, 4)
        vbox.pack_start(buttonBox, False, False, 4)
        self.add(vbox)

        # Finally show all widgets
        self.show_all()
        self.cdHBox2.hide()

    def on_objCombo1_changed(self, sender):
        if sender.get_model()[sender.get_active()][0] == 'Both Start and Stop Times' or sender.get_model()[sender.get_active()][0] == 'Stop Time':
            self.cdHBox2.hide()
            self.res['milliseconds2'] = 0
        else:
            self.cdHBox2.show()
        self.res['applyToTime1'] = sender.get_model()[sender.get_active()][0]

    def on_main_button_click(self, sender, sender_name):
        if sender_name != 'OK':
            self.destroy()
            return

        if self.res['applyToSubs'] is None or self.res['milliseconds1'] is None or self.res['operation1'] is None or self.res['applyToTime1'] is None:
            self.destroy()
            return

        if self.res['applyToTime1'] == 'Start Time' and (self.res['operation2'] is not None and not isfloat(self.res['milliseconds2'])):
            self.destroy()
            return

        if not isfloat(self.res['milliseconds1']):
            self.destroy()
            return

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

        if self.res['milliseconds1'] is not None:
            milliseconds1 = int(self.res['milliseconds1']) * (1 if self.res['operation1'] == 'add' else -1)
        else:
            milliseconds1 = 0
        if self.res['milliseconds2'] is not None:
            milliseconds2 = int(self.res['milliseconds2']) * (1 if self.res['operation1'] == 'add' else -1)
        else:
            milliseconds2 = 0

        operation1Items = applyItems[:]
        if milliseconds1 > 0:
            operation1Items.reverse()

        for item in applyItems:
            newBound = [None, None]
            if self.res['applyToTime1'] == 'Start Time':
                newBound[0] = int(item.startTime) + milliseconds1
                newBound[1] = int(item.stopTime) + milliseconds2
            elif self.res['applyToTime1'] == 'Stop Time':
                newBound[0] = int(item.startTime)
                newBound[1] = int(item.stopTime) + milliseconds1
            elif self.res['applyToTime1'] == 'Both Start and Stop Times':
                newBound[0] = int(item.startTime) + milliseconds1
                newBound[1] = int(item.stopTime) + milliseconds1
            else:
                continue

            nextSub = self.subtitleModel.get_next(item)
            prevSub = self.subtitleModel.get_prev(item)

            if newBound[0] < 0:
                return
            if nextSub is not None and newBound[1] > nextSub.startTime - 120:
                continue
            if prevSub is not None and newBound[0] < prevSub.stopTime + 120:
                continue
            if newBound[0] > newBound[1] or newBound[1] - newBound[0] < 1000:
                continue
            self.changeList.append((item, int(item.startTime), int(item.stopTime), int(newBound[0]), int(newBound[1])))
            item.startTime = int(newBound[0])
            item.stopTime = int(newBound[1])
        self.destroy()

    def on_combo_changed(self, sender, name):
        self.res[name] = sender.get_model()[sender.get_active()][0]

    def on_entry_changed(self, sender, name):
        self.res[name] = sender.get_text()
