import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class cPreferencesDialog(Gtk.Dialog):
    def __init__(self, parent, data):
        super(cPreferencesDialog, self).__init__('Preferences', None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, ("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK))
        self.parent = parent
        self.set_transient_for(parent)
        self.set_resizable(False)

        self.preferences = data.copy()

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

        self.vbox.add(encoding_frame)
        self.vbox.add(self.CheckButton_Incremental_Backups)
        self.vbox.add(self.CheckButton_Autosave)

        self.CheckButton_Incremental_Backups.set_active(self.preferences['Incremental_Backups'])
        self.CheckButton_Autosave.set_active(self.preferences['Autosave'])
        if self.preferences['Encoding'] == 'Windows-1253':
            self.enc_win1253.set_active(True)
        elif self.preferences['Encoding'] == 'UTF-8 BOM':
            self.enc_utf8_bom.set_active(True)

        self.CheckButton_Incremental_Backups.connect('clicked', self.CheckButton_Incremental_Backups_Clicked)
        self.CheckButton_Autosave.connect('clicked', self.CheckButton_Autosave_Clicked)
        self.enc_utf8_bom.connect('clicked', self.enc_utf8_bom_Clicked)
        self.enc_win1253.connect('clicked', self.enc_win1253_Clicked)

        self.vbox.show_all()
        self.set_default_response(Gtk.ResponseType.OK)

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
