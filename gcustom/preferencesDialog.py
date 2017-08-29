import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from utils import isfloat

class cPreferencesDialog(Gtk.Dialog):
    def __init__(self, parent, data, viewport):
        super(cPreferencesDialog, self).__init__('Preferences', None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, ("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK))
        self.parent = parent
        self.set_transient_for(parent)
        self.set_resizable(False)

        self.preferences = data.copy()
        self.viewport = viewport
        self.enc_win1253 = Gtk.RadioButton(group = None, label = 'Windows-1253 (Default for Windows)')
        self.enc_utf8_bom = Gtk.RadioButton(group = self.enc_win1253, label='UTF-8 BOM')

        encoding_frame = Gtk.Frame()
        encoding_vbox = Gtk.VBox()
        encoding_frame.set_label('Encoding used for saving')
        encoding_vbox.add(self.enc_win1253)
        encoding_vbox.add(self.enc_utf8_bom)
        encoding_frame.add(encoding_vbox)

        self.CheckButton_Incremental_Backups = Gtk.CheckButton('Incremental Backups')
        self.CheckButton_Autosave = Gtk.CheckButton('Autosave (every 1 minute)')
        hbox = Gtk.HBox(spacing = 4)
        label = Gtk.Label('Waveform Zoom')
        self.zoomEntry = Gtk.Entry()
        useCurrentZoomButton = Gtk.Button('Use Current')
        useCurrentZoomButton.connect('clicked', self.on_useCurrentZoomButton_clicked)
        hbox.add(label)
        hbox.add(self.zoomEntry)
        hbox.add(useCurrentZoomButton)

        self.vbox.add(encoding_frame)
        self.vbox.add(self.CheckButton_Incremental_Backups)
        self.vbox.add(self.CheckButton_Autosave)
        self.vbox.add(hbox)

        self.CheckButton_Incremental_Backups.set_active(self.preferences['Incremental_Backups'])
        self.CheckButton_Autosave.set_active(self.preferences['Autosave'])
        if self.preferences['Encoding'] == 'Windows-1253':
            self.enc_win1253.set_active(True)
        elif self.preferences['Encoding'] == 'UTF-8 BOM':
            self.enc_utf8_bom.set_active(True)

        if not 'SceneDetect' in self.preferences:
            self.preferences['SceneDetect'] = {'Auto': False, 'TwoPass': True}

        self.SDCheckButton = Gtk.CheckButton('Auto Scene Detect')
        self.SDCheckButton.set_active(self.preferences['SceneDetect']['Auto'])
        self.SDPCheckButton = Gtk.CheckButton('Two Pass (fast)')
        self.SDPCheckButton.set_active(self.preferences['SceneDetect']['TwoPass'])

        hbox = Gtk.HBox(spacing = 5)
        hbox.add(self.SDCheckButton)
        hbox.add(self.SDPCheckButton)
        self.vbox.add(hbox)

        self.SDCheckButton.connect('toggled', self.on_SD_toggle, 'Auto')
        self.SDPCheckButton.connect('toggled', self.on_SD_toggle, 'TwoPass')

        if not 'Zoom' in self.preferences:
            self.preferences['Zoom'] = 20

        self.zoomEntry.set_text(str(self.preferences['Zoom']))

        self.CheckButton_Incremental_Backups.connect('clicked', self.CheckButton_Incremental_Backups_Clicked)
        self.CheckButton_Autosave.connect('clicked', self.CheckButton_Autosave_Clicked)
        self.enc_utf8_bom.connect('clicked', self.enc_utf8_bom_Clicked)
        self.enc_win1253.connect('clicked', self.enc_win1253_Clicked)
        self.zoomEntry.connect('changed', self.on_zoomEntry_change)

        self.vbox.show_all()
        self.set_default_response(Gtk.ResponseType.OK)

    def on_SD_toggle(self, widget, value):
        if value == 'Auto':
            self.preferences['SceneDetect'][value] = widget.get_active()
        elif value == 'TwoPass':
            self.preferences['SceneDetect'][value] = widget.get_active()

    def on_zoomEntry_change(self, sender):
        if isfloat(sender.get_text()):
            if float(sender.get_text()) == 0:
                return
            self.preferences['Zoom'] = float(sender.get_text())

    def on_useCurrentZoomButton_clicked(self, sender):
        if self.viewport[0] != self.viewport[1]:
            self.zoomEntry.set_text( str(round(1 / float(self.viewport[1] - self.viewport[0]), 2)) )

    def enc_utf8_bom_Clicked(self, sender):
        self.preferences['Encoding'] = 'UTF-8 BOM'

    def enc_win1253_Clicked(self, sender):
        self.preferences['Encoding'] = 'Windows-1253'

    def CheckButton_Autosave_Clicked(self, sender):
        self.preferences['Autosave'] = self.CheckButton_Autosave.get_acvite()

    def CheckButton_Incremental_Backups_Clicked(self,  sender):
        self.preferences['Incremental_Backups'] = self.CheckButton_Incremental_Backups.get_active()

    def CheckButton_BOM_Clicked(self, sender):
        self.preferences['BOM'] = self.CheckButton_BOM.get_active()
