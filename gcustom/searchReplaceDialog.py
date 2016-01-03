# -*- encoding: utf-8 -*-
import gi
import regex
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk

class cSearchReplaceDialog(Gtk.Window):
    def __init__(self, parent, treeView, subtitles_model):
        super(cSearchReplaceDialog, self).__init__()

        # Setup Window Properties and Variables
        self.parent = parent
        self.set_title("Search / Replace")
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.treeView = treeView
        self.subtitles = subtitles_model
        self.findText = None
        self.replaceText = None
        self.set_resizable(False)
        self.lastFindIdx = None

        # Widgets
        searchEntry = Gtk.Entry()
        searchEntry.props.width_request = 200
        searchButton = Gtk.Button()
        searchButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_FIND, Gtk.IconSize.BUTTON))
        replaceEntry = Gtk.Entry()
        replaceEntry.props.width_request = 200
        replaceButton = Gtk.Button()
        replaceButton.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_FIND_AND_REPLACE, Gtk.IconSize.BUTTON))
        self.wholeWordsSearch = Gtk.CheckButton("Whole Words")
        self.caseSensitive = Gtk.CheckButton("Case Sensitive")
        self.caseSensitive.set_active(True)

        # Layout
        tmp = Gtk.Label('Search')
        tmp.props.width_request = 65
        searchBox = Gtk.HBox()
        searchBox.pack_start(tmp, False, False, 0)
        searchBox.pack_start(searchEntry, False, False, 5)
        searchBox.pack_start(searchButton, False, False, 5)

        replaceBox = Gtk.HBox()
        tmp = Gtk.Label('Replace')
        tmp.props.width_request = 65
        replaceBox.pack_start(tmp, False, False, 0)
        replaceBox.pack_start(replaceEntry, False, False, 5)
        replaceBox.pack_start(replaceButton, False, False, 5)

        settingsBox = Gtk.HBox()
        settingsBox.pack_start(self.wholeWordsSearch, False, False, 5)
        settingsBox.pack_start(self.caseSensitive, False, False, 5)

        mainBox = Gtk.VBox(spacing = 3)
        mainBox.pack_start(searchBox, False, False, 0)
#        mainBox.pack_start(replaceBox, False, False, 0)
        mainBox.pack_start(settingsBox, False, False, 0)

        tmp = Gtk.VBox()
        tmp.pack_start(mainBox, False, False, 5)

        self.add(tmp)

        # Connections
        searchEntry.connect('key-release-event', self.on_key_release, 'search')
        replaceEntry.connect('key-release-event', self.on_key_release, 'replace')
        searchButton.connect('key-release-event', self.on_key_release, None)
        replaceButton.connect('key-release-event', self.on_key_release, None)
        self.wholeWordsSearch.connect('key-release-event', self.on_key_release, None)
        self.caseSensitive.connect('key-release-event', self.on_key_release, None)
        searchButton.connect('clicked', self.on_clicked, 'search')
        replaceButton.connect('clicked', self.on_clicked, 'replace')
        searchEntry.connect('changed', self.on_entry_changed, 'search')
        replaceEntry.connect('changed', self.on_entry_changed, 'replace')
        
        # Finally
        self.show_all()

    def tv_select_row(self, row):
        if row is None:
            return
        sub = self.treeView.get_model()[row][0]
        path = self.subtitles.get_sub_path(sub)
        if path != None:
            self.treeView.set_cursor(path)

    def find_row(self, text, left_idx):
        search_text = text.decode('utf-8').upper() if not self.caseSensitive.get_active() else text.decode('utf-8')
        for iterNum, row in enumerate(self.treeView.get_model()):
            subText = row[0].text.upper() if not self.caseSensitive.get_active() else row[0].text
            if search_text in subText and left_idx < iterNum:
                if self.wholeWordsSearch.get_active():
                    if regex.search('\\b'+search_text+'\\b', subText, flags = regex.U | regex.M) is not None:
                        return iterNum
                else:
                    return iterNum
        return None
 
    def on_entry_changed(self, widget, arg):
        if arg == 'search':
            self.findText = widget.get_text()
            self.lastFindIdx = None
        elif arg == 'replace':
            self.replaceText = widget.get_text()
            self.lastFindIdx = None

    def on_clicked(self, widget, arg):
        if arg == 'search' and self.findText != None:
            nextIdx = self.find_row(self.findText, self.lastFindIdx)
            if nextIdx is not None:
                self.lastFindIdx = nextIdx
            if nextIdx is None and (self.lastFindIdx > 0):
                nextIdx = self.find_row(self.findText, -1)
            self.tv_select_row(nextIdx)
            self.lastFindIdx = nextIdx
        elif arg == 'replace' and self.replace != None and self.findText != None:
            return

    def on_key_release(self, widget, event, arg):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        if event.keyval == Gdk.KEY_Return:
            self.on_clicked(None, arg)
