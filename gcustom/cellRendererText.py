import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from textEditDialog import cTextEditDialog

class cCellRendererText(Gtk.CellRendererText):
    """ Label entry cell which calls TextEdit_Dialog upon editing """
    __gtype_name__ = 'CellRendererCustomText'

    def __init__(self, parent):
        super(cCellRendererText, self).__init__()
        self.parentWindow = parent

    def do_start_editing(
               self, event, treeview, path, background_area, cell_area, flags):
        if not self.get_property('editable'):
            return
        sub = treeview.get_model()[path][0]
        entry = Gtk.Entry()
        dialog = cTextEditDialog(self.parentWindow, sub, 'vo', treeview.thesaurus)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.text)
            self.emit('edited', path, entry.get_text())
        dialog.destroy()
