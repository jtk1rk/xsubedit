# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gtk, Gdk,  GObject
import subtitles
#import platform
from tagtext import TagText as cTagText
from mparser import Tag
from utils import brList
from sites.GoogleTranslate import translate as GTrans
from sites.WordReference import translate as WRTrans
from sites.UrbanDictionary import meaning as UDMeaning
from sites.TheFreeDictionary import meaning as TFDMeaning
from gcustom.textResultWin import cTextResultWin

#if platform.system() == 'Windows':
#    import customspell as GtkSpell
#else:
#    gi.require_version('GtkSpell', '3.0')
#    from gi.repository import GtkSpell
import customspell as GtkSpell

def custom_insert_markup(buff,  markup):
    tagText = cTagText()
    tagText.parse_markup(markup)
    tagText.replace_parsed('&lt;i&gt;', '<i>')
    tagText.replace_parsed('&lt;/i&gt;', '</i>')
    buff.set_property('text', tagText.text)

    # Setup Color Tags (if any)
    color_tags = set()
    for tag in tagText.tags:
        if 'foreground' in tag.attributes and 'background' in tag.attributes:
            buff.create_tag(tag.id, foreground=tag.attributes['foreground'], background=tag.attributes['background'])
            color_tags.add(tag.id)
        if 'foreground' in tag.attributes and not 'background' in tag.attributes:
            buff.create_tag(tag.id, foreground=tag.attributes['foreground'])
            color_tags.add(tag.id)
        if 'background' in tag.attributes and not 'foreground' in tag.attributes:
            buff.create_tag(tag.id, background=tag.attributes['background'])
            color_tags.add(tag.id)

    # Apply Tags
    for tag in tagText.tags:
        if tag.name == 'i':
            buff.apply_tag_by_name('italics', buff.get_iter_at_offset(tag.start), buff.get_iter_at_offset(tag.stop))
        if tag.name == 'b':
            buff.apply_tag_by_name('bold', buff.get_iter_at_offset(tag.start), buff.get_iter_at_offset(tag.stop))
        if tag.name == 'span' and tag.id in color_tags:
                buff.apply_tag_by_name(tag.id, buff.get_iter_at_offset(tag.start), buff.get_iter_at_offset(tag.stop))

class cHistory:
    def __init__(self, textBuffer):
        self.data = brList()
        self.textBuffer = textBuffer 
        self.curIdx = 0
        self.serialize_format = self.textBuffer.register_serialize_tagset()
        self.deserialize_format = self.textBuffer.register_deserialize_tagset()
        begin, end = self.textBuffer.get_bounds()
        insert_iter_offset = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()
        self.data.append(self.curIdx, (self.textBuffer.serialize(self.textBuffer, self.serialize_format, begin, end), insert_iter_offset))

    def clear_text_buffer(self):
        self.textBuffer.set_text('')

    def update(self):
        begin, end = self.textBuffer.get_bounds()
        self.curIdx += 1
        insert_iter_offset = self.textBuffer.get_iter_at_mark(self.textBuffer.get_insert()).get_offset()
        self.data.append(self.curIdx, (self.textBuffer.serialize(self.textBuffer, self.serialize_format, begin, end), insert_iter_offset))

    def undo(self):
        if self.curIdx > 0:
            self.curIdx -= 1
            self.clear_text_buffer()
            self.textBuffer.deserialize(self.textBuffer, self.deserialize_format, self.textBuffer.get_start_iter(), self.data[self.curIdx][0])
            self.textBuffer.place_cursor(self.textBuffer.get_iter_at_offset(self.data[self.curIdx][1]))

    def redo(self):
        if self.curIdx < len(self.data) - 1:
            self.curIdx += 1
            self.clear_text_buffer()
            self.textBuffer.deserialize(self.textBuffer, self.deserialize_format, self.textBuffer.get_start_iter(), self.data[self.curIdx][0])
            self.textBuffer.place_cursor(self.textBuffer.get_iter_at_offset(self.data[self.curIdx][1]))

