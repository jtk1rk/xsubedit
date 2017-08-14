import enchant
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Pango, Gtk

class Checker:
    def __init__(self):
        self.spellchecker = None
        self.language = None
        self.buffer = None
        self.text_view = None
        self.changed_handler_id = None
        self.clicked_handler_id = None
        self.p1 = None
        self.p2 = None

    def set_language(self,  language):
        if not enchant.dict_exists(language):
            return
        self.language = language
        self.spellchecker = enchant.Dict(language)
    
    def get_language_list(self):
        return enchant.list_languages()

    def attach(self, text_view):
        self.text_view = text_view
        self.buffer = text_view.get_buffer()
        self.changed_handler_id = self.buffer.connect('changed', self.on_buffer_changed)
        self.buffer.create_tag(tag_name="customspell-error", underline=Pango.Underline.ERROR)
        self.popup_populate_handler = self.text_view.connect('populate-popup', self.on_populate_popup)

    def detach(self):
        if self.changed_handler_id == None:
            return
        self.buffer.disconnect(self.changed_handler_id)
        self.text_view.disconnect(self.popup_populate_handler)
        self.buffer = None
        self.changed_handler_id = None
        self.text_view = None

    def on_populate_popup(self, sender, popup):
        if not (hasattr(self.text_view, 'last_mouse_x') and hasattr(self.text_view, 'last_mouse_y')) or self.spellchecker is None:
            return
        itr = self.text_view.get_iter_at_location(self.text_view.last_mouse_x, self.text_view.last_mouse_y)
        if type(itr) is tuple:
            itr = itr[1]
        p1 = itr.copy()
        p2 = itr.copy()
        p1.backward_word_start()
        p2.forward_word_end()
        word = self.buffer.get_text(p1, p2, False)

        if self.spellchecker.check(word):
            removeWordMenuItem = Gtk.MenuItem('Remove Word')
            popup.insert(Gtk.SeparatorMenuItem(), 0)
            popup.insert(removeWordMenuItem, 0)
            removeWordMenuItem.connect('activate', self.on_remove_activated,  word)
            popup.show_all()
            return

        word_list = self.spellchecker.suggest(word)
        if word_list == []:
            return

        menuItems = [Gtk.MenuItem(item) for item in word_list]
        popup.insert(Gtk.SeparatorMenuItem(), 0)
        moreResults = Gtk.Menu()

        for idx,  item in enumerate(menuItems):
            item.connect('activate', self.on_activate, p1, p2)
            if idx <= 10:
                popup.insert(item, 0)
            else:
                moreResults.add(item)

        if len(menuItems) > 10:
            moreMenuItem = Gtk.MenuItem("More...")
            moreMenuItem.set_property('submenu', moreResults)
            popup.insert(moreMenuItem, 0)

        addWordMenuItem = Gtk.MenuItem('Add Word')
        popup.insert(Gtk.SeparatorMenuItem(), 0)
        popup.insert(addWordMenuItem, 0)
        addWordMenuItem.connect('activate', self.on_add_activated,  word)
        popup.show_all()

    def on_add_activated(self, item, word):
        if self.spellchecker is None:
            return
        self.spellchecker.add(word)
        self.on_buffer_changed(self.text_view.get_buffer())

    def on_remove_activated(self, item, word):
        if self.spellchecker is None:
            return
        self.spellchecker.remove(word)
        self.on_buffer_changed(self.text_view.get_buffer())

    def on_activate(self, item, p1, p2):
        word = item.get_label()
        self.buffer.delete(p1, p2)
        self.buffer.insert(p1, word, -1)
        self.text_view.history.update()

    def on_buffer_changed(self,  buffer):
        if self.spellchecker == None:
            return
        self.buffer.remove_tag_by_name('customspell-error', self.buffer.get_start_iter(), self.buffer.get_end_iter())
        self.text_view.queue_draw()

        pointer = self.buffer.get_start_iter().copy()
        insert = self.buffer.get_iter_at_mark(self.buffer.get_insert())
        word_list = []

        while pointer.forward_word_end():
            word_end = pointer.copy()
            word_start = None
            if not pointer.backward_word_start():
                break
            word_start = pointer.copy()
            if not insert.in_range(word_start, word_end):
                word_list.append((self.buffer.get_text(word_start, word_end, False), word_start, word_end))
            pointer = word_end.copy()

        for entry in word_list:
            if entry[0] == '':
                continue
            if not self.spellchecker.check(entry[0].strip()):
                buffer.apply_tag_by_name("customspell-error", entry[1], entry[2])
