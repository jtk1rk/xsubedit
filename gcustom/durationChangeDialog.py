# -*- coding: UTF-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
from utils import isfloat

class cDurationChangeDialog(Gtk.Window):
    def __init__(self, parent, subtitleModel, treeview, changeList):
        super(cDurationChangeDialog, self).__init__()
        self.parent = parent
        self.set_title('Duration Edit Dialog')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.set_resizable(False)
        self.subtitleModel = subtitleModel
        self.res = {}
        self.tvSelectionList = []
        self.treeview = treeview
        self.res['applyTo'] = None
        self.res['originalMS'] = None
        self.res['targetMS'] = None
        self.res['operation'] = None
        self.res['condition'] = None
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

        # Selected / All combo
        comboHBox = Gtk.HBox(spacing = 3)
        selectionBox = Gtk.ComboBoxText()
        selectionBox.append_text('all lines')
        selectionBox.append_text('selected lines')
        comboHBox.pack_start(Gtk.Label('Apply changes to '), False, False, 3)
        comboHBox.pack_start(selectionBox, False, False, 3)
        selectionBox.connect('changed', self.on_combo_changed, 'applyTo')

        # Conditional
        cdHBox1 = Gtk.HBox()
        cdHBox2 = Gtk.HBox()
        cdCombo = Gtk.ComboBoxText()
        cdCombo.append_text('<')
        cdCombo.append_text('>')
        cdCombo.append_text('>=')
        cdCombo.append_text('<=')
        cdCombo.append_text('=')
        origMSEntry = Gtk.Entry()
        opCombo = Gtk.ComboBoxText()
        opCombo.append_text('add')
        opCombo.append_text('remove')
        tgMSEntry = Gtk.Entry()

        cdHBox1.pack_start(Gtk.Label('If duration is '), False, False, 2)
        cdHBox1.pack_start(cdCombo, False, False, 2)
        cdHBox1.pack_start(origMSEntry, False, False, 2)
        cdHBox1.pack_start(Gtk.Label('millisecond(s) then '), False, False, 2)
        cdHBox2.pack_start(opCombo, False, False, 2)
        cdHBox2.pack_start(tgMSEntry, False, False, 2)
        cdHBox2.pack_start(Gtk.Label('millisecond(s)'), False, False, 2)

        opCombo.connect('changed', self.on_combo_changed, 'operation')
        cdCombo.connect('changed', self.on_combo_changed, 'condition')
        tgMSEntry.connect('changed', self.on_entry_changed, 'targetMS')
        origMSEntry.connect('changed', self.on_entry_changed, 'originalMS')

        # Add layouts
        info = u'Η διάρκεια δεν πρόκειται να γίνει μικρότερη από 1 δευτερόλεπτο,\nδεν πρόκειται να παραβιάσει το κενό των 120ms\nκαι δεν πρόκειται να μετατρέψει μια γραμμή σε "πολύ γρήγορη".'
        vbox = Gtk.VBox()
        vbox.pack_start(Gtk.Label(info), False, False, 6)
        vbox.pack_start(comboHBox, False, False, 4)
        vbox.pack_start(cdHBox1, False, False, 4)
        vbox.pack_start(cdHBox2, False, False, 6)
        vbox.pack_start(buttonBox, False, False, 4)
        self.add(vbox)

        # Finally show all widgets
        self.show_all()

    def on_main_button_click(self, sender, sender_name):
        if sender_name != 'OK' or any(entry is None for entry in self.res.itervalues()) or self.subtitleModel.is_empty() or not(isfloat(self.res['originalMS']) or isfloat(self.res['targetMS'])):
            self.destroy()
            return

        # Create list of subtitles to apply changes
        applyItems = []
        if self.res['applyTo'] == 'all lines':
            for item in self.subtitleModel.get_model():
                applyItems.append(item[0])
        else:
            self.get_tv_selection()
            if len(self.tvSelectionList) == 0:
                self.destroy()
                return
            applyItems = self.tvSelectionList[:]

        origMS = int(self.res['originalMS'])
        targetMS = int(self.res['targetMS'])

        for item in applyItems:
            if (self.res['condition'] == '<' and not(item.duration < origMS)) or (self.res['condition'] == '<=' and not(item.duration < origMS)) or (self.res['condition'] == '>' and not(item.duration > origMS)) or (self.res['condition'] == '>=' and not(item.duration >= origMS)) or (self.res['condition'] == '=' and not(item.duration == origMS)):
                continue

            # Check if new duration is less than the minimum allowed
            minDuration = int ( (20.0 * (item.calc_target_duration() - 500) / 26.9999999999) + 500 ) + 1
            targetDuration = item.duration + targetMS * (1 if self.res['operation'] == 'add' else -1)
            targetDuration = targetDuration if targetDuration >= minDuration else minDuration
            targetDuration = targetDuration if targetDuration >= 1000 else 1000

            # Check if gap is not violated
            newStop = int(item.stopTime) + (int(targetDuration) - int(item.duration))
            nextSub = self.subtitleModel.get_next(item)
            if nextSub is not None and newStop > nextSub.startTime - 120:
                newStop = nextSub.startTime - 120

            # Check if change in stopTime violates min duration
            if int(newStop) - int(item.startTime) < int(minDuration):
                continue

            # Finally Apply newStop
            self.changeList.append( (item, int(item.startTime), int(item.stopTime), int(item.startTime), int(newStop)) )
            item.stopTime = int(newStop)

        self.destroy()

    def on_combo_changed(self, sender, name):
        self.res[name] = sender.get_model()[sender.get_active()][0]

    def on_entry_changed(self, sender, name):
        self.res[name] = sender.get_text()