class cTextEditDialog(Gtk.Dialog):
    def __init__(self, parent, sub, info_type, thesaurus):
        super(cTextEditDialog, self).__init__('Subtitle Text Editor', None, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, ("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK))
        self.set_transient_for(parent)
        self.set_default_size(500, 240)
        self.char_count = Gtk.TextView()
        self.char_count.set_property('width-request', 30)
        self.char_count.set_sensitive(False)
        self.thesaurus = thesaurus
        
        self.hbox = Gtk.HBox(spacing = 1)
        self.text_view_box = Gtk.VBox(spacing = 1)
        self.text_view = Gtk.TextView()
        self.text_view.set_size_request(-1, 50)
        self.helper_text_view = Gtk.TextView()
        self.helper_text_view.set_property('editable', False)
        self.helper_text_view.set_property('can-focus', False)
        self.text_view_box.add(self.text_view)
        self.text_view_box.add(self.helper_text_view)

        if info_type == 'info':
            color_list = [(sub.info[key][1], sub.info[key][2]) for key in sub.info if key.startswith('Text')]
            tagText = cTagText()
            tagText.text = sub.text
            for color in color_list:
                for pos in color[0]:
                    tagText.add_tag(Tag('span', pos[0], pos[1], {'background': color[1]}))
            tagText.replace_parsed('<i>', '&lt;i&gt;')
            tagText.replace_parsed('</i>', '&lt;/i&gt;')
            custom_insert_markup(self.text_view.get_buffer(), tagText.markup)
            custom_insert_markup(self.helper_text_view.get_buffer(), sub.info_text_str)
        elif info_type == 'vo':
            self.text_view.get_buffer().set_text(sub.text)
            self.helper_text_view.get_buffer().set_text(sub.vo)

        self.rs_text_label = Gtk.Label('Reading Speed: ')
        self.rs_value_label = Gtk.Label('')
        self.rs_dummylabel = Gtk.Label('\t\t\t\t')
        self.rs_box = Gtk.HBox(spacing = 1)
        self.rs_box.pack_start(self.rs_text_label, False, False, 0)
        self.rs_box.pack_start(self.rs_value_label, False, False, 0)
        self.rs_box.pack_start(self.rs_dummylabel, True, True, 0)

        self.history = cHistory(self.text_view.get_buffer())
        self.text_view.history = self.history

        self.spell = GtkSpell.Checker()
        self.spell.attach(self.text_view)
        self.spell.set_language('el_GR')

        self.hbox.pack_start(self.char_count, False, False, 0)
        self.hbox.pack_end(self.text_view_box, True, True, 0)
        self.vbox.pack_start(self.hbox,True, True, 0)
        self.action_area.pack_start(self.rs_box, False, False, 0)
        self.action_area.reorder_child(self.rs_box, 0)

        self.sub = subtitles.subRec(int(sub.startTime), int(sub.stopTime),  sub.text)
        self.update_count()

        self.vbox.show_all()
        self.set_default_response(Gtk.ResponseType.OK)
        self.changed_handler = self.text_view.get_buffer().connect('changed', self.buffer_changed)
        self.text_view.connect("key-release-event", self.key_release)
        self.text_view.connect("key-press-event", self.key_press)
        self.connect('destroy-event', self.on_destroy)
        self.text = sub.text

        self.text_view.connect('populate-popup',  self.on_tv_populate_popup)
        self.text_view.connect('button-press-event', self.on_tv_button_press)
        self.helper_text_view.connect('populate-popup',  self.on_hp_populate_popup)
        self.helper_text_view.connect('button-press-event', self.on_hp_button_press)
        self.helper_text_view.last_mouse_x = 0
        self.helper_text_view.last_mouse_y = 0
        self.text_view.last_mouse_x  = 0
        self.text_view.last_mouse_y = 0
        self.spell.on_buffer_changed(self.text_view.get_buffer())

    def on_tv_button_press(self, sender, event):
        self.text_view.last_mouse_x = event.x
        self.text_view.last_mouse_y = event.y

    def on_hp_button_press(self, sender, event):
        self.helper_text_view.last_mouse_x = event.x
        self.helper_text_view.last_mouse_y = event.y

    def on_hp_populate_popup(self, sender, popup):
        if self.get_selected_text(self.helper_text_view) == '':
            return
        transMenu = Gtk.Menu()
        transSubMenu = Gtk.MenuItem('Μετάφραση / Λεξικό')
        transSubMenu.set_property('submenu', transMenu)
        hp_GTrans = Gtk.MenuItem('Translation by Google')
        hp_WRTrans = Gtk.MenuItem('Translation by WordReference')
        hp_UDMeaning = Gtk.MenuItem('Meaning by UrbanDictionary')
        hp_TFDMeaning = Gtk.MenuItem('Meaning by TheFreeDictionary')
        transMenu.add(hp_GTrans)
        transMenu.add(hp_WRTrans)
        transMenu.add(hp_UDMeaning)
        transMenu.add(hp_TFDMeaning)
        popup.insert(Gtk.SeparatorMenuItem(), 0)
        popup.insert(transSubMenu, 0)
        hp_GTrans.connect('activate', self.trans_activated, 'GTrans', self.helper_text_view)
        hp_WRTrans.connect('activate', self.trans_activated, 'WRTrans', self.helper_text_view)
        hp_UDMeaning.connect('activate', self.trans_activated, 'UDMeaning', self.helper_text_view)
        hp_TFDMeaning.connect('activate', self.trans_activated, 'TFDMeaning', self.helper_text_view)
        popup.show_all()

    def on_tv_populate_popup(self, sender,  popup):
        # Add Translation Menu
        if not self.get_selected_text(self.text_view) == '':
            TranslationSubMenuItem = Gtk.MenuItem('Μετάφραση / Λεξικό')
            TranslationMenu = Gtk.Menu()
            TranslationSubMenuItem.set_property('submenu', TranslationMenu)
            mGTrans = Gtk.MenuItem('Translation by Google')
            mWRTrans = Gtk.MenuItem('Translation by WordReference')
            mTFDMeaning = Gtk.MenuItem('Meaning by TheFreeDictionary')
            mUDMeaning = Gtk.MenuItem('Meaning by UrbanDictionary')
            TranslationMenu.add(mGTrans)
            TranslationMenu.add(mWRTrans)
            TranslationMenu.add(mTFDMeaning)
            TranslationMenu.add(mUDMeaning)
            popup.insert(Gtk.SeparatorMenuItem(), 0)
            popup.insert(TranslationSubMenuItem, 0)
            mGTrans.connect('activate', self.trans_activated, 'GTrans', self.text_view)
            mWRTrans.connect('activate', self.trans_activated, 'WRTrans', self.text_view)
            mUDMeaning.connect('activate', self.trans_activated, 'UDMeaning', self.text_view)
            mTFDMeaning.connect('activate', self.trans_activated, 'TFDMeaning', self.text_view)
            popup.show_all()
        # Add Synonyms Menu
        iter = self.text_view.get_iter_at_location(self.text_view.last_mouse_x, self.text_view.last_mouse_y)
        p1 = iter.copy()
        p2 = iter.copy()
        p1.backward_word_start()
        p2.forward_word_end()
        word = self.text_view.get_buffer().get_text(p1, p2, False)
        thes_res = self.thesaurus.check(word)
        if thes_res is None or len(thes_res) == 0:
            return
        thesaurus = Gtk.MenuItem('Συνώνυμα')
        thesSubMenu = Gtk.Menu()
        subMenuItems = []
        for item in thes_res:
            menuItem = Gtk.MenuItem(item)
            subMenuItems.append(menuItem)
            thesSubMenu.add(menuItem)
        thesaurus.set_property('submenu', thesSubMenu)
        popup.insert(Gtk.SeparatorMenuItem(), 0)
        popup.insert(thesaurus, 0)
        for item in subMenuItems:
            item.connect('activate', self.on_thesaurus_activated,  p1,  p2)
        popup.show_all()

    def on_thesaurus_activated(self, sender,  p1,  p2):
        word = sender.get_label()
        self.text_view.get_buffer().delete(p1, p2)
        self.text_view.get_buffer().insert(p1, word, -1)
        self.history.update()
    
    def get_selected_text(self, textview):
        if not textview.get_buffer().get_has_selection():
            return ''
        bounds = textview.get_buffer().get_selection_bounds()
        return textview.get_buffer().get_text(bounds[0], bounds[1], False)

    def trans_activated(self, sender, service, textview):
        text = self.get_selected_text(textview)
        if text == '':
            return
        res = None
        caption = ''
        if service == 'GTrans':
            res = GTrans(text)
            caption = 'Results from Google Translate'
        elif service == 'WRTrans':
            res = WRTrans(text)
            caption = 'Results from WordReference'
        elif service == 'UDMeaning':
            res = UDMeaning(text)
            caption = 'Results from UrbanDictionary'
        elif service == 'TFDMeaning':
            res = TFDMeaning(text)
            caption = 'Results from TheFreeDictionary'
        if res is None or len(res) == 0:
            return
        showText = '\n'.join(res)
        cTextResultWin(self, caption, showText)

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    def on_destroy(self, widget, event):
        self.spell.detach()

    def key_press(self, widget, event):
        if  (event.keyval == Gdk.KEY_Return and event.state & Gdk.ModifierType.CONTROL_MASK) or (event.keyval == Gdk.KEY_F2):
            return True
        return False

    def key_release(self, widget, event):
        buffer = self.text_view.get_buffer()

        insertIter = buffer.get_iter_at_mark(buffer.get_insert())
        if insertIter.backward_search("...", 0, None) != None:
            eFindIterStart = insertIter.backward_search("...", 0, None)[0]
            eFindIterStop = insertIter.backward_search("...", 0, None)[1]
            buffer.delete(eFindIterStart, eFindIterStop)
            buffer.insert(buffer.get_iter_at_mark(buffer.get_insert()), "…")

        insertIter = buffer.get_iter_at_mark(buffer.get_insert())
        if insertIter.backward_search('\"', 0, None) != None:
            qFindIter = insertIter.backward_search('\"', 0, None)[1] if insertIter.backward_search('\"', 0, None) != None else None
            qFindIterPrev = insertIter.backward_search('\"', 0, None)[0]
            qOpen = qFindIter.backward_search('«', 0, None)[1].get_offset() if qFindIter.backward_search('«', 0, None) != None else -1
            qClose = qFindIter.backward_search('»', 0, None)[1].get_offset() if qFindIter.backward_search('»', 0, None) != None else -1
            if (qOpen == -1 and qClose == -1) or (qOpen < qClose):
                buffer.delete(qFindIterPrev, qFindIter)
                buffer.insert(qFindIter, '«')
            else:
                buffer.delete(qFindIterPrev, qFindIter)
                buffer.insert(qFindIter, '»')

        if  (event.keyval in [Gdk.KEY_i, Gdk.KEY_I, 1993, 2025]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            if buffer.get_has_selection():
                iter1 = buffer.get_selection_bounds()[0]
                buffer.insert(iter1, "<i>")
                iter2 = buffer.get_selection_bounds()[1]
                buffer.insert(iter2, "</i>")
                buffer.select_range(iter2,iter2)
            else:
                insertIter = buffer.get_iter_at_mark(buffer.get_insert())
                itStartIter = insertIter.backward_search("<i>", 0, None)
                if itStartIter != None:
                    itStopIter = itStartIter[1].forward_search("</i>", 0, None)
                else:
                    itStopIter = None
                isOpen = itStartIter != None and (itStopIter == None)
                if itStartIter == None:
                    buffer.insert(insertIter, "<i>")
                elif isOpen:
                    buffer.insert(insertIter, "</i>")
                elif not isOpen:
                    if insertIter.compare(itStopIter[1]) >= 0:
                        buffer.insert(insertIter, "<i>")

        if  event.keyval == Gdk.KEY_Return and event.state & Gdk.ModifierType.CONTROL_MASK:
            self.response(Gtk.ResponseType.OK)
            return True

        if  event.keyval in [Gdk.KEY_Z, Gdk.KEY_z, 2022, 1990] and event.state & Gdk.ModifierType.CONTROL_MASK:
            with GObject.signal_handler_block(self.text_view.get_buffer(), self.changed_handler):
                if event.state & Gdk.ModifierType.SHIFT_MASK:
                    self.history.redo()
                else:
                    self.history.undo()

        if (event.keyval in [Gdk.KEY_Y, Gdk.KEY_y, 2037, 2005]) and event.state & Gdk.ModifierType.CONTROL_MASK:
            with GObject.signal_handler_block(self.text_view.get_buffer(), self.changed_handler):
                self.history.redo()

    def update_count(self):
        lines = self.text_view.get_buffer().get_text(self.text_view.get_buffer().get_start_iter(), self.text_view.get_buffer().get_end_iter(), False)
        tmptext = lines
        lines = lines.split('\n')
        tmp = '\n'.join(map(lambda i: str(len(i.decode("utf-8").replace('<i>','').replace('</i>',''))), lines))
        self.char_count.get_buffer().set_text(tmp)
        self.sub.text = tmptext.decode('utf-8')
        self.rs_value_label.set_markup(self.sub.rs_str)

    def buffer_changed(self, sender):
        self.text = sender.get_text(sender.get_start_iter(), sender.get_end_iter(), include_hidden_chars = True).decode('utf-8')
        self.history.update()
        self.update_count()
