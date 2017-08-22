import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from os.path import splitext

class cProjectSettingsDialog(Gtk.Dialog):
    def __init__(self, parent, project):
        super(cProjectSettingsDialog, self).__init__('Project Settings', None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, ("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK))
        self.parent = parent
        self.set_transient_for(parent)
        self.set_resizable(False)
        if project['projectFile'] == '':
            self.use_vo = True
        else:
            self.use_vo = (project['voFile'] != '')

        hbox1 = Gtk.HBox(spacing=4)
        self.videoButton = Gtk.Button()
        self.videoButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON))
        self.project_video_entry = Gtk.Entry()
        self.project_video_entry.props.width_request = 400
        hbox1.pack_start(Gtk.Label("Project Video"), False, False, 0)
        hbox1.pack_end(self.videoButton, False, False, 0)
        hbox1.pack_end(self.project_video_entry, False, True, 0)

        hbox2 = Gtk.HBox(spacing=4)
        self.projectButton = Gtk.Button()
        self.projectButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON))
        self.project_filename_entry = Gtk.Entry()
        self.project_filename_entry.props.width_request = 400
        hbox2.pack_start(Gtk.Label("Project File"), False, False, 0)
        hbox2.pack_end(self.projectButton, False, False, 0)
        hbox2.pack_end(self.project_filename_entry, False, True, 0)

        hbox3 = Gtk.HBox(spacing=4)
        self.subtitleButton = Gtk.Button()
        self.subtitleButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON))
        self.project_sub_filename_entry = Gtk.Entry()
        self.project_sub_filename_entry.props.width_request = 400
        hbox3.pack_start(Gtk.Label("Project Sub"), False, False, 0)
        hbox3.pack_end(self.subtitleButton, False, False, 0)
        hbox3.pack_end(self.project_sub_filename_entry, False, True, 0)

        hbox4 = Gtk.HBox(spacing=4)
        self.voButton = Gtk.Button()
        self.voButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON))
        self.project_vo_filename_entry = Gtk.Entry()
        self.project_vo_filename_entry.props.width_request = 400
        #hbox4.pack_start(Gtk.Label("Project VO"), False, False, 0)
        voCheckButton = Gtk.CheckButton('Project VO')
        voCheckButton.set_active(self.use_vo)
        voCheckButton.connect('toggled', self.on_vo_toggled)
        hbox4.pack_start(voCheckButton, False, False, 0)
        hbox4.pack_end(self.voButton, False, False, 0)
        hbox4.pack_end(self.project_vo_filename_entry, False, True, 0)

        self.vbox.pack_start(hbox1, False, False, 0)
        self.vbox.pack_start(hbox2, False, False, 0)
        self.vbox.pack_start(hbox3, False, False, 0)
        self.vbox.pack_start(hbox4, False, False, 0)

        self.project_video_entry.set_text(project['videoFile'])
        self.project_filename_entry.set_text(project['projectFile'])
        self.project_sub_filename_entry.set_text(project['subFile'])
        self.project_vo_filename_entry.set_text(project['voFile'])

        self.project_filename_entry.connect('changed', self.on_project_filename_entry_change)
        self.project_video_entry.connect('changed', self.on_project_video_entry_change)
        self.project_sub_filename_entry.connect('changed', self.on_project_sub_filename_entry_change)
        self.project_vo_filename_entry.connect('changed', self.on_project_vo_filename_entry_change)
        self.videoButton.connect('clicked', self.on_videoButton_clicked)
        self.projectButton.connect('clicked', self.on_projectButton_clicked)
        self.subtitleButton.connect('clicked', self.on_subtitleButton_clicked)
        self.voButton.connect('clicked', self.on_voButton_clicked)

        self.project = project.copy()
        self.vbox.show_all()
        self.set_default_response(Gtk.ResponseType.OK)
        self.on_vo_toggled(voCheckButton)

    def on_vo_toggled(self, widget):
        self.use_vo = widget.get_active()
        self.project_vo_filename_entry.set_sensitive(self.use_vo)
        self.voButton.set_sensitive(self.use_vo)

    def on_voButton_clicked(self, sender):
        dialog = Gtk.FileChooserDialog("Subtitle", self.parent, Gtk.FileChooserAction.OPEN, ("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('Reference Subtitle File')
        filter.add_pattern('*.srt')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ""
        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename == '':
            return
        self.project['voFile'] = filename
        self.project_vo_filename_entry.set_text(filename)

    def on_subtitleButton_clicked(self, sender):
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
        self.project['subFile'] = filename
        self.project_sub_filename_entry.set_text(filename)

    def on_videoButton_clicked(self, sender):
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
        self.project['videoFile'] = filename
        self.project_video_entry.set_text(filename)
        # UPDATE ALL OTHER
        self.project['subFile'] = splitext(filename)[0]+'.srt'
        self.project_sub_filename_entry.set_text(self.project['subFile'])
        self.project['projectFile'] = splitext(filename)[0]+'.prj'
        self.project_filename_entry.set_text(self.project['projectFile'])
        self.project['voFile'] = splitext(filename)[0]+'-vo'+'.srt'
        if self.use_vo:
            self.project_vo_filename_entry.set_text(self.project['voFile'])

    def on_projectButton_clicked(self, sender):
        dialog = Gtk.FileChooserDialog("Project", self.parent, Gtk.FileChooserAction.OPEN, ("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('Project File')
        filter.add_pattern('*.prj')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ""
        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()
        if filename == '':
            return
        self.project['projectFile'] = filename
        self.project_filename_entry.set_text(filename)

    def on_project_filename_entry_change(self, sender):
        self.project['projectFile'] = sender.get_text()

    def on_project_video_entry_change(self, sender):
        self.project['videoFile'] = sender.get_text()

    def on_project_sub_filename_entry_change(self, sender):
        self.project['subFile'] = sender.get_text()

    def on_project_vo_filename_entry_change(self, sender):
        self.project['voFile'] = sender.get_text()
