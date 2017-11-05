import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, Gdk, GObject, GdkX11
from subtitles import timeStamp
from subtitles import subRec
from subutils import ms2ts, is_timestamp, ts2ms

from gcustom.cellRendererText import cCellRendererText
from gcustom.preferencesDialog import cPreferencesDialog
from gcustom.projectSettingsDialog import cProjectSettingsDialog
from gcustom.waveformGenerationDialog import cWaveformGenerationDialog
from gcustom.subCheckerDialog import cSubCheckerDialog
from gcustom.recodeDialog import cRecodeDialog
from gcustom.splitSrtDialog import cSplitSrtDialog
from gcustom.openMenu import cOpenMenu
from gcustom.textEditDialog import cTextEditDialog
from gcustom.searchReplaceDialog import cSearchReplaceDialog
from gcustom.durationChangeDialog import cDurationChangeDialog
from gcustom.timeChangeDialog import cTimeChangeDialog
from gcustom.syncDialog import cSyncDialog
from gcustom.selectionListDialog import cSelectionListDialog
from gcustom.visualSyncDialog import cSyncAudioWidget
from gcustom.autoSyncOtherVersionDialog import cAutoSyncOtherVersionDialog
from gcustom.cVideoWindow import cVideoWindow
from gcustom.cMergeSplitDialog import cMergeSplitDialog

from thesaurus import cThesaurus
from cmediainfo import cMediaInfo
from subfile import srtFile, gen_timestamp_srt_from_source
from os import makedirs, errno
from os.path import join

from history import cHistory
from utils import cPreferences, do_all, filter_markup
from scenedetect import cSceneDetect
from cfile import cfile
import ctypes, platform
import pickle
import appdirs
import sys

def get_parent_button(widget):
    res = widget
    parent = widget
    cnt = 0
    while not (parent is None) and (parent.get_name() != 'GtkButton') and (cnt < 10):
        widget = parent
        parent = widget.get_parent()
        cnt += 1
    return parent if not (parent is None) and parent.get_name() == 'GtkButton' else widget

