import enchant
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('Pango', '1.0')
gi.require_version('Gio', '2.0')
from gi.repository import Pango, Gtk, Gio

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
        self.button_release_handler_id = self.text_view.connect('button-release-event', self.on_textview_button_release)
        self.button_press_handler_id = self.text_view.connect('button-press-event', self.on_textview_button_press)
        self.buffer.create_tag(tag_name="customspell-error", underline=Pango.Underline.ERROR)
    
    def detach(self):
        if self.changed_handler_id == None:
            return
        self.buffer.disconnect(self.changed_handler_id)
        self.text_view.disconnect(self.button_press_handler_id)
        self.text_view.disconnect(self.button_release_handler_id)
        self.buffer = None
        self.changed_handler_id = None
        self.text_view = None

    def on_textview_button_press(self, widget, event):
        if event.button == 3:
            return True
        return False

    def on_textview_button_release(self, widget, event):
        if event.button == 3:
            iter = self.text_view.get_iter_at_location(event.x, event.y)
            self.p1 = iter.copy()
            self.p2 = iter.copy()
            self.p1.backward_word_start()
            self.p2.forward_word_end()
            word = self.buffer.get_text(self.p1, self.p2, False)

            if self.spellchecker.check(word):
                return True

            word_list = self.spellchecker.suggest(word)
            if word_list == []:
                return True

            menu_list = Gio.Menu()
            menu_list.append('0')
            for item in word_list:
                menu_list.append(item)

            self.menu   = Gtk.Menu.new_from_model(menu_list)
            self.menu.get_active().hide()
            self.menu.popup(None, None, None, None, event.button, event.time)
            self.menu.connect('selection-done',  self.on_popup_selection)
 
        return False

    def on_popup_selection(self,  menu_shell):
        word = self.menu.get_active().get_label()
        if word == '0':
            return
        self.buffer.delete(self.p1, self.p2)
        self.buffer.insert(self.p1, word, -1)
        self.p1 = None
        self.p2 = None

    def on_buffer_changed(self,  buffer):
        if self.spellchecker == None:
            return
        self.buffer.remove_all_tags(self.buffer.get_start_iter(), self.buffer.get_end_iter())

        # Try to solve the problem that
        # red lines remain visible for long time.
        # If it doesn't solve it, the next line will be removed.
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
            if not self.spellchecker.check(entry[0]):
                buffer.apply_tag_by_name("customspell-error", entry[1], entry[2])
