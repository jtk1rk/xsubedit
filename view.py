import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, Gdk, GObject
from gcustom.audioWidget import cAudioWidget
from gcustom.progressBar import cProgressBar

class TimedStatusBar(Gtk.Statusbar):
    def __init__(self, timeout):
        super(TimedStatusBar, self).__init__()
        self.timeout = timeout
        self.last_tag = None

    def clear(self):
        self.pop(0)
        self.last_tag = None

    def del_timer(self):
        if self.last_tag:
            GObject.source_remove(self.last_tag)

    def set_timer(self):
        self.del_timer()
        self.last_tag = GObject.timeout_add(self.timeout, self.clear)

    def output(self, msg):
        self.del_timer()
        self.clear()
        self.push(0, msg)
        self.set_timer()

class EventDrawingArea(Gtk.EventBox):
    def __init__(self):
        super(EventDrawingArea, self).__init__()
        self.DrawingArea = Gtk.DrawingArea()
        self.add(self.DrawingArea)
        self.set_events(Gdk.EventMask.SCROLL_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.show_all()

class View(Gtk.Window):
    width = 1024
    height = 768
    audioViewSize = 0.8
    subtitlesViewSize = 0.7
    widgets = {}

    def __init__(self, prog_title):
        super(View, self).__init__(title = prog_title)
        self.prog_title = prog_title
        self.set_default_size(self.width, self.height)
        black = Gdk.RGBA(0,0,0,1)

        # Widgets
        self.widgets['video'] = EventDrawingArea()
        self.widgets['video'].override_background_color(0, black)
        self.widgets['audio'] = cAudioWidget()
        self.widgets['audio'].override_background_color(0, black)
        self.widgets['subtitles'] = Gtk.TreeView()
        self.widgets['video-eventbox'] = Gtk.EventBox()
        self.widgets['scale'] = Gtk.HScale.new_with_range(0,100,1)
        self.widgets['scale'].set_property('draw-value', False)
        self.widgets['scale'].set_property('has-origin', False)
        self.widgets['progress-bar'] = cProgressBar(height = 5)
        #self.widgets['statusbar'] = TimedStatusBar(4000)

        # Toolbar
        self.widgets['toolbar'] = Gtk.Toolbar()
        self.widgets['saveFileTB'] = Gtk.ToolButton()
        self.widgets['saveFileTB'].set_tooltip_text('Save Project')
        self.widgets['saveFileTB'].set_stock_id(Gtk.STOCK_SAVE)
        self.widgets['newFileTB'] = Gtk.ToolButton()
        self.widgets['newFileTB'].set_tooltip_text('Create Project')
        self.widgets['newFileTB'].set_stock_id(Gtk.STOCK_NEW)
        self.widgets['openFileTB'] = Gtk.ToolButton()
        self.widgets['openFileTB'].set_tooltip_text('Open Project')
        self.widgets['openFileTB'].set_stock_id(Gtk.STOCK_OPEN)
        self.widgets['separator1TB'] = Gtk.SeparatorToolItem()
        self.widgets['undoTB'] = Gtk.ToolButton()
        self.widgets['undoTB'].set_tooltip_text('Undo')
        self.widgets['undoTB'].set_stock_id(Gtk.STOCK_UNDO)
        self.widgets['redoTB'] = Gtk.ToolButton()
        self.widgets['redoTB'].set_tooltip_text('Redo')
        self.widgets['redoTB'].set_stock_id(Gtk.STOCK_REDO)
        self.widgets['preferencesTB'] = Gtk.ToolButton()
        self.widgets['preferencesTB'].set_tooltip_text('Preferences')
        self.widgets['preferencesTB'].set_stock_id(Gtk.STOCK_PROPERTIES)
        self.widgets['projectSettingsTB'] = Gtk.ToolButton()
        self.widgets['projectSettingsTB'].set_tooltip_text('Project Settings')
        self.widgets['projectSettingsTB'].set_stock_id(Gtk.STOCK_DND)
        self.widgets['importSRTTB'] = Gtk.ToolButton()
        self.widgets['importSRTTB'].set_tooltip_text('Import Srt')
        self.widgets['importSRTTB'].set_stock_id(Gtk.STOCK_ADD)
        self.widgets['checkTB'] = Gtk.ToolButton()
        self.widgets['checkTB'].set_tooltip_text('Check Subtitles')
        self.widgets['checkTB'].set_stock_id(Gtk.STOCK_SPELL_CHECK)
        self.widgets['separator2TB'] = Gtk.SeparatorToolItem()
        self.widgets['separator3TB'] = Gtk.SeparatorToolItem()
        self.widgets['position-label'] = Gtk.Label('Position: 00:00:00,000 ')
        self.widgets['duration-label'] = Gtk.Label('Duration: 00:00:00,000\t\t')

        self.widgets['toolbar'].add(self.widgets['newFileTB'])
        self.widgets['toolbar'].add(self.widgets['openFileTB'])
        self.widgets['toolbar'].add(self.widgets['saveFileTB'])
        self.widgets['toolbar'].add(self.widgets['separator1TB'])
        self.widgets['toolbar'].add(self.widgets['preferencesTB'])
        self.widgets['toolbar'].add(self.widgets['projectSettingsTB'])
        self.widgets['toolbar'].add(self.widgets['separator2TB'])
        self.widgets['toolbar'].add(self.widgets['undoTB'])
        self.widgets['toolbar'].add(self.widgets['redoTB'])
        self.widgets['toolbar'].add(self.widgets['separator3TB'])
        self.widgets['toolbar'].add(self.widgets['importSRTTB'])
        self.widgets['toolbar'].add(self.widgets['checkTB'])

        # AudioView Context Menu
        self.widgets['AudioContextMenu'] = Gtk.Menu()
        self.widgets['ACM-SplitHere'] = Gtk.MenuItem('Split Subtitle')
        self.widgets['ACM-CreateHere'] = Gtk.MenuItem('New Subtitle')
        self.widgets['ACM-DeleteSub'] = Gtk.MenuItem('Delete Subtitle')
        self.widgets['ACM-ResetAudioScale'] = Gtk.MenuItem('Reset Vertical Zoom')
        self.widgets['ACM-StickZoom'] = Gtk.CheckMenuItem('Stick Zoom')
        self.widgets['ACM-StickZoom'].set_tooltip_text('Keep current horizontal zoom size')

        self.widgets['AudioContextMenu'].add(self.widgets['ACM-CreateHere'])
        self.widgets['AudioContextMenu'].add(self.widgets['ACM-SplitHere'])
        self.widgets['AudioContextMenu'].add(self.widgets['ACM-DeleteSub'])
        self.widgets['AudioContextMenu'].add(self.widgets['ACM-ResetAudioScale'])
        self.widgets['AudioContextMenu'].add(self.widgets['ACM-StickZoom'])
        self.widgets['ACM-StickZoom'].show()
        self.widgets['ACM-SplitHere'].show()
        self.widgets['ACM-CreateHere'].show()
        self.widgets['ACM-DeleteSub'].show()

        # Header Context Menu
        self.widgets['HeaderContextMenu'] = Gtk.Menu()
        self.widgets['HCM-N'] = Gtk.CheckMenuItem('N')
        self.widgets['HCM-StartTime'] = Gtk.CheckMenuItem('StartTime')
        self.widgets['HCM-StopTime'] = Gtk.CheckMenuItem('StopTime')
        self.widgets['HCM-Duration'] = Gtk.CheckMenuItem('Duration')
        self.widgets['HCM-Reference'] = Gtk.CheckMenuItem('Reference')
        self.widgets['HCM-RS'] = Gtk.CheckMenuItem('RS')
        self.widgets['HCM-Count'] = Gtk.CheckMenuItem('Count')
        self.widgets['HCM-Info'] = Gtk.CheckMenuItem('Info')
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-N'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-StartTime'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-StopTime'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-Duration'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-Reference'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-RS'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-Count'])
        self.widgets['HeaderContextMenu'].add(self.widgets['HCM-Info'])
        self.widgets['HCM-N'].set_active(True)
        self.widgets['HCM-StartTime'].set_active(True)
        self.widgets['HCM-StopTime'].set_active(True)
        self.widgets['HCM-Duration'].set_active(True)
        self.widgets['HCM-Reference'].set_active(True)
        self.widgets['HCM-RS'].set_active(True)
        self.widgets['HCM-Count'].set_active(True)
        self.widgets['HCM-Info'].set_active(True)
        self.widgets['HCM-N'].show()
        self.widgets['HCM-StartTime'].show()
        self.widgets['HCM-StopTime'].show()
        self.widgets['HCM-Duration'].show()
        self.widgets['HCM-Reference'].show()
        self.widgets['HCM-RS'].show()
        self.widgets['HCM-Count'].show()
        self.widgets['HCM-Info'].show()

        # TreeView Context Menu
        self.widgets['TVContextMenu'] = Gtk.Menu()
        self.widgets['TVCM-Delete'] = Gtk.MenuItem('Delete Subtitle(s)')
        self.widgets['TVCM-Merge'] = Gtk.MenuItem('Merge Subtitles')
        self.widgets['TVCM-Merge-To-Dialog'] = Gtk.MenuItem('Merge to Dialog')
        self.widgets['TVCM-DurationEdit'] = Gtk.MenuItem('Edit Duration')
        self.widgets['TVCM-TimeEditDialog'] = Gtk.MenuItem('Edit Time')
        self.widgets['TVCM-SyncDialog'] = Gtk.MenuItem('Sync')
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-Merge'])
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-Merge-To-Dialog'])
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-Delete'])
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-DurationEdit'])
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-TimeEditDialog'])
        self.widgets['TVContextMenu'].add(self.widgets['TVCM-SyncDialog'])
        self.widgets['TVCM-Delete'].show()
        self.widgets['TVCM-Merge'].show()
        self.widgets['TVCM-Merge-To-Dialog'].show()

        # Video Context Menu
        self.widgets['VideoContextMenu'] = Gtk.Menu()
        self.widgets['VCM-SceneDetect'] = Gtk.MenuItem('Detect Scene Changes')
        self.widgets['VCM-StopDetection'] = Gtk.MenuItem('Stop Detection')
        self.widgets['VCM-TwoPassSD'] = Gtk.CheckMenuItem('Two-pass Detection (faster)')
        self.widgets['VCM-TwoPassSD'].set_active(True)

        self.widgets['VideoContextMenu'].add(self.widgets['VCM-SceneDetect'])
        self.widgets['VideoContextMenu'].add(self.widgets['VCM-StopDetection'])
        self.widgets['VideoContextMenu'].add(self.widgets['VCM-TwoPassSD'])

        self.widgets['VCM-SceneDetect'].show()
        self.widgets['VCM-StopDetection'].hide()
        self.widgets['VCM-TwoPassSD'].show()

        # Containers
        self.widgets['root-paned-container'] = Gtk.Paned(orientation = Gtk.Orientation.VERTICAL)
        self.widgets['audio-video-container'] = Gtk.Paned(orientation = Gtk.Orientation.HORIZONTAL)
        self.widgets['audio-video-container'].override_background_color(Gtk.StateType.NORMAL, black)

        self.widgets['toolbar-subtitles-container'] = Gtk.VBox()
        self.widgets['audio-scale-container'] = Gtk.VBox()
        self.widgets['toolbar-reports-container'] = Gtk.HBox()
        self.widgets['vertical-sub-scrollable'] = Gtk.ScrolledWindow()
        self.widgets['vertical-sub-scrollable'].set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # Layout
        self.widgets['root-paned-container'].set_position((1 - self.subtitlesViewSize) * self.height)
        self.widgets['audio-video-container'].set_position(self.audioViewSize * self.width)

        self.widgets['video-eventbox'].add(self.widgets['video'])

        self.widgets['audio-scale-container'].pack_start(self.widgets['audio'], True, True, 0)
        self.widgets['audio-scale-container'].pack_start(self.widgets['progress-bar'], False, False, 0)
        self.widgets['audio-scale-container'].pack_end(self.widgets['scale'], False, False, 0)
        self.widgets['audio-video-container'].add(self.widgets['audio-scale-container'])
        self.widgets['audio-video-container'].add(self.widgets['video-eventbox'])

        self.widgets['toolbar-reports-container'].pack_start(self.widgets['toolbar'],True, True, 0)
        self.widgets['toolbar-reports-container'].pack_start(self.widgets['duration-label'], False, False, 0)
        self.widgets['toolbar-reports-container'].pack_end(self.widgets['position-label'], False, False, 50)

        self.widgets['toolbar-subtitles-container'].pack_start(self.widgets['toolbar-reports-container'], False, False, 0)
        self.widgets['vertical-sub-scrollable'].add(self.widgets['subtitles'])
        self.widgets['toolbar-subtitles-container'].pack_start(self.widgets['vertical-sub-scrollable'], True, True, 0)

        #self.widgets['toolbar-subtitles-container'].pack_end(self.widgets['statusbar'], False, False, 0)

        self.widgets['root-paned-container'].add(self.widgets['audio-video-container'])
        self.widgets['root-paned-container'].add(self.widgets['toolbar-subtitles-container'])

        self.add(self.widgets['root-paned-container'])

    def __getitem__(self, key):
        return self.widgets[key]