class Controller:

    resizeEventCounter = 0
    tvSelectionList = []

    def __init__(self, model, view):
        #self.state = {'model': model, 'view': view} # Here we will save all local class variables
        #self.preferences should be a class containing "dialog_run" method that shows the dialog
        self.model = model
        self.view = view

        GObject.type_register(subRec)

        view['undoTB'].set_sensitive(False)
        view['redoTB'].set_sensitive(False)

        self.history = cHistory()

        self.videoWidgetIsSet = False
        self.videoDuration = 0
        self.audioDuration = 0

        try:
            makedirs(appdirs.user_config_dir('xSubEdit', 'jtapps'))
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        # Load Thesaurus
        path = ''

        if cfile('share/thesaurus.pz').exists:
            path = 'share/thesaurus.pz'
        elif cfile('/usr/share/xsubedit/thesaurus.pz').exists:
            path = '/usr/share/xsubedit/thesaurus.pz'
        elif cfile('/usr/local/share/xsubedit/thesaurus.pz').exists:
            path = '/usr/local/share/xsubedit/thesaurus.pz'
        else:
            raise IOError('Cannot find thesaurus.pz')

        view['subtitles'].thesaurus = cThesaurus(path)

        self.preferences = cPreferences(join(appdirs.user_config_dir('xSubEdit', 'jtapps'),'xSubEdit.conf')) #preferences do not go inside self.state

        self.cursorLeftMargin = Gdk.Cursor(Gdk.CursorType.LEFT_SIDE)
        self.cursorRightMargin = Gdk.Cursor(Gdk.CursorType.RIGHT_SIDE)
        view['scale'].set_can_focus(False)

        # Connections
        model.video.playbus.connect('message::eos', self.on_video_finish)
        view.connect('realize', self.on_realized)
        view.connect('delete-event', self.on_quit)
        view.connect('check-resize', self.on_mainwindow_resize)
        view['audio'].connect('right-click', self.on_audio_right_click)
        view['audio'].connect('sub-updated', self.on_audio_sub_updated)
        view['audio'].connect('scroll-event', self.on_audio_mousewheel)
        view['audio'].connect('dragged-sub', self.on_audio_dragged_sub)
        view['audio'].connect('handle-double-click', self.on_audio_handle_double_click)
        view['audio'].connect('vertical-scale-update', self.on_vertical_scale_update)
        view['audio'].connect('tmpSub-update', self.on_audio_tmpSub_update)
        self.active_sub_changed_id = view['audio'].connect('active-sub-changed', self.on_audio_active_sub_changed)
        view['scale'].connect('change-value', self.on_scale_changed)
        view['ACM-CreateHere'].connect('activate', self.on_ACM_CreateHere)
        view['ACM-DeleteSub'].connect('activate', self.on_ACM_DeleteSub)
        view['ACM-SplitHere'].connect('activate', self.on_ACM_SplitHere)
        view['ACM-StickZoom'].connect('toggled', self.on_ACM_StickZoom)
        view['ACM-ResetAudioScale'].connect('activate', self.on_ACM_ResetAudioScale)
        view['subtitles'].connect('button-press-event', self.on_tv_button_press)
        view['subtitles'].connect('button-release-event', self.on_tv_button_release)
        view['subtitles'].connect('realize', self.on_tv_realize)
        view['TVCM-Delete'].connect('activate', self.on_TVCM_Delete)
        view['TVCM-Merge'].connect('activate', self.on_TVCM_Merge)
        view['TVCM-Merge-To-Dialog'].connect('activate', self.on_TVCM_Merge)
        view['TVCM-DurationEdit'].connect('activate', self.on_TVCM_DurationEdit)
        view['TVCM-SyncDialog'].connect('activate', self.on_TVCM_SyncDialog)
        view['TVCM-TimeEditDialog'].connect('activate', self.on_TVCM_TimeEditDialog)
        view['openFileTB'].connect('clicked', self.on_open_button_clicked)
        view['openFileTB'].connect('button-release-event', self.on_open_button_release)
        view['newFileTB'].connect('clicked', self.on_new_button_clicked)
        view['saveFileTB'].connect('clicked', self.on_save_button_clicked)
        view['checkTB'].connect('clicked', self.on_TB_check_clicked)
        view['MergeSplitTB'].connect('clicked', self.on_TB_MergeSplit_clicked)
        view['visualSyncTB'].connect('clicked', self.on_TB_visual_sync)
        view['importSRTTB'].connect('clicked', self.on_TB_import_srt)
        view['subtitles'].connect('key-release-event', self.on_key_release)
        self.tv_cursor_changed_id  = view['subtitles'].connect('cursor_changed', self.on_tv_cursor_changed)
        view['audio'].connect('key-release-event', self.on_key_release)
        view['undoTB'].connect('clicked', self.on_undo_clicked)
        view['redoTB'].connect('clicked', self.on_redo_clicked)
        view['preferencesTB'].connect('clicked', self.preferences_clicked)
        view['audio'].connect('viewpos-update', self.on_audio_pos)
        view['video'].connect('button-release-event', self.on_video_clicked)
        self.history.connect('history-update',  self.on_history_update)
        view['VCM-TwoPassSD'].connect('activate', self.on_VCM, 'VCM-TwoPassSD')
        view['VCM-SceneDetect'].connect('activate', self.on_VCM, 'VCM-SceneDetect')
        view['VCM-StopDetection'].connect('activate', self.on_VCM, 'VCM-StopDetection')
        view['VCM-Detach'].connect('activate', self.on_VCM, 'VCM-Detach')
        view['splitSubsTB'].connect('clicked', self.on_TB_split)
        view['autoSyncOtherVersionTB'].connect('clicked', self.on_autoSyncOtherVersion_clicked)

        model.connect('audio-ready', self.on_audio_ready)
        model.video.connect('position-update', self.on_video_position)
        model.subtitles.connect('buffer-changed', self.on_sub_buffer_changed)

        view['subtitles'].set_model(self.model.subtitles.get_model())
        editSubCell = cCellRendererText(self.view)
        editTimeCell1 = Gtk.CellRendererText()
        editTimeCell2 = Gtk.CellRendererText()
        viewNumberCell = Gtk.CellRendererText()
        viewCountCell = Gtk.CellRendererText()
        viewCountCell.set_property('xalign', 1)
        viewDurationCell = Gtk.CellRendererText()
        viewScoreCell = Gtk.CellRendererText()
        viewInfoCell = Gtk.CellRendererText()
        viewVOCell = Gtk.CellRendererText()
        editSubCell.set_property('editable', 'True')
        editTimeCell1.set_property('editable', 'True')
        editTimeCell2.set_property('editable', 'True')
        column0 = Gtk.TreeViewColumn('N')
        column1 = Gtk.TreeViewColumn('Start Time')
        column2 = Gtk.TreeViewColumn('Stop Time')
        column3 = Gtk.TreeViewColumn('Duration')
        column4 = Gtk.TreeViewColumn('Reference')
        column5 = Gtk.TreeViewColumn('RS')
        column6 = Gtk.TreeViewColumn('Count')
        column7 = Gtk.TreeViewColumn('Subtitle')
        column8 = Gtk.TreeViewColumn('Info')
        column4.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column7.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column8.set_sizing(Gtk.TreeViewColumnSizing.AUTOSIZE)
        column4.set_expand(False)
        column7.set_expand(False)
        column8.set_expand(False)
        column4.set_resizable(True)
        column7.set_resizable(True)
        column8.set_resizable(True)
        column4.set_min_width(50)
        column7.set_min_width(50)
        column8.set_min_width(50)

        view['HCM-N'].connect('toggled', self.on_HCM_toggled, column0)
        view['HCM-StartTime'].connect('toggled', self.on_HCM_toggled, column1)
        view['HCM-StopTime'].connect('toggled', self.on_HCM_toggled, column2)
        view['HCM-Duration'].connect('toggled', self.on_HCM_toggled, column3)
        view['HCM-Reference'].connect('toggled', self.on_HCM_toggled, column4)
        view['HCM-RS'].connect('toggled', self.on_HCM_toggled, column5)
        view['HCM-Count'].connect('toggled', self.on_HCM_toggled, column6)
        view['HCM-Info'].connect('toggled', self.on_HCM_toggled, column8)

        column0.pack_start(viewNumberCell, False)
        column1.pack_start(editTimeCell1, True)
        column2.pack_start(editTimeCell2, True)
        column3.pack_start(viewDurationCell, True)
        column4.pack_start(viewVOCell, True)
        column5.pack_start(viewScoreCell, True)
        column6.pack_start(viewCountCell, True)
        column7.pack_start(editSubCell, True)
        column8.pack_start(viewInfoCell, True)
        column0.add_attribute(viewNumberCell, 'text', 1)
        column1.add_attribute(editTimeCell1, 'markup', 2)
        column2.add_attribute(editTimeCell2, 'markup', 3)
        column3.add_attribute(viewDurationCell, 'markup', 4)
        column4.add_attribute(viewVOCell, 'markup', 5)
        column5.add_attribute(viewScoreCell, 'markup', 7)
        column6.add_attribute(viewCountCell, 'markup', 6)
        column7.add_attribute(editSubCell, 'markup', 8)
        column8.add_attribute(viewInfoCell, 'markup', 9)
        view['subtitles'].append_column(column0)
        view['subtitles'].append_column(column1)
        view['subtitles'].append_column(column2)
        view['subtitles'].append_column(column3)
        view['subtitles'].append_column(column4)
        view['subtitles'].append_column(column5)
        view['subtitles'].append_column(column6)
        view['subtitles'].append_column(column7)
        view['subtitles'].append_column(column8)
        view['subtitles'].get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        view['subtitles'].set_property('rubber-banding', True)
        view['subtitles'].set_search_column(-1)

        editSubCell.connect('edited', self.on_sub_edit)
        editTimeCell1.connect('edited', self.on_time_edit, 1)
        editTimeCell2.connect('edited', self.on_time_edit, 2)

        view['audio'].subtitlesModel = self.model.subtitles

        # Show Main Window
        view.show_all()
        view['subtitles'].grab_focus()
        view['splitSubsTB'].set_property('sensitive', False)
        view['importSRTTB'].set_property('sensitive', False)
        view['checkTB'].set_property('sensitive', False)
        view['visualSyncTB'].set_property('sensitive', False)
        view['autoSyncOtherVersionTB'].set_property('sensitive', False)
        view['saveFileTB'].set_property('sensitive', False)

        # Final initializations
        self.preferences.load()
        if 'Zoom' in self.preferences:
            view['audio'].viewportUpper = 1 / float(self.preferences['Zoom'])
        self.autosaveHandle = None
        view['subtitles'].override_background_color(Gtk.StateFlags.SELECTED, Gdk.RGBA(0.5, 0.5, 0.7, 1))
        if 'subViewSize' in self.preferences and 'audioViewSize' in self.preferences:
            self.view.subtitlesViewSize = self.preferences['subViewSize']
            self.view.audioViewSize = self.preferences['audioViewSize']
            self.view['root-paned-container'].set_position((1 - self.view.subtitlesViewSize) * self.view.height)
            self.view['audio-video-container'].set_position(self.view.audioViewSize * self.view.width)

        self.view['audio'].scenes = self.model.scenes
        self.view['progress-bar'].set_visible(False)

        if 'Maximized' in self.preferences and self.preferences['Maximized']:
            self.view.maximize()

        if 'Video-Detached' in self.preferences and self.preferences['Video-Detached']:
            self.on_VCM(None, 'VCM-Detach')

        try:
            self.scene_detection_twopass = self.preferences['SceneDetect']['TwoPass']
        except:
            self.scene_detection_twopass = True

        self.view['VCM-TwoPassSD'].set_active(self.scene_detection_twopass)

        self.init_done = True

    def on_TB_MergeSplit_clicked(self, sender):
        cMergeSplitDialog(self.view)

    def on_TB_split(self, sender):
        cSplitSrtDialog(self.view, self.model.subFilename, self.model.subtitles.get_sub_list())

    def on_TB_visual_sync(self, sender):
        if not self.has_audio_duration():
            return
        subs = self.model.subtitles.get_sub_list()
        if len(subs) == 0:
            dlg = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, 'No subtitles found to synchronize.')
            dlg.run()
            dlg.destroy()
            return
        for sub in subs:
            sub.startTime_before_sync = int(sub.startTime)
            sub.stopTime_before_sync = int(sub.stopTime)
        slist_before = [(sub, int(sub.startTime), int(sub.stopTime)) for sub in subs]
        self.vSyncWidget = cSyncAudioWidget(self.view.widgets['audio-scale-container'], self.view['audio'])
        self.vSyncWidget.subtitlesModel = self.model.subtitles
        self.vSyncWidget.audioDuration = self.audioDuration / 1000
        self.vSyncWidget.audioModel = self.model.audio
        self.vSyncWidget.sceneModel = self.model.scenes
        self.vSyncWidget.destroy_signal_id = self.vSyncWidget.connect('destroy', self.on_vsync_destroy, slist_before)
        self.view['visualSyncTB'].set_sensitive(False)

    def on_autoSyncOtherVersion_clicked(self, sender):
        cAutoSyncOtherVersionDialog(self.view, self.model.video.videoFilename, self.model.subtitles.get_sub_list())

    def on_vsync_destroy(self, widget, slist_before):
        widget.disconnect(widget.destroy_signal_id)
        subs = self.model.subtitles.get_sub_list()
        if widget.save:
            slist_after = [(sub, int(sub.startTime), int(sub.stopTime)) for sub in subs]
            slist_diff = []
            for i in xrange(len(subs)):
                if slist_before[i][1] != slist_after[i][1] or slist_before[i][2] != slist_after[i][2]:
                    slist_diff.append((subs[i], int(slist_before[i][1]), int(slist_before[i][2]), int(slist_after[i][1]), int(slist_after[i][2])))
            if len(slist_diff) > 0:
                self.history.add(('menu-change-time', slist_diff))
        else:
            for sub in subs:
                sub.startTime = sub.startTime_before_sync
                sub.stopTime = sub.stopTime_before_sync
        self.view['audio'].show()
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()
        self.view['visualSyncTB'].set_sensitive(True)

    def on_VCM(self, widget, option):
        if option == 'VCM-TwoPassSD':
            self.scene_detection_twopass = widget.get_active()
            try:
                self.preferences['SceneDetect']['TwoPass'] = self.scene_detection_twopass
            except:
                self.preferences['SceneDetect'] = {'Auto': False, 'TwoPass': widget.get_active()}
            self.preferences.save()
        elif option == 'VCM-SceneDetect':
            try:
                one_pass = (self.preferences['SceneDetect']['TwoPass'] == False)
            except:
                one_pass = False
            self.scenedetect_start(one_pass)
        elif option == 'VCM-StopDetection' and hasattr(self, 'scenedetect'):
            self.scenedetect.stop()
            self.view['progress-bar'].set_visible(False)
        elif option == 'VCM-Detach':
            sz = None
            pos = None
            if 'Video-Size' in self.preferences:
                sz = self.preferences['Video-Size']
            if 'Video-Position' in self.preferences:
                pos = self.preferences['Video-Position']

            videoWindow = cVideoWindow(self.view, win_size = sz, win_position = pos)
            self.set_video_widget(videoWindow)
            self.view['video'].hide()
            videoWindow.handler_destroy = videoWindow.connect('destroy', self.on_video_window_destroy)
            videoWindow.handler_update_pos = videoWindow.connect('update-pos', self.on_video_window_update_pos)
            videoWindow.handler_update_size = videoWindow.connect('update-size', self.on_video_window_update_size)
            videoWindow.backup_audio_view_size = self.view.audioViewSize
            self.view.audioViewSize = 1
            self.view['audio-video-container'].set_position(self.view.audioViewSize * self.view.width)
            self.preferences['Video-Detached'] = True

    def on_video_window_update_size(self, widget, value):
        self.preferences['Video-Size'] = value

    def on_video_window_update_pos(self, widget, value):
        self.preferences['Video-Position'] = value

    def on_video_window_destroy(self, widget):
        widget.disconnect(widget.handler_destroy)
        widget.disconnect(widget.handler_update_size)
        widget.disconnect(widget.handler_update_pos)
        self.view['video'].show()
        self.set_video_widget(self.view['video'].DrawingArea)
        self.view.audioViewSize = widget.backup_audio_view_size
        self.view['audio-video-container'].set_position(self.view.audioViewSize * self.view.width)
        if widget.close_request:
            self.preferences['Video-Detached'] = False

    def on_HCM_toggled(self, widget, column):
        column.props.visible = widget.get_active()

    def on_tv_realize(self, widget):
        col = self.view['subtitles'].get_columns()
        self.setup_tv_header(col[0],'N')
        self.setup_tv_header(col[1],'Start Time')
        self.setup_tv_header(col[2],'Stop Time')
        self.setup_tv_header(col[3],'Duration')
        self.setup_tv_header(col[4],'Reference')
        self.setup_tv_header(col[5],'RS')
        self.setup_tv_header(col[6],'Count')
        self.setup_tv_header(col[7],'Subtitle')
        self.setup_tv_header(col[8],'Info')

    def setup_tv_header(self, column, text):
        column.props.clickable = True
        label = Gtk.Label(text)
        label.show()
        column.set_widget(label)
        lb = get_parent_button(column.get_widget())
        lb.connect('button-press-event', self.on_header_clicked)

    def on_header_clicked(self, widget, event):
        if event.button == 3:
            self.view['HeaderContextMenu'].popup(None, None, None, None, event.button, event.time)
        return True

    def on_realized(self, widget):
        bg = widget.get_style_context().get_background_color(Gtk.StateType.NORMAL)
        self.view['scale'].override_background_color(Gtk.StateType.NORMAL, bg)

    def on_audio_handle_double_click(self, sender, sub, old_st):
        self.history.add(('edit-stopTime', sub, old_st, int(sub.stopTime)))

    def on_TVCM_TimeEditDialog(self, widget):
        if self.model.subtitles.is_empty():
            return
        changeList = []
        cTimeChangeDialog(self.view, self.model.subtitles, self.view['subtitles'], changeList)
        self.history.add(('menu-change-time', changeList))
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_TVCM_SyncDialog(self, widget):
        if self.model.subtitles.is_empty():
            return
        changeList = []
        cSyncDialog(self.view, self.model.subtitles, self.view['subtitles'], changeList)
        self.history.add(('menu-change-time', changeList))
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_TVCM_DurationEdit(self, widget):
        if self.model.subtitles.is_empty():
            return
        changeList = []
        cDurationChangeDialog(self.view, self.model.subtitles, self.view['subtitles'], changeList)
        self.history.add(('menu-change-time', changeList))
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_audio_tmpSub_update(self, sender):
        if self.view['audio'].tmpSub != None:
            duration = int(self.view['audio'].tmpSub.duration)
            self.view['duration-label'].set_label('Duration: '+str(ms2ts(duration))+'\t\t')

    def on_open_button_release(self, sender,  event):
        if event.button == 3:
            if 'MRU' in self.preferences.keys() and len(self.preferences['MRU'] ) > 0:
                menuObj = cOpenMenu(self.preferences)
                menuObj.handler_select = menuObj.connect('custom-select', self.on_OCM_select)
                menuObj.menu.popup(None, None, None, None, event.button, event.time)
            return True
        else:
            return False

    def on_TB_import_srt(self, widget):
        if not self.has_audio_duration():
            return
        dialog = Gtk.FileChooserDialog('Import SRT', self.view, Gtk.FileChooserAction.OPEN, ('_Cancel', Gtk.ResponseType.CANCEL, '_Open', Gtk.ResponseType.OK))
        dialog.set_current_folder(cfile(self.model.subFilename).abspath)
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('SRT File')
        filter.add_pattern('*.srt')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ''

        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()

        if filename == '':
            return

        subList = srtFile(filename).read_from_file()
        do_all(self.model.subtitles.append, subList)
        self.model.subtitles.load_vo_data(self.model.voReference)
        self.view['audio'].queue_draw()

    def save_subs_info(self):
        subs_info = []
        for row in self.model.subtitles.get_model():
            subs_info.append(row[self.model.subtitles.COL_SUB].info)
        projectData = pickle.load(open(self.model.projectFilename.decode('utf-8'), 'rb'))
        projectData['subs_info'] = subs_info
        projectData['subs_hash'] = self.model.subtitles.calc_hash()
        projectData['scenes'] = self.model.scenes
        pickle.dump(projectData, open(self.model.projectFilename.decode('utf-8'), 'wb'))

    def load_subs_info(self):
        subs_info = []
        projectData = pickle.load(open(self.model.projectFilename.decode('utf-8'), 'rb'))
        if 'subs_info' not in projectData or ('subs_info' in projectData and len(projectData['subs_info']) < len(self.model.subtitles.get_model())):
            return
        subs_info = projectData['subs_info']
        self.model.scenes = projectData['scenes'][:]
        self.view['audio'].scenes = self.model.scenes
        if self.model.subtitles.calc_hash() == projectData['subs_hash']:
            for i, row in enumerate(self.model.subtitles.get_model()):
                for key in subs_info[i]:
                    sub = row[self.model.subtitles.COL_SUB]
                    sub.info = (key, subs_info[i][key])
                    if key == 'Audio-Last_Edited':
                        self.model.subtitles.last_edited = sub
                        path = self.model.subtitles.get_sub_path(sub)
                        if path != None:
                            with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                                self.view['subtitles'].set_cursor(path)
                                self.view['audio'].activeSub = sub
                                self.view['audio'].center_active_sub()

    def on_TB_check_clicked(self, widget):
        if self.model.subtitles.is_empty():
            return
        cSubCheckerDialog(self.view, zip(*self.model.subtitles.get_model())[0]).run()
        self.save_subs_info()

    def on_audio_active_sub_changed(self, widget, sub):
        if sub == None:
            return
        path = self.model.subtitles.get_sub_path(sub)
        if path == None:
            return
        with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
            self.view['subtitles'].set_cursor(path)

    def on_ACM_StickZoom(self, widget):
        self.view['audio'].stickZoom = widget.get_active()

    def on_ACM_ResetAudioScale(self, widget):
        self.view['audio'].scale_linear_audio = 1

    def on_vertical_scale_update(self, widget, value):
        if value == 1:
            self.view['ACM-ResetAudioScale'].hide()
        else:
            self.view['ACM-ResetAudioScale'].show()

    def on_audio_dragged_sub(self, widget, orig_sub, new_sub):
        if orig_sub.startTime != new_sub.startTime:
            self.history.add(('edit-startTime', new_sub, int(orig_sub.startTime), int(new_sub.startTime)))
        if orig_sub.stopTime != new_sub.stopTime:
            self.history.add(('edit-stopTime', new_sub, int(orig_sub.stopTime), int(new_sub.stopTime)))

    def on_audio_right_click(self, widget, event):
        if self.view['audio'].overSub != None:
            if self.view['audio'].overSub == self.view['audio'].tmpSub:
                self.view['ACM-SplitHere'].hide()
                self.view['ACM-DeleteSub'].hide()
                self.view['ACM-CreateHere'].show()
            else:
                self.view['ACM-SplitHere'].show()
                self.view['ACM-DeleteSub'].show()
                self.view['ACM-CreateHere'].hide()
        else:
            self.view['ACM-SplitHere'].hide()
            self.view['ACM-DeleteSub'].hide()
            self.view['ACM-CreateHere'].show()
        self.view['AudioContextMenu'].popup(None, None, None, None, event.button, event.time)

    def on_audio_sub_updated(self, widget, sub):
        res = self.model.voReference.get_subs_in_range(int(sub.startTime), (sub.stopTime))
        sub.vo = '\n'.join(voItem[2].strip() for voItem in res)
        if 'Audio-Warning-Better-RS' in sub.info and sub.rs >= 20:
            sub.info = ('Audio-Warning-Better-RS', (sub.info['Audio-Warning-Better-RS'][0].replace('red', 'black'), []))
        self.view['subtitles'].queue_draw()
        self.check_modified()

    def on_tv_cursor_changed(self, widget):
        if self.model.subtitles.is_empty():
            return
        with GObject.signal_handler_block(self.view['audio'], self.active_sub_changed_id):
            self.view['audio'].activeSub = self.model.subtitles.get_sub_from_path(self.view['subtitles'].get_cursor()[0])
            self.view['duration-label'].set_label('Duration: '+str(self.view['audio'].activeSub.duration)+'\t\t')
            self.view['audio'].center_active_sub()
            self.model.video.pause()
            self.model.video.set_videoPosition(self.view['audio'].videoSegment[0])
            self.model.video.set_segment(self.view['audio'].videoSegment)

    def set_video_widget(self, _widget = None):
        if self.videoWidgetIsSet and _widget is None :
            return
        self.videoWidgetIsSet = True
        widget = self.view['video'].DrawingArea if _widget is None else _widget
        video = widget.get_property('window')
        if platform.system() == 'Windows':
            if not video.ensure_native():
                print('Error: Video playback requires a native window.')
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object]
            drawingarea_gpointer = ctypes.pythonapi.PyCapsule_GetPointer(video.__gpointer__, None)
            gdkdll = ctypes.CDLL('libgdk-3-0.dll')
            widget._xid = gdkdll.gdk_win32_window_get_handle(drawingarea_gpointer)
        else:
            widget._xid = widget.get_property('window').get_xid()
        self.model.video.set_video_widget(widget)

    def on_sub_buffer_changed(self, sender):
        self.view['audio'].invalidateCanvas()

    def on_update_audio_duration(self, sender, value):
        self.audioDuration = value
        self.model.video.set_duration(value)
        self.view['audio'].audioDuration = value / 1000
        self.view['audio'].queue_draw()

    def preferences_clicked(self, sender):
        prefs = cPreferencesDialog(self.view, self.preferences.get_data(), (self.view['audio'].viewportLower, self.view['audio'].viewportUpper))
        res = prefs.run()
        if res == Gtk.ResponseType.OK:
            self.preferences.set_data(prefs.preferences)
            curVH = self.view['audio'].viewportUpper
            curVL = self.view['audio'].viewportLower
            midV = curVL + (curVH - curVL) / 2.0
            diff = 1 / self.preferences['Zoom']
            self.view['audio'].viewportLower = midV - diff / 2.0
            self.view['audio'].viewportUpper = midV + diff / 2.0
            self.preferences.save()
        prefs.destroy()

    def on_quit(self, sender, event):
        if self.model.subtitles.is_changed():
            save_changes_dialog = Gtk.Dialog("Save Changes", self.view, Gtk.DialogFlags.MODAL, ("_NO", Gtk.ResponseType.CANCEL, "_YES", Gtk.ResponseType.OK))
            box = save_changes_dialog.get_content_area()
            box.add(Gtk.Label("Do you want to save the subtitle?"))
            box.show_all()
            res = save_changes_dialog.run()
            if res == Gtk.ResponseType.OK:
                self.on_save_button_clicked(None)
            else:
                self.save_subs_info()
            save_changes_dialog.destroy()
        else:
            if self.has_audio_duration():
                self.save_subs_info()

        if hasattr(self, 'scenedetect'):
            self.scenedetect.stop()

        self.preferences['Maximized'] = self.view.props.is_maximized
        self.preferences.save()

        Gtk.main_quit()

    def hist_back(self):
        if self.history.is_empty() or self.history.is_at_first_element():
            return
        curHistItem = self.history.back()
        if curHistItem[0] == 'menu-change-time':
            for item in curHistItem[1]:
                item[0].startTime = int(item[1])
                item[0].stopTime = int(item[2])
        if curHistItem[0] == 'replace-text':
            curHistItem[1].text = curHistItem[2]
        if curHistItem[0] == 'edit-text':
            curHistItem[1].text = curHistItem[2]
        if curHistItem[0] == 'edit-startTime':
            curHistItem[1].startTime = int(curHistItem[2])
            self.view['audio'].activeSub = curHistItem[1]
        if curHistItem[0] == 'edit-stopTime':
            curHistItem[1].stopTime = curHistItem[2]
            self.view['audio'].activeSub = curHistItem[1]
        if curHistItem[0] == 'append':
            treeselection = self.view['subtitles'].get_selection()
            treeselection.unselect_all()
            with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                self.model.subtitles.remove_sub(curHistItem[1])
        if curHistItem[0] == 'delete':
            for sub in curHistItem[1]:
                self.model.subtitles.append(sub)
                self.view['audio'].activeSub = sub
        if curHistItem[0] == 'merge':
            treeselection = self.view['subtitles'].get_selection()
            treeselection.unselect_all()
            with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                self.model.subtitles.remove_sub(curHistItem[2])
            last_added = None
            for sub in curHistItem[1]:
                self.model.subtitles.append(sub)
                last_added = sub
            if last_added != None:
                self.view['audio'].activeSub = last_added
        if curHistItem[0] == 'split':
            self.model.subtitles.remove_sub(curHistItem[2])
            curHistItem[1].stopTime = curHistItem[3]
            self.view['audio'].activeSub = curHistItem[1]

        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def hist_forward(self):
        if self.history.is_at_last_element() or self.history.is_empty():
            return
        curHistItem = self.history.forward()
        if curHistItem[0] == 'menu-change-time':
            for item in curHistItem[1]:
                item[0].startTime = int(item[3])
                item[0].stopTime = int(item[4])
        if curHistItem[0] == 'replace-text':
            curHistItem[1].text = curHistItem[3]
        if curHistItem[0] == 'edit-text':
            curHistItem[1].text = curHistItem[3]
        if curHistItem[0] == 'edit-startTime':
            curHistItem[1].startTime = curHistItem[3]
            self.view['audio'].activeSub = curHistItem[1]
        if curHistItem[0] == 'edit-stopTime':
            curHistItem[1].stopTime = curHistItem[3]
            self.view['audio'].activeSub = curHistItem[1]
        if curHistItem[0] == 'append':
            self.model.subtitles.append(curHistItem[1])
            self.view['audio'].activeSub = curHistItem[1]
        if curHistItem[0] == 'delete':
            treeselection = self.view['subtitles'].get_selection()
            treeselection.unselect_all()
            with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                for sub in curHistItem[1]:
                    self.model.subtitles.remove_sub(sub)
            self.view['audio'].activeSub = None
        if curHistItem[0] == 'merge':
            treeselection = self.view['subtitles'].get_selection()
            treeselection.unselect_all()
            with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                for sub in curHistItem[1]:
                    self.model.subtitles.remove_sub(sub)
            self.model.subtitles.append(curHistItem[2])
            self.view['audio'].activeSub = curHistItem[2]
        if curHistItem[0] == 'split':
            curHistItem[1].stopTime = curHistItem[4]
            self.model.subtitles.append(curHistItem[2])
            self.view['audio'].activeSub = curHistItem[1]

        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_undo_clicked(self, sender):
        self.hist_back()
        self.view['subtitles'].queue_draw()
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_redo_clicked(self, sender):
        self.hist_forward()
        self.view['subtitles'].queue_draw()
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()

    def on_history_update(self,  sender,  state):
        if state == self.history.HIST_EMPTY:
            self.view['undoTB'].set_sensitive(False)
            self.view['redoTB'].set_sensitive(False)
        if state == self.history.HIST_AT_LAST_ELEMENT:
            self.view['undoTB'].set_sensitive(True)
            self.view['redoTB'].set_sensitive(False)
        if state == self.history.HIST_AT_INTERMEDIATE_ELEMENT:
            self.view['undoTB'].set_sensitive(True)
            self.view['redoTB'].set_sensitive(True)
        if state == self.history.HIST_AT_FIRST_ELEMENT:
            self.view['undoTB'].set_sensitive(False)
            self.view['redoTB'].set_sensitive(True)

    def on_key_release_vsync(self, widget, event):
        if event.keyval in [Gdk.KEY_F12, Gdk.KEY_F, Gdk.KEY_f, 2006, 2038] and not event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.vSyncWidget.audioDuration == 0:
                return
            if self.model.video.is_playing():
                self.model.video.pause()
            else:
                self.model.video.set_videoPosition(self.vSyncWidget.videoSegment[0])
                self.model.video.set_segment((self.vSyncWidget.videoSegment[0], self.vSyncWidget.audioDuration))
                self.model.video.play()
        elif event.keyval == Gdk.KEY_F1:
            if self.vSyncWidget.audioDuration == 0:
                return
            self.model.video.set_videoPosition(self.vSyncWidget.videoSegment[0])
            self.model.video.set_segment(self.vSyncWidget.videoSegment)
            self.model.video.play()
        elif event.keyval == Gdk.KEY_Escape:
            self.model.video.pause()

    def on_key_release_base(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.model.video.pause()

    def on_key_release_normal(self, widget, event):
        if event.keyval == Gdk.KEY_F5:
            if self.view['audio'].activeSub == None:
                posts = timeStamp(int(self.view['audio'].cursor))
                prev = self.model.subtitles.get_sub_before_timeStamp(posts)
            else:
                if len(self.tvSelectionList) > 1:
                    prev = self.model.subtitles.get_prev(self.tvSelectionList[0])
                else:
                    prev  = self.model.subtitles.get_prev(self.view['audio'].activeSub)
            if prev == None:
                return
            self.view['audio'].activeSub = prev
            path = self.model.subtitles.get_sub_path(prev)
            self.model.video.set_videoPosition(self.view['audio'].videoSegment[0])
            if path != None:
                self.view['subtitles'].set_cursor(path)
                self.model.video.set_segment((int(self.view['audio'].activeSub.startTime), int(self.view['audio'].activeSub.stopTime)))
            self.view['duration-label'].set_label('Duration: '+str(self.view['audio'].activeSub.duration)+'\t\t')
            self.view['audio'].queue_draw()
            self.model.video.set_segment(self.view['audio'].videoSegment)
            self.model.video.play()
        elif event.keyval in [Gdk.KEY_F12, Gdk.KEY_F, Gdk.KEY_f, 2006, 2038] and not event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.view['audio'].audioDuration == 0:
                return
            if self.model.video.is_playing():
                self.model.video.pause()
            else:
                self.model.video.set_videoPosition(self.view['audio'].videoSegment[0])
                self.model.video.set_segment((self.view['audio'].videoSegment[0],  self.view['audio'].audioDuration))
                self.model.video.play()
        elif event.keyval in [Gdk.KEY_p,  Gdk.KEY_P, 2000, 2032]:
            if self.view['audio'].audioDuration == 0:
                return
            if self.model.video.is_playing():
                self.model.video.pause()
            else:
                self.model.video.set_videoPosition(self.view['audio'].pos)
                self.model.video.set_segment((self.view['audio'].pos, self.view['audio'].audioDuration))
                self.model.video.play()
        elif event.keyval == Gdk.KEY_F6:
            if self.view['audio'].activeSub == None:
                posts = timeStamp(int(self.view['audio'].cursor))
                nexts = self.model.subtitles.get_sub_after_timeStamp(posts)
            else:
                if len(self.tvSelectionList) > 1:
                    nexts = self.model.subtitles.get_next(self.tvSelectionList[-1])
                else:
                    nexts = self.model.subtitles.get_next(self.view['audio'].activeSub)
            if nexts == None:
                return
            self.view['audio'].activeSub = nexts
            path = self.model.subtitles.get_sub_path(nexts)
            self.model.video.set_videoPosition(self.view['audio'].videoSegment[0])
            if path != None:
                self.view['subtitles'].set_cursor(path)
                self.model.video.set_segment((int(self.view['audio'].activeSub.startTime), int(self.view['audio'].activeSub.stopTime)))
            self.view['duration-label'].set_label('Duration: '+str(self.view['audio'].activeSub.duration)+'\t\t')
            self.view['audio'].queue_draw()
            self.model.video.set_segment(self.view['audio'].videoSegment)
            self.model.video.play()
        elif event.keyval == Gdk.KEY_F1:
            if not self.has_audio_duration():
                return
            self.model.video.set_videoPosition(self.view['audio'].videoSegment[0])
            self.model.video.set_segment(self.view['audio'].videoSegment)
            self.model.video.play()
        elif (event.keyval in [Gdk.KEY_Z, Gdk.KEY_z, 2022, 1990]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            if event.state & Gdk.ModifierType.SHIFT_MASK:
                self.hist_forward()
            else:
                self.hist_back()
        elif (event.keyval in [Gdk.KEY_Y, Gdk.KEY_y, 2037, 2005]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.hist_forward()
        elif (event.keyval == Gdk.KEY_O or event.keyval == Gdk.KEY_o) and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.on_open_button_clicked(None)
        elif (event.keyval in [Gdk.KEY_S, Gdk.KEY_s, 2034, 2002]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.on_save_button_clicked(None)
        elif (event.keyval == Gdk.KEY_N or event.keyval == Gdk.KEY_n) and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.on_new_button_clicked(None)
        elif (event.keyval in [Gdk.KEY_F, Gdk.KEY_f, 2038, 2006]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            if self.model.subtitles.is_empty():
                return
            cSearchReplaceDialog(self.view, self.view['subtitles'], self.model.subtitles, self.history)
        elif (event.keyval in [Gdk.KEY_plus, Gdk.KEY_KP_Add]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            audio = self.view['audio']
            if audio.audioDuration == 0:
                return
            cr = audio.cursor
            if audio.lowms > cr or audio.highms < cr:
                pointx = int(audio.get_allocation().width / 2)
            else:
                pointx = int(((cr - audio.lowms) / float(audio.highms - audio.lowms)) * audio.get_allocation().width)
            audio.zoom(Gdk.ScrollDirection.UP, pointx)
        elif (event.keyval in [Gdk.KEY_minus, Gdk.KEY_KP_Subtract]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            audio = self.view['audio']
            if audio.audioDuration == 0:
                return
            cr = audio.cursor
            if audio.lowms > cr or audio.highms < cr:
                pointx = int(audio.get_allocation().width / 2)
            else:
                pointx = int(((cr - audio.lowms) / float(audio.highms - audio.lowms)) * audio.get_allocation().width)
            audio.zoom(Gdk.ScrollDirection.DOWN, pointx)
        elif (event.keyval  == Gdk.KEY_Delete):
            self.on_TVCM_Delete(None)
        elif (event.keyval in [Gdk.KEY_G, Gdk.KEY_g]):
            for i, row in enumerate(self.model.subtitles.get_model()):
                sub = row[self.model.subtitles.COL_SUB]
                for key in sub.info:
                    if key != 'Audio-Last_Edited':
                        continue
                    path = self.model.subtitles.get_sub_path(sub)
                    if path is None:
                        break
                    with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                        self.view['subtitles'].set_cursor(path)
                        self.view['audio'].activeSub = sub
                        self.view['audio'].center_active_sub()
                    break

    def on_key_release(self, widget, event):
        self.on_key_release_base(widget, event)
        if hasattr(self, 'vSyncWidget') and self.vSyncWidget.props.visible:
            self.on_key_release_vsync(widget, event)
        else:
            self.on_key_release_normal(widget, event)

    def on_new_button_clicked(self, widget):
        self.set_video_widget()
        dialog = cProjectSettingsDialog(self.view, {'videoFile': '', 'subFile': '', 'projectFile': '', 'voFile': '', 'subPolicy': 'Normal'})
        res = dialog.run()
        projectFiles = None
        if res == Gtk.ResponseType.OK:
            projectFiles = dialog.project.copy()
            if not(dialog.use_vo):
                projectFiles['voFile'] = ''
        dialog.destroy()
        if projectFiles != None:
            refpath = cfile(projectFiles['projectFile']).abspath
            projectFiles['videoFile'] = cfile(projectFiles['videoFile'], refpath = refpath).relfull
            projectFiles['subFile'] = cfile(projectFiles['subFile'], refpath = refpath).relfull
            projectFiles['voFile'] = cfile(projectFiles['voFile'], refpath = refpath).relfull
            tmp = cfile(projectFiles['videoFile'])
            tmp.change_ext('.pkf')
            projectFiles['peakFile'] = tmp.relfull
            self.model.projectFilename = projectFiles['projectFile']
            self.view.set_title( cfile(projectFiles['videoFile']).base )

            orig_video = cfile(projectFiles['videoFile'], refpath = refpath).full_path
            tmpstr = self.check_video_file_compatibility( cfile(projectFiles['videoFile'], refpath = refpath).full_path )
            projectFiles['videoFile'] = tmpstr
            pickle.dump(projectFiles, open(projectFiles['projectFile'].decode('utf-8'), 'wb'))

            projectFiles['videoFile'] = cfile( projectFiles['videoFile'], refpath = refpath).full_path
            projectFiles['peakFile'] = cfile(projectFiles['peakFile'], refpath = refpath).full_path
            subfile = cfile(projectFiles['subFile'], refpath = refpath)
            projectFiles['subFile'] = subfile.full_path
            vofile = cfile(projectFiles['voFile'], refpath = refpath)
            projectFiles['voFile'] = vofile.full_path
            if projectFiles['videoFile'] != '':
                self.model.video.set_video_filename(projectFiles['videoFile'])
            self.model.peakFilename = projectFiles['peakFile']
            self.model.subFilename = projectFiles['subFile']
            self.model.voFilename = projectFiles['voFile']

            self.preferences.update_mru(projectFiles['projectFile'])
            self.preferences.save()

            if not cfile(projectFiles['peakFile']).exists:
                wgDialog = cWaveformGenerationDialog(self.view, orig_video, self.model.peakFilename)
                wgDialog.run()

            self.model.get_waveform()
            self.on_update_audio_duration(None, self.model.audioDuration)

            if vofile.filename != '':
                if not vofile.exists and subfile.exists:
                    cfile(projectFiles['subFile']).copy(vofile.full_path)

            self.model.subtitles.clear()
            backup = subfile.obj_copy()
            backup.change_base(backup.base + '-original-backup')
            spol = projectFiles['subPolicy']

            if subfile.exists:
                if spol == 'Normal':
                    subs = srtFile(subfile.full_path).read_from_file()
                    do_all(self.model.subtitles.append, subs)
                    self.model.subtitles.clear_all_modified_timestamps()
                elif spol == 'Timestamps':
                    subfile.copy(backup)
                    gen_timestamp_srt_from_source(backup.full_path, subfile.full_path)
                    subs = srtFile(subfile.full_path).read_from_file()
                    do_all(self.model.subtitles.append, subs)
                    self.model.subtitles.clear_all_modified_timestamps()
                elif spol == 'Empty':
                    subfile.copy(backup)
                    subfile.delete()
                    subfile.touch()
            if spol == 'Fill_VO' and vofile.exists:
                if subfile.exists:
                    subfile.copy(backup)
                vofile.copy(subfile)
                subs = srtFile(subfile.full_path).read_from_file()
                do_all(self.model.subtitles.append, subs)
                self.model.subtitles.clear_all_modified_timestamps()
                self.view['audio'].queue_draw()

            if projectFiles['voFile'] != '' and vofile.exists:
                self.open_vo(vofile.full_path)

                if self.preferences['Autosave']:
                    if self.autosaveHandle:
                        GObject.source_remove(self.autosaveHandle)
                        self.autosaveHandle = None
                    self.autosaveHandle = GObject.timeout_add_seconds(60, self.autosave)

            if vofile.filename == '':
                referenceCol = self.view['subtitles'].get_columns()[4]
                referenceCol.props.visible = False
                self.view['HCM-Reference'].set_active(False)

            try:
                tmpv = self.preferences['SceneDetect']['Auto']
                one_pass = (self.preferences['SceneDetect']['TwoPass'] == False)
            except:
                tmpv = False
                one_pass = False
            if tmpv:
                self.scenedetect_start(one_pass)
            self.view['subtitles'].queue_draw()

    def scenedetect_start(self, _one_pass):
        self.scenedetect = cSceneDetect(self.model.video.videoFilename, one_pass = _one_pass)
        self.scenedetect.connect('finish', self.scenedetect_finish)
        self.scenedetect.connect('detect', self.scenedetect_detect)
        self.scenedetect.connect('progress', self.scenedetect_progress)
        self.view['progress-bar'].set_visible(True)
        self.scenedetect.start()

    def scenedetect_finish(self, sender):
        self.view['progress-bar'].set_visible(False)
        self.save_subs_info()

    def scenedetect_progress(self, sender, percent):
        self.view['progress-bar'].set_fraction(percent)

    def scenedetect_detect(self, sender, pos):
        if not pos in self.model.scenes:
            self.model.scenes.append(pos)
            self.view['audio'].invalidateCanvas()
            self.view['audio'].queue_draw()

    def autosave(self):
        if self.model.subtitles.is_changed():
            self.on_save_button_clicked(None)
        return True

    def open_srt(self, filename):
        if not cfile(filename).exists:
            return
        self.model.subFilename = filename
        subs = srtFile(self.model.subFilename).read_from_file()
        self.model.subtitles.clear()
        do_all(self.model.subtitles.append, subs)
        self.model.subtitles.clear_all_modified_timestamps()
        self.view['audio'].queue_draw()
        if self.preferences['Autosave']:
            if self.autosaveHandle:
                GObject.source_remove(self.autosaveHandle)
                self.autosaveHandle = None
            self.autosaveHandle = GObject.timeout_add_seconds(60, self.autosave)

    def open_vo(self, filename):
        if not cfile(filename).exists or filename == '':
            return
        self.model.voFilename = filename
        subs = srtFile(self.model.voFilename.decode('utf-8')).read_from_file()
        self.model.voReference.set_data(subs)
        self.model.subtitles.load_vo_data(self.model.voReference)
        self.model.voReference.filename = filename

    def open_pkf(self, filename):
        if not cfile(filename).exists:
            wgDialog = cWaveformGenerationDialog(self.view, self.model.video.videoFilename, self.model.peakFilename)
            wgDialog.run()
        self.model.get_waveform()
        self.on_update_audio_duration(None, self.model.audioDuration)

    def open_project(self, filename):
        self.set_video_widget()
        self.preferences.update_mru(filename)
        self.preferences.save()

        self.model.projectFilename = filename
        refpath = cfile(filename).abspath

        projectData = pickle.load(open(filename.decode('utf-8'), 'rb'))
        self.model.video.set_video_filename( cfile(projectData['videoFile'], refpath = refpath).full_path )
        self.model.peakFilename = cfile(projectData['peakFile'], refpath = refpath).full_path
        self.model.subFilename = cfile(projectData['subFile'], refpath = refpath).full_path
        self.model.voFilename = cfile(projectData['voFile'], refpath = refpath).full_path

        self.view.set_title( cfile(projectData['videoFile']).base + ' - ' + self.view.prog_title )

        self.open_pkf(self.model.peakFilename)
        self.open_srt(self.model.subFilename)
        self.open_vo(self.model.voFilename)
        self.load_subs_info()
        self.model.subtitles.clear_changed()
        self.check_modified()

        if projectData['voFile'] == '':
            referenceCol = self.view['subtitles'].get_columns()[4]
            referenceCol.props.visible = False
            self.view['HCM-Reference'].set_active(False)

        self.view['splitSubsTB'].set_sensitive(True)
        self.view['importSRTTB'].set_sensitive(True)
        self.view['checkTB'].set_sensitive(True)
        self.view['visualSyncTB'].set_sensitive(True)
        self.view['autoSyncOtherVersionTB'].set_sensitive(True)
        self.view['saveFileTB'].set_sensitive(True)

    def on_OCM_select(self, sender, result):
        sender.disconnect(sender.handler_select)
        if cfile(result).exists:
            self.open_project(result)

    def on_open_button_clicked(self, widget):
        dialog = Gtk.FileChooserDialog('Open Project', self.view, Gtk.FileChooserAction.OPEN, ('_Cancel', Gtk.ResponseType.CANCEL, '_Open', Gtk.ResponseType.OK))
        dialog.set_default_response(Gtk.ResponseType.OK)
        filter = Gtk.FileFilter()
        filter.set_name('Project File')
        filter.add_pattern('*.prj')
        dialog.add_filter(filter)
        res = dialog.run()
        filename = ''

        if res == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
        dialog.destroy()

        if filename == '':
            return

        self.open_project(filename)

    def on_TVCM_Delete(self, widget):
        self.history.add(('delete', self.tvSelectionList[:]))
        self.view['audio'].activeSub = None
        with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
            do_all(self.model.subtitles.remove_sub, self.tvSelectionList)
        treeselection = self.view['subtitles'].get_selection()
        treeselection.unselect_all()
        self.view['audio'].queue_draw()

    def on_TVCM_Merge(self, widget):
        merged = subRec(int(self.tvSelectionList[0].startTime), int(self.tvSelectionList[-1].stopTime),'')
        if widget.get_label() == 'Merge Subtitles':
            merged.text = '\n'.join(sub.text for sub in self.tvSelectionList)
        else:
            merged.text = '\n'.join('- ' + sub.text for sub in self.tvSelectionList)
        treeselection = self.view['subtitles'].get_selection()
        treeselection.unselect_all()
        with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
            do_all(self.model.subtitles.remove_sub, self.tvSelectionList)
        self.history.add(('merge', self.tvSelectionList[:], merged))
        self.tvSelectionList = []
        merged.vo = '\n'.join(line[2].strip() for line in self.model.voReference.get_subs_in_range(merged.startTime, merged.stopTime))
        self.model.subtitles.append(merged)
        self.view['audio'].activeSub = merged
        self.view['audio'].queue_draw()

    def on_tv_button_release(self, widget, event):
        if self.model.subtitles.is_empty():
            return

        (model, pathlist) = widget.get_selection().get_selected_rows()
        self.tvSelectionList= []
        for path in pathlist:
            tree_iter = model.get_iter(path)
            self.tvSelectionList.append(model.get_value(tree_iter, 0))

        if len(self.tvSelectionList ) > 1:
            self.model.video.pause()
            startTime = self.tvSelectionList[0].startTime
            stopTime = self.tvSelectionList[0].stopTime
            duration = 0
            for sub in self.tvSelectionList:
                startTime = startTime if sub.startTime > startTime else sub.startTime
                stopTime = stopTime if sub.stopTime < stopTime else sub.stopTime
                duration += int(sub.duration)
            self.view['audio'].center_multiple_active_subs(startTime, stopTime)
            self.view['duration-label'].set_label('Duration: '+str(ms2ts(duration))+'\t\t')

    def on_tv_button_press(self, widget, event):
        if event.button == 1 and event.type == Gdk.EventType._2BUTTON_PRESS:
            res = self.view['subtitles'].get_path_at_pos(event.x, event.y)
            if res is None:
                return
            if self.view['subtitles'].get_column(8) == res[1]:
                sub = self.model.subtitles.get_sub_from_path(res[0])
                dialog = cTextEditDialog(self.view, sub, 'info', self.view['subtitles'].thesaurus)
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    self.history.add(('edit-text', sub, sub.text, dialog.text))
                    if sub.text != dialog.text:
                        sub.info = {}
                    sub.text = dialog.text
                    self.view['audio'].invalidateCanvas()
                    self.view['audio'].queue_draw()
                dialog.destroy()
                # Change sub info color
                for key in sub.info:
                    if key.startswith('Audio'):
                        sub.info = (key, (sub.info[key][0].replace('red', 'black').replace('orange', 'black'), []))
                self.save_subs_info()

            if self.view['subtitles'].get_column(4) == res[1]:
                sub = self.model.subtitles.get_sub_from_path(res[0])
                voIdxList = self.model.voReference.get_indexes_in_range(sub.startTime, sub.stopTime)
                voList = [self.model.voReference.get_line(idx) for idx in voIdxList]
                if len(voList) > 1:
                    dialog = cSelectionListDialog(self.view, [item[3] for item in voList], title = 'Select VO Line', header_title = 'Lines')
                    dialog.run()
                    if dialog.result == None:
                        return
                    editIdx = dialog.result
                    dialog.destroy()
                else:
                    editIdx = 0
                tmpSub = subRec(voList[editIdx][1], voList[editIdx][2], voList[editIdx][3])
                edit = cTextEditDialog(self.view, tmpSub, 'copy', self.view['subtitles'].thesaurus) # Thesaurus should really be at the model, not on a view oject
                response = edit.run()
                if response == Gtk.ResponseType.OK and self.model.voReference.text_data[voList[editIdx][0]] != edit.text:
                    self.model.voReference.text_data[voList[editIdx][0]] = edit.text
                    vo_res = self.model.voReference.get_subs_in_range(int(sub.startTime), (sub.stopTime))
                    sub.vo = '\n'.join(voItem[2].strip() for voItem in vo_res)
                    self.view['audio'].invalidateCanvas()
                    self.view['audio'].queue_draw()
                    self.model.voReference.save()
                edit.destroy()

        if event.button == 3:
            res = self.view['subtitles'].get_path_at_pos(event.x, event.y)
            if res is None:
                return
            if res[1] in [self.view['subtitles'].get_column(1), self.view['subtitles'].get_column(2), self.view['subtitles'].get_column(3)]:
                self.view['TVCM-DurationEdit'].show()
                self.view['TVCM-TimeEditDialog'].show()
                self.view['TVCM-SyncDialog'].show()
            else:
                self.view['TVCM-SyncDialog'].hide()
                self.view['TVCM-TimeEditDialog'].hide()
                self.view['TVCM-DurationEdit'].hide()

            if len(self.tvSelectionList) == 0:
                return True

            if len(self.tvSelectionList) == 1:
                self.view['TVCM-Merge'].hide()
                self.view['TVCM-Merge-To-Dialog'].hide()
                self.view['TVCM-Delete'].show()
            else:
                consecutive = True
                for i in xrange(1, len(self.tvSelectionList)):
                    if self.model.subtitles.get_prev(self.tvSelectionList[i]) != self.tvSelectionList[i-1]:
                        consecutive = False
                if consecutive:
                    self.view['TVCM-Merge'].show()
                    self.view['TVCM-Merge-To-Dialog'].show()
                    self.view['TVCM-Delete'].show()
                else:
                    self.view['TVCM-Merge'].hide()
                    self.view['TVCM-Merge-To-Dialog'].hide()
                    self.view['TVCM-Delete'].show()

            self.view['TVContextMenu'].popup(None, None, None, None, event.button, event.time)
            return True

    def check_modified(self):
        caption = self.view.get_title()
        if not self.model.subtitles.is_changed():
            if caption[-2:] == ' *':
                self.view.set_title(caption[:-2])
        else:
            if caption[-2:] != ' *':
                self.view.set_title(caption+' *')

    def on_sub_edit(self, renderer, row, newText):
        sub = self.model.subtitles.get_sub(row)
        self.history.add(('edit-text', sub, sub.text, newText.decode('utf-8')))
        sub.text = newText.decode('utf-8')
        self.check_modified()

    def on_time_edit(self, renderer, row, newText, col):
        if not is_timestamp(newText):
            return
        sub = self.model.subtitles.get_sub(row)
        prevSub = self.model.subtitles.get_prev(sub)
        nextSub = self.model.subtitles.get_next(sub)
        if (prevSub != None and timeStamp(newText) < prevSub.stopTime) or (nextSub != None and timeStamp(newText) > nextSub.startTime) or (ts2ms(newText) <= 0):
            return
        if col == 1:
            self.history.add(('edit-startTime', sub, int(sub.startTime), newText))
            sub.startTime = newText
        elif col == 2:
            self.history.add(('edit-stopTime', sub, int(sub.stopTime), newText))
            sub.stopTime = newText
        self.view['audio'].invalidateCanvas()
        self.view['audio'].queue_draw()
        self.check_modified()

    def on_ACM_CreateHere(self, widget):
        if self.view['audio'].tmpSub != None and self.view['audio'].overSub == self.view['audio'].tmpSub:
            sub = subRec(int(self.view['audio'].tmpSub.startTime), int(self.view['audio'].tmpSub.stopTime),'')
            self.view['audio'].tmpSub = None
            vo_res = self.model.voReference.get_subs_in_range(int(sub.startTime), (sub.stopTime))
            sub.vo = '\n'.join(voItem[2].strip() for voItem in vo_res)
            self.model.subtitles.append(sub)
            self.history.add(('append', sub))
        else:
            mouse_msec = self.view['audio'].get_mouse_msec(self.view['audio'].mouse_last_click_coords[0])
            prevSub = self.model.subtitles.get_sub_before_timeStamp(mouse_msec)
            prevSub = prevSub if prevSub != None else subRec(0, 0, '')
            nextSub = self.model.subtitles.get_sub_after_timeStamp(mouse_msec)
            nextSub = nextSub if nextSub != None else subRec(self.view['audio'].audioDuration, self.view['audio'].audioDuration,'')
            lowLimit = int(mouse_msec if mouse_msec > prevSub.stopTime + 120 else prevSub.stopTime + 120)
            highLimit = int(mouse_msec + 1000 if mouse_msec + 1000 < nextSub.startTime - 120 else nextSub.startTime - 120)
            if highLimit - lowLimit < 1000:
                missingDuration = 1000 - (highLimit - lowLimit)
                if (lowLimit == int(prevSub.stopTime) + 120) and (highLimit < int(nextSub.startTime)):
                    highLimit = int(highLimit + missingDuration if highLimit + missingDuration < nextSub.startTime - 120 else nextSub.startTime - 120)
                if (lowLimit > int(prevSub.stopTime)) and (highLimit == int(nextSub.startTime) - 120):
                    lowLimit = int(lowLimit - missingDuration if lowLimit - missingDuration > prevSub.stopTime + 120 else prevSub.stopTime + 120)
            if abs(highLimit - lowLimit) <= 120:
                return
            newSub = subRec(lowLimit, highLimit, '')
            newSub.vo = '\n'.join(voItem[2].strip() for voItem in self.model.voReference.get_subs_in_range(int(newSub.startTime), (newSub.stopTime)))
            self.model.subtitles.append(newSub)
            self.view['audio'].activeSub = newSub
            self.history.add(('append', newSub))
        self.view['audio'].queue_draw()
        self.check_modified()

    def on_ACM_DeleteSub(self, widget):
        self.history.add(('delete', [self.view['audio'].overSub]))
        self.view['audio'].activeSub = None
        with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
            self.model.subtitles.remove_sub(self.view['audio'].overSub)
        treeselection = self.view['subtitles'].get_selection()
        treeselection.unselect_all()
        self.view['audio'].queue_draw()
        self.check_modified()

    def on_ACM_SplitHere(self, widget):
        sub = self.view['audio'].overSub
        mouse_msec = self.view['audio'].get_mouse_msec(self.view['audio'].mouse_last_click_coords[0])
        if int(mouse_msec - 120) <= int(sub.startTime):
            return
        newSub = subRec(int(mouse_msec), int(sub.stopTime), sub.text)
        self.history.add(('split', sub, newSub, int(sub.stopTime), int(mouse_msec - 120)))
        sub.stopTime = int(mouse_msec - 120)
        newSub.vo = '\n'.join(line[2].strip() for line in self.model.voReference.get_subs_in_range(int(newSub.startTime), int(newSub.stopTime)))
        self.model.subtitles.append(newSub)
        self.view['audio'].activeSub = sub
        self.view['audio'].queue_draw()
        self.check_modified()

    def on_audio_pos(self, sender, pos):
        self.view['scale'].set_value(pos)

    def on_scale_changed(self, widget, scroll, value):
        wg = self.view['audio']
        if hasattr(self, 'vSyncWidget') and self.vSyncWidget.props.visible:
            wg = self.vSyncWidget
        posValue = value if value <= 100 else 100
        posValue = posValue if posValue >= 0 else 0
        lower = wg.viewportLower * 100
        upper = wg.viewportUpper * 100
        if posValue + abs(upper - lower) > 100:
            return
        wg.viewportLower =  posValue / 100.0
        wg.viewportUpper = (posValue + abs(upper - lower)) / 100.0
        wg.queue_draw()

    def crash_save(self):
        if self.model.subFilename == '' :
            return
        srtFile(self.model.subFilename+'_crash').write_to_file(self.model.subtitles.get_sub_list(), encoding = self.preferences['Encoding'])

    def on_save_button_clicked(self, widget):
        if self.model.subFilename == "":
            return
        # Save Subtitle
        if self.preferences['Incremental_Backups']:
            srtFilename = self.model.subFilename.decode('utf-8')
            tmp = cfile(srtFilename)
            base = tmp.base
            ext = tmp.ext
            for i in xrange(9, 0, -1):
                if cfile('%s-%s.%s' % (base, str(i+1), ext)).exists:
                    cfile('%s-%s.%s' % (base, str(i+1), ext)).delete()
                if cfile('%s-%s.%s' % (base, str(i), ext)).exists:
                    cfile('%s-%s.%s' % (base, str(i), ext)).rename('%s-%s.%s' % (base, str(i+1), ext))
            if cfile('%s-1.%s' % (base, ext)).exists:
                cfile('%s-1.%s' % (base, ext)).delete()
            if cfile(base + '.' + ext).exists:
                cfile(base + '.' + ext).rename(base + '-1.' + ext)
        srtFile(self.model.subFilename).write_to_file(self.model.subtitles.get_sub_list(), encoding = self.preferences['Encoding'])
        self.save_subs_info()
        self.model.subtitles.clear_changed()
        self.check_modified()

    def on_mainwindow_resize(self, widget):
        if self.resizeEventCounter > 0:
            self.resizeEventCounter -= 1
            return
        newHeight = self.view.get_allocation().height
        newWidth = self.view.get_allocation().width
        if self.view.width == newWidth and self.view.height == newHeight:
            self.view.subtitlesViewSize = 1 - (self.view['root-paned-container'].get_position() / (float(self.view.height - 1)))
            self.view.audioViewSize = self.view['audio-video-container'].get_position() / float(self.view.width - 1)
        else:
            self.view.width, self.view.height = newWidth, newHeight
            self.view['root-paned-container'].set_position((1 - self.view.subtitlesViewSize) * self.view.height)
            self.view['audio-video-container'].set_position(self.view.audioViewSize * self.view.width)
            self.resizeEventCounter = 2
        if (hasattr(self, 'init_done') and self.init_done) and (not ('subViewSize' in self.preferences and 'audioViewSize' in self.preferences) or not (self.preferences['subViewSize'] == self.view.subtitlesViewSize and self.preferences['audioViewSize'] == self.view.audioViewSize)):
            self.preferences['subViewSize'] = self.view.subtitlesViewSize
            if self.view['video'].props.visible:
                self.preferences['audioViewSize'] = self.view.audioViewSize
            self.preferences.save()

    def on_video_finish(self, bus, message):
        self.model.video.pause()

    def on_video_clicked(self, widget, event):
        if event.button == 1:
            if not self.model.video.is_ready():
                return
            if self.model.video.is_playing():
                self.model.video.pause()
            else:
                self.model.video.play()
        elif event.button == 3:
            vready = self.has_audio_duration()
            self.view['VCM-SceneDetect'].set_sensitive(vready)
            if hasattr(self, 'scenedetect') and self.scenedetect.is_active():
                self.view['VCM-SceneDetect'].hide()
                self.view['VCM-StopDetection'].show()
            else:
                self.view['VCM-SceneDetect'].show()
                self.view['VCM-StopDetection'].hide()
            self.view['VideoContextMenu'].popup(None, None, None, None, event.button, event.time)

    def on_audio_mousewheel(self, widget, event):
        wg = self.view['audio']
        if hasattr(self, 'vSyncWidget') and self.vSyncWidget.props.visible:
            wg = self.vSyncWidget
        self.view['scale'].set_value(wg.viewportLower * 100)

    def on_audio_ready(self, sender):
        self.view['audio'].audioModel = self.model.audio
        self.view['audio'].subtitleModel = self.model.subtitles
        self.view['audio'].voModel = self.model.voReference
        self.view['audio'].queue_draw()

    def on_video_position_vsync(self):
        self.vSyncWidget.pos = self.view['audio'].pos

        # Follow video position in audioview
        pos = self.vSyncWidget.pos / float(self.vSyncWidget.audioDuration)
        vup = self.vSyncWidget.viewportUpper
        vlow = self.vSyncWidget.viewportLower
        vdiff = vup - vlow
        if pos > vlow + vdiff * 0.98 and vup < 1:
            if pos - vdiff * 0.90 < 1:
                self.vSyncWidget.viewportLower = pos - vdiff * 0.10
                self.vSyncWidget.viewportUpper = pos + vdiff * 0.90
            else:
                self.vSyncWidget.viewportUpper = 1
                self.vSyncWidget.viewportLower = 1 - vdiff
            self.vSyncWidget.queue_draw()
        if pos < vlow:
            if pos - vdiff * 0.10 > 0:
                self.vSyncWidget.viewportLower = pos - vdiff * 0.10
                self.vSyncWidget.viewportUpper = pos + vdiff * 0.90
            else:
                self.vSyncWidget.viewportLower = 0
                self.vSyncWidget.viewportUpper = vdiff
            self.vSyncWidget.queue_draw()

    def on_video_position(self, sender, _position):
        position = _position / 1000.0
        self.view['audio'].pos = int(self.audioDuration * position)
        self.view['position-label'].set_label('Position: %s ' % ms2ts(int( position * self.audioDuration)))

        # Show Subtitle on Video
        overSub = self.model.subtitles.inside_sub(self.view['audio'].pos)
        text = overSub.text if overSub != None else ''
        self.model.video.set_subtitle(filter_markup(text))

        # Follow video position in audioview
        pos = self.view['audio'].pos / float(self.view['audio'].audioDuration)
        vup = self.view['audio'].viewportUpper
        vlow = self.view['audio'].viewportLower
        vdiff = vup - vlow
        if pos > vlow + vdiff * 0.98 and vup < 1:
            if pos - vdiff * 0.90 < 1:
                self.view['audio'].viewportLower = pos - vdiff * 0.10
                self.view['audio'].viewportUpper = pos + vdiff * 0.90
            else:
                self.view['audio'].viewportUpper = 1
                self.view['audio'].viewportLower = 1 - vdiff
            self.view['audio'].queue_draw()
        if pos < vlow:
            if pos - vdiff * 0.10 > 0:
                self.view['audio'].viewportLower = pos - vdiff * 0.10
                self.view['audio'].viewportUpper = pos + vdiff * 0.90
            else:
                self.view['audio'].viewportLower = 0
                self.view['audio'].viewportUpper = vdiff
            self.view['audio'].queue_draw()

        # Activate subtitles under video position, blocking centering signals
        if not self.model.video.is_playing():
            return
        if overSub != None:
            path = self.model.subtitles.get_sub_path(overSub)
            if path != None:
                with GObject.signal_handler_block(self.view['subtitles'], self.tv_cursor_changed_id):
                    self.view['subtitles'].set_cursor(path)

        if hasattr(self, 'vSyncWidget') and self.vSyncWidget.props.visible:
            self.on_video_position_vsync()

    def has_audio_duration(self):
        return self.audioDuration != 0

    def has_video_duration(self):
        return self.videoDuration != 0

    def check_video_file_compatibility(self, filename):
        if platform.system() != 'Windows':
            return filename
        media_info = cMediaInfo(filename)
        media_info.run()
        tmp = cfile(filename)
        tmp.change_base(tmp.base + '-fixed')
        tmp.change_ext('.mkv')
        new_filename = tmp.full_path
        if media_info.audio_codec != 'A_AAC':
            recodeDialog = cRecodeDialog(self.view, filename, new_filename, 'ffmpeg -y -i "SOURCEFILE" -c:v copy -c:a pcm_s16le "DESTFILE"', 'Fixing incompatible audio.')
            recodeDialog.run()
            return new_filename if recodeDialog.result else ''
        return filename
