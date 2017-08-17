# -*- encoding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from progressBar import cProgressBar
from subchecker import cSubChecker

class cSubCheckerDialog(Gtk.Window):
    def __init__(self, parent, subList):
        super(cSubCheckerDialog, self).__init__()
        self.parent = parent
        self.set_title('Checking Subtitles')
        self.set_modal(True)
        self.set_transient_for(parent)
        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)
        self.set_size_request(400, -1)
        self.progressBar = cProgressBar()
        self.add(self.progressBar)
        self.subChecker = cSubChecker()
        self.subList = subList
        self.set_resizable(False)
        self.show_all()
        window = self.get_window()
        if window:
            window.set_functions(0)

    def set_progress(self, value):
        self.progressBar.position = value
        self.process_messages()

    def run(self):
        if len(self.subList) == 0:
            self.destroy()
            return
        self.show()
        self.process_messages()
        for sub in self.subList:
            sub.info = {}
        # Iterate through all subtitles
        # and perform checks
        for i in xrange(len(self.subList)):
            prevSub = self.subList[i - 1] if i - 1 > 0 else None
            curSub = self.subList[i]
            nextSub = self.subList[i + 1] if i + 1 < len(self.subList) else None

            # Checks go here

            self.subChecker.check_final_n(curSub)
            self.subChecker.check_duration(curSub, nextSub)
            self.subChecker.check_time_gap(curSub, prevSub)
            self.subChecker.check_gap_after_punctuation(curSub)
            self.subChecker.check_ending_with_article(curSub)
            self.subChecker.check_ending_with_preposition(curSub)
            self.subChecker.check_multiple_whitespaces(curSub)
            self.subChecker.check_orthography(curSub)
            self.subChecker.check_dialog_dash(curSub)
            self.subChecker.xproof_checks(prevSub, curSub, nextSub)
            self.subChecker.check_empty_line(curSub)

            # Checks done

            if curSub.info_text_str != '': # and 'Audio-Text-Corrections' not in curSub.info:
                curSub.info = ('Audio-Text-Corrections',  (u"<span foreground='orange'>Διορθώσεις κειμένου</span>",  []))

            self.set_progress(float(i+1) / len(self.subList))
        self.destroy()

    def _run(self):
        if len(self.subList) == 0:
            self.destroy()
            return

        self.show()
        self.process_messages()

        self.set_progress(0)
        self.subChecker.check_time_gap()
        self.set_progress(1/9.0)
        self.subChecker.check_duration()
        self.set_progress(2/9.0)
        self.subChecker.check_ellipsis_and_ending()
        self.set_progress(3/9.0)
        self.subChecker.check_gap_after_punctuation()
        self.set_progress(4/9.0)
        self.subChecker.check_ending_with_article()
        self.set_progress(5/9.0)
        self.subChecker.check_ending_with_preposition()
        self.set_progress(6/9.0)
        self.subChecker.check_multiple_whitespaces()
        self.set_progress(7/9.0)
        self.subChecker.check_orthography()
        self.set_progress(8/9.0)
        self.subChecker.check_final_n()
        self.set_progress(9/9.0)
        self.destroy()

    def process_messages(self):
        while Gtk.events_pending():
            Gtk.main_iteration_do(False)
