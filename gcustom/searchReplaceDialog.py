# -*- encoding: utf-8 -*-
import gi
import regex
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk
from gcustom.replaceConfirmDialog import cReplaceConfirmDialog

class cSearchReplaceDialog(Gtk.Window):
    def __init__(self, parent, treeView, subtitles_model, hist):
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
        self.lastFindReplaceIdx = None
        self.hist = hist

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
        mainBox.pack_start(replaceBox, False, False, 0)
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
        lidx = -1 if left_idx is None else left_idx
        res = (None, None)
        search_text = text.decode('utf-8').upper() if not self.caseSensitive.get_active() else text.decode('utf-8')
        for iterNum, row in enumerate(self.treeView.get_model()):
            if iterNum <= lidx:
                continue
            subText = row[0].text.upper() if not self.caseSensitive.get_active() else row[0].text
            whword = '\\b' if self.wholeWordsSearch.get_active() else ''
            grp = regex.finditer(whword+search_text+whword, subText, flags = regex.U | regex.M)
            lst = [(item.start(), item.end()) for item in grp]
            tmpidx = iterNum if len(lst) > 0 else None
            res = (tmpidx, lst)
            if res[0] is not None:
                break
        return res

    def on_entry_changed(self, widget, arg):
        if arg == 'search':
            self.findText = widget.get_text()
            self.lastFindIdx = None
            self.lastFindReplaceIdx = None
        elif arg == 'replace':
            self.replaceText = widget.get_text()
            self.lastFindIdx = None
            self.lastFindReplaceIdx = None

    def on_clicked(self, widget, arg):
        if arg == 'search' and self.findText != None:
            nextIdx = self.find_row(self.findText, self.lastFindIdx)[0]
            if nextIdx is None:
                self.lastFindIdx = None
                return
            self.lastFindIdx = nextIdx
            self.tv_select_row(nextIdx)
        elif arg == 'replace' and self.replaceText != None and self.findText != None:
            nextIdx, posList = self.find_row(self.findText, -1)
            while nextIdx is not None:
                curpos = None
                if posList is not None and len(posList) > 0:
                    curpos = posList.pop(0)
                    self.lastFindIdx = nextIdx
                else:
                    nextIdx, posList = self.find_row(self.findText, self.lastFindIdx)
                    if nextIdx is None:
                        self.lastFindIdx = None
                        continue
                    curpos = posList.pop(0)
                    self.lastFindReplaceIdx = nextIdx
                    self.lastFindIdx = nextIdx
                    self.tv_select_row(nextIdx)
                if curpos is None:
                    return
                dialog = cReplaceConfirmDialog(self, self.treeView.get_model()[nextIdx][0].text, self.replaceText, curpos)
                dialog.run()
                res = dialog.result
                dialog.destroy()
                if res == 'OK':
                    tmp_txt = self.treeView.get_model()[nextIdx][0].text
                    new_txt = tmp_txt[:curpos[0]] + self.replaceText.decode('utf-8') + tmp_txt[curpos[1]:]
                    sub = self.treeView.get_model()[nextIdx][0]
                    self.hist.add( ('replace-text', sub, tmp_txt, new_txt) )
                    sub.text = new_txt
                elif res == 'Cancel':
                    continue
                elif res == 'Stop':
                    return

    def on_key_release(self, widget, event, arg):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
        if event.keyval == Gdk.KEY_Return:
            self.on_clicked(None, arg)
