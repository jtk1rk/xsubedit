# -*- coding: utf-8 -*-
import regex as re
import platform
import enchant
from utils import isfloat, find_all_str

def remove_tags(text):
    return re.sub('<[^>]*>', '', text)

class cSubChecker(object):
    def __init__(self):
        self.final_n_words = [u'δε', u'μη', u'το', u'τη', u'ένα', u'αυτή']
        self.final_n_words = set([word.upper() for word in self.final_n_words])
        self.final_n_triggers = [u'α', u'ά', u'ε', u'έ', u'ι', u'ί', u'η', u'ή', u'υ', u'ύ', u'ϋ', u'ΰ', u'ο', u'ό', u'ω', u'ώ', u'ΐ']
        self.final_n_triggers += [u'κ', u'π', u'τ', u'γκ', u'μπ', u'ντ', u'ξ', u'ψ']
        self.final_n_triggers = tuple([word.upper() for word in self.final_n_triggers])
        self.article = []
        self.article += [u' ο', u' Ο', u'.Ο']
        self.article += [u' η', u' Η', u'.Η']
        self.article += [u' το', u' Το', u'.Το']
        self.article += [u' του', u' Του', u'.Του']
        self.article += [u' την', u' Την', u'.Την']
        self.article += [u' τον', u' Τον', u'.Τον']
        self.preposition = []
        self.preposition += [u' Με', u'.Με', u' με']
        self.preposition += [u' Σε', u'.Σε', u' σε']
        self.preposition += [u' Για', u'.Για', u' για']
        self.preposition += [u' Ως', u'.Ως', u' ως']
        self.preposition += [u' Πριν', u'.Πριν', u' πριν']
        self.preposition += [u' Προς', u'.Προς', u' προς']
        self.preposition += [u' Σαν', u'.Σαν', u' σαν']
        self.preposition += [u' Αντί', u'.Αντί', u' αντί']
        self.preposition += [u' Από', u'.Από', u' από']
        self.preposition += [u' Δίχως', u'.Δίχως', u' δίχως']
        self.preposition += [u' Έως', u'.Έως', u' έως']
        self.preposition += [u' Κατά', u'.Κατά', u' κατά']
        self.preposition += [u' Λόγω', u'.Λόγω', u' λόγω']
        self.preposition += [u' Μετά', u'.Μετά', u' μετά']
        self.preposition += [u' Μέχρι', u'.Μέχρι', u' μέχρι']
        self.preposition += [u' Παρά', u'.Παρά', u' παρά']
        self.preposition += [u' Χωρίς', u'.Χωρίς', u' χωρίς']
        self.preposition += [u' Εναντίον', u'.Εναντίον', u' εναντίον']
        self.preposition += [u' Εξαιτίας', u'.Εξαιτίας', u' εξαιτίας']
        self.preposition += [u' Ίσαμε', u'.Ίσαμε', u' ίσαμε']
        self.preposition += [u' Μεταξύ', u'.Μεταξύ', u' μεταξύ']
        self.preposition += [u' Στο', u'.Στο', u' στο']
        self.preposition += [u' Στον', u'.Στον', u' στον']
        self.preposition += [u' Στη', u'.Στη', u' στη']
        self.preposition += [u' Στην', u'.Στην', u' στην']
        self.preposition += [u' Ανά', u'.Ανά', u' ανά']
        self.preposition += [u' Άνευ', u'.Άνευ', u' άνευ']
        self.preposition += [u' Διά', u'.Διά', u' διά']
        self.preposition += [u' Εις', u'.Εις', u' εις']
        self.preposition += [u' Εκ', u'.Εκ', u' εκ']
        self.preposition += [u' Εκτός', u'.Εκτός', u' εκτός']
        self.preposition += [u' Εν', u'.Εν', u' εν']
        self.preposition += [u' Ένεκα', u'.Ένεκα', u' ένεκα']
        self.preposition += [u' Εντός', u'.Εντός', u' εντός']
        self.preposition += [u' Επί', u'.Επί', u' επί']
        self.preposition += [u' Κατόπιν', u'.Κατόπιν', u' κατόπιν']
        self.preposition += [u' Μείον', u'.Μείον', u' μείον']
        self.preposition += [u' Περί', u'.Περί', u' περί']
        self.preposition += [u' Πλην', u'.Πλην', u' πλην']
        self.preposition += [u' Προ', u'.Προ', u' προ']
        self.preposition += [u' Συν', u'.Συν', u' συν']
        self.preposition += [u' Υπέρ', u'.Υπέρ', u' υπέρ']
        self.preposition += [u' Υπό', u'.Υπό', u' υπό']
        self.preposition += [u' Χάριν', u'.Χάριν', u' χάριν']

        target_language = 'el' if platform.system() == 'Linux' else 'el_GR'

        if target_language not in enchant.list_languages():
            self.dict = None
        else:
            self.dict = enchant.Dict(target_language)

    def check_final_n(self, sub):
        word_watch = self.final_n_words
        triggers = self.final_n_triggers
        wordList = re.sub("[\W]", " ", remove_tags(sub.text), flags = re.UNICODE).split()
        notify = set()
        for i, word in enumerate(wordList):
            if i + 1 >= len(wordList):
                continue
            if word.upper() in word_watch and wordList[i + 1].startswith(triggers):
                notify.add(word)
        if len(notify) > 0:
            tmpstr = u','.join([item + u' ή ' + item + u'ν' for item in notify])
            sub.info = ('Text-Warning-Final-N', (tmpstr, []))
        else:
            sub.info = ('Text-Warning-Final-N', '')

    def check_time_gap(self, curSub, prevSub):
        # Checks for the 120ms gap between subtitles.
        # If there isn't one, the first subtitle is marked.
        if not(prevSub):
            return
        if int(curSub.startTime - prevSub.stopTime) < 120:
            prevSub.info = ('Audio-Error-120ms', (u'<span foreground="red">Κενό ως την επόμενη γραμμή &lt; 120ms</span>', []))
        else:
            prevSub.info = ('Audio-Error-120ms', '')

    def check_duration(self, curSub, nextSub):
        # Checks if subtitle rs is less than 27
        # and if it's duration is at least 1000
        if float(curSub.rs) >= 27:
            curSub.info = ('Audio-Error-RS', (u'<span foreground="red">Πολύ γρήγορη γραμμή</span>', []))
        else:
            curSub.info = ('Audio-Error-RS', '')
        if int(curSub.duration) < 1000:
            curSub.info = ('Audio-Error-Duration', (u'<span foreground="red">Διάρκεια &lt; 1 δευτερόλεπτο</span>', []))
        elif int(curSub.duration) > 6000:
            curSub.info = ('Audio-Error-Duration', (u'<span foreground="red">Διάρκεια &gt; 6 δευτερόλεπτα</span>', []))
        else:
            curSub.info = ('Audio-Error-Duration', '')

        # Check if there is enough space to make a line with rs 20
        if nextSub:
            if float(curSub.rs) > 20 and (nextSub.startTime > (curSub.stopTime + 120)):
                curSub.info = ('Audio-Warning-Better-RS', (u'<span foreground="red">Reading Speed &gt; 20 ενώ υπάρχει χώρος</span>', []))
            else:
                curSub.info = ('Audio-Warning-Better-RS', '')
        else:
            if float(curSub.rs) > 20:
                curSub.info = ('Audio-Warning-Better-RS', (u'<span foreground="red">Reading Speed &gt; 20 ενώ υπάρχει χώρος</span>', []))
            else:
                curSub.info = ('Audio-Warning-Better-RS', '')

    def check_ellipsis_and_ending(self, curSub, prevSub):
        # Checks if all ... are unicode ellipsis char
        # and if all ellipses are consistent with next subtitle
        # Also checks subtitle ending
        if '...' in curSub.text:
            curSub.info = ('Text-Error-Ellipsis-Char', (u'Τα αποσιωπητικά είναι 3 χαρακτήρες', []))
        else:
            curSub.info = ('Text-Error-Ellipsis-Char', '')
        if not remove_tags(curSub.text).strip().endswith((u'.', u'»', u'…', u'...', u';', u'!')):
            curSub.info = ('Text-Error-Ending', (u'Η γραμμή πρέπει να τελειώνει με . ή » ή … ή ; ή !',  []))
        else:
            curSub.info = ('Text-Error-Ending', '')

        if not(prevSub):
            return

        if remove_tags(prevSub.text).strip().endswith((u'…', u'...')) and not(remove_tags(curSub.text).strip().startswith((u'…', u'...')) or any(l.startswith((u'- ...', u'-...', u'- …', u'-…')) for l in remove_tags(curSub.text).splitlines())):
            curSub.info = ('Text-Error-Ellipsis-Missing-Start', (u'Η γραμμή έπρεπε να αρχίζει με …',  []))
        else:
            curSub.info = ('Text-Error-Ellipsis-Missing-Start', '')

        if not remove_tags(prevSub.text).strip().endswith((u'…', u'...')) and (remove_tags(curSub.text).strip().startswith((u'…', u'...')) or any(l.startswith((u'- ...', u'-...', u'- …', u'-…')) for l in remove_tags(curSub.text).splitlines())):
            prevSub.info = ('Text-Error-Ellipsis-Missing-End', (u'Η γραμμή έπρεπε να τελειώνει με …', []))
        else:
            prevSub.info = ('Text-Error-Ellipsis-Missing-End', '')

    def check_gap_after_punctuation(self, curSub):
        # Checks for gaps after punctuations
        plist = [m.start() for m in re.finditer('[,\.-][^\W\d_]',  remove_tags(curSub.text.strip()), flags = re.UNICODE)]
        if len(plist) > 0:
            curSub.info = ('Text-Error-Whitespace-Missing', (u'Λείπει κενό μετά από σημείο στίξης ή παύλα.', []))
        else:
            curSub.info = ('Text-Error-Whitespace-Missing', '')

    def check_ending_with_article(self, sub):
        article = self.article
        lines = sub.text.splitlines()
        ends_with_article = False
        for line in lines:
            if remove_tags(line.strip()).endswith(tuple(article)):
                ends_with_article = True
        if ends_with_article:
            sub.info = ('Text-Error-Line-Ends-With-Article', (u'Η γραμμή τελειώνει με άρθρο;', []))
        else:
            sub.info = ('Text-Error-Line-Ends-With-Article', '')

    def check_ending_with_preposition(self, sub):
        preposition = self.preposition
        lines = sub.text.splitlines()
        ends_with_preposition = False
        for line in lines:
            ends_with_preposition = False
            if remove_tags(line.strip()).endswith(tuple(preposition)):
                ends_with_preposition = True
        if ends_with_preposition:
            sub.info = ('Text-Error-Ends-With-Preposition', (u'Πρόθεση στο τέλος γραμμής.', []))
        else:
            sub.info = ('Text-Error-Ends-With-Preposition', '')

    def check_multiple_whitespaces(self, sub):
        if sub.text.find('  ') != -1:
            sub.info = ('Text-Error-Multiple-Whitespaces', (u'Πολλαπλά κενά', []))
        else:
            sub.info = ('Text-Error-Multiple-Whitespaces', '')

    def check_orthography(self, sub):
        if not self.dict:
            return

        wordList = re.sub("[\W]", " ", remove_tags(sub.text), flags = re.UNICODE).split()
        errorList = [word for word in wordList if (not self.dict.check(word)) and (not isfloat(word))]
        errorCoord = []
        for word in errorList:
            coords = find_all_str(sub.text, word)
            errorCoord += [coord for coord in coords]

        if len(errorList) > 0:
            sub.info = ('Text-Error-Orthography', (u'Ορθογραφία: '+','.join(w for w in errorList), errorCoord))
        else:
            sub.info = ('Text-Error-Orthography', '')

    def check_dialog_dash(self, sub):
        text = sub.text.splitlines()
        if len(text) < 2:
            return
        if (text[0].startswith('-') and not text[1].startswith('-')) or (not text[0].startswith('-') and text[1].startswith('-')):
            sub.info = ('Text-Error-Dialog_Dash', (u'FMT: Λείπει παύλα διαλόγου σε μια γραμμή;', []))
        else:
            sub.info = ('Text-Error-Dialog_Dash', '')

    def check_empty_line(self, sub):
        if sub.text == '':
            sub.info = ('Audio-Error-Empty_Line', (u'<span foreground="red">Κενή γραμμή</span>', []))
        else:
            sub.info = ('Audio-Error-Empty_Line', '')

#  **************************************** Text-XProof-CHECKS ****************************************
    def xp_single_sub_check(self, sub, regex, error_type, color, info_text, reflags):
        res = re.finditer(regex, sub.text, flags= re.U | reflags if reflags != None else re.UNICODE)
        res_list = []
        for item in res:
            res_list.append((item.start(), item.end()))
        if len(res_list) > 0:
            #sub.info = (error_type, (u'<span foreground="'+color+'">' + info_text + u'</span>', res_list))
            sub.info = (error_type, (info_text, res_list))
        else:
            sub.info = (error_type, '')

    def xproof_checks(self, prevSub, curSub, nextSub):
        xps = self.xp_single_sub_check
        #fwnhen_tonismeno = u"[ΆάΈέΉήΊίΌόΎύΏώ]"
        #symfwno = u"[βγδζθκλμνξπρστφχψ]"
        #fwnhen_atono = u"(?:[αεο]ι|ου|[αε]υ|[αεηιουωϊϋ])"
        #egklitiko = u"\\b(?:[μσ](?:ου|ας)|τους?|[μσ]ε|τ(?:ον?|ην?|ης|ες|α))\\b"
        #symfwno_teliko = u"[ςν]"
        thene_n = u"(?:[αάεέηήιίοόυύωώκπτξψ]|γκ|ντ|μπ)"

        #xps(curSub, u"(?<=[ΆάΈέΉήΊίΌόΎύΏώ]\\w+)([άέήίόύώ])(?!\\w*\\s(?:[σμ](?:ας|ε)|[μστ]ο[υν]|τ[οαη]|τ[ηε][ςν]|τους)\\b)", 'Text-XProof-dual_accent', 'black', u'Τόνος εγκλιτικού χωρίς εγκλιτικό;', re.M | re.I)
        #xps(curSub, u"("+fwnhen_tonismeno+symfwno+"*"+fwnhen_atono+symfwno+"*)("+fwnhen_atono+"?)(?="+symfwno_teliko+"?\\s"+egklitiko+")", 'Text-XProof-missing_dual_accent', 'black', u'Λείπει τόνος εγκλιτικού; (σημείωση: η βάρδια είναι δισύλλαβη (βάρ-δγια, όχι βάρ-δι-α, άρα δεν παίρνει τόνο εγκλιτικού)', re.M | re.I)

        # Substituted by my own searches
        #xps(curSub, u'^([^-].)(?=.*\\n- )', 'Text-XProof-bol2_dash_1', 'black', u'FMT: Λείπει παύλα διαλόγου από την πρώτη γραμμή;', re.M | re.I)

        # Modified
        xps(curSub, u'([εέ][ιί]?)τε\\b', 'Text-XProof-second_plural', 'black', u"Είναι όντως Βʹ πληθυντικό πρόσωπο; («εσείς παίζετε»)", re.M | re.I)
        xps(curSub, u'([εέ][ιί]?)ται\\b', 'Text-XProof-third_singular', 'black', u'Είναι όντως Γʹ ενικό/πληθυντικό πρόσωπο; («αυτό χαίρεται» ή «εσείς να χαίρετε»;)', re.M | re.I)
        xps(curSub, u"(κατ(?:'\\s)?αρχ)(?:άς|ήν)", 'Text-XProof-initially_principle', 'black', u"VRFY: Κατ' αρχάς/καταρχάς (αρχικά) ή κατ' αρχήν/καταρχήν (κατά κανόνα);", re.M | re.I)
        xps(curSub, u'((?:δι|τρι))σ(?=δι[άα])', 'Text-XProof-dimensions', 'black', u'FIX: Διδιάστατος, τριδιάστατος, τετραδιάστατος, όχι δισδιά- τρισδιά- τετρακισδιάστατος', re.M | re.I)

        # Original
        xps(curSub, u'(?<!-)\\s…', 'Text-XProof-space_ellipsis', 'black', u'Διαγραφή κενού πριν από αποσιωπητικά', re.M)
        xps(curSub, u'(?<=- )…[ ]', 'Text-XProof-space_ellipsis_space', 'black', u'Παύλα, κενό, αποσιωπητικά, περιττό κενό', re.M)
        xps(curSub, u'(?i)(?<=\\bν)ο(?=ιώ[θσ])', 'Text-XProof-feel_now', 'black', u'Από το «γιγνώσκω», όχι «νοιάζομαι» (Μπαμπινιώτης) (ενεστώτας, υποτ αορ)', re.M)
        xps(curSub, u'(?i)(?<=\\b[έε]ν)ο(?=ιω[θσ])', 'Text-XProof-felt_before', 'black', u'Από το «γιγνώσκω», όχι «νοιάζομαι» (Μπαμπινιώτης) (παρατ, αόρ)', re.M)
        xps(curSub, u"(?<=[αάεέηήιίοόυύωώ])'(\\s)(?=[βγδζθκλμνξπρστφχψ])", 'Text-XProof-misplaced_apostrophe_1', 'black', u'Μήπως η απόστροφος να μπει δίπλα στο σύμφωνο; (αφαίρεση)', re.M | re.I)
        xps(curSub, u"(?<=[βγδζθκλμνξπρστφχψ])(\\s)'(?=[αάεέηήιίοόυύωώ])", 'Text-XProof-misplaced_apostrophe_2', 'black', u'Μήπως η απόστροφος να μπει δίπλα στο σύμφωνο; (έκθλιψη)', re.M | re.I)
        xps(curSub, u"(?<=\\bτ)ο(?=ν\\s\\w+ων\\b)", 'Text-XProof-plural_genitive', 'black', u'Γενική πληθυντικού, λάθος άρθρο;',  re.M | re.I)
        xps(curSub, u"Που\\b(?=[^.;!]*;)", 'Text-XProof-where_question', 'black', u'Μάλλον ερωτηματικό "πού" (σε ποιο μέρος), έχει ερωτηματικό μετά.', re.M | re.I)
        xps(curSub, u"Πως\\b(?=[^.;!]*;)", 'Text-XProof-how_question', 'black', u'Μάλλον ερωτηματικό "πώς" (με ποιον τρόπο), έχει ερωτηματικό μετά.', re.M | re.I)
        xps(curSub, u"(?<=\\b[πΠ])ω(?=ς\\sνα\\b)", 'Text-XProof-how_to', 'black', u'«Πώς να»: σχεδόν σίγουρα το «πώς» τονίζεται (με ποιον τρόπο).', re.M | re.I)
        xps(curSub, u"(του)(?=\\s\\w+ς\\b)", 'Text-XProof-dative_plural', 'black', u'Είναι αιτιατική πληθυντικού και ξεχάσαμε το "ς" από το «τους»;', re.M | re.I)
        xps(curSub, u"\\bτο τι\\b", 'Text-XProof-the_what', 'black', u'Ίσως ταιριάζει «ό,τι».', re.I | re.M)
        xps(curSub, u"(?m)^-\\s", 'Text-XProof-their_dialog', 'black', u'XXX: εισαγωγή διαλόγου', re.M)
        xps(curSub, u"^<i>-\\s?", 'Text-XProof-eas_my_life', 'black', u'Τα &lt;i&gt; μετά από άνοιγμα διαλόγου, παρακαλώ. Ευχαριστώ.', re.M)
        xps(curSub, u"\\.\\.\\.", 'Text-XProof-ellipsis_on', 'black', u'Οι τρεις τελείες γίνονται ένας.', re.M)
        xps(curSub, u"(?<=…)\\.+", 'Text-XProof-ellipsis_plus_period', 'black', u'Διαγραφή τελειών μετά από αποσιωπητικά.', re.M)
        xps(curSub, u"\\?", 'Text-XProof-latin_question_mark', 'black', u'Λατινικό ερωτηματικό σε ελληνικό.', re.M)
        xps(curSub, u"^ +| +$", 'Text-XProof-trim', 'black', u'Διαγραφή των κενών διαστημάτων στην αρχή και στο τέλος μιας γραμμής.', re.M)
        xps(curSub, u"  +", 'Text-XProof-single_spaces', 'black', u'Πολλαπλά κενά διαστήματα γίνονται ένα.', re.M | re.I)
        xps(curSub, u"\\s+,", 'Text-XProof-space_comma', 'black', u'Διαγραφή κενών πριν από κόμμα.', re.M | re.I)
        xps(curSub, u'\\s(["»])$', 'Text-XProof-ends_space_quote', 'black', u'Κενό πριν από εισαγωγικά στο τέλος αράδας.', re.M | re.I)
        xps(curSub, u",(?=\\S)", 'Text-XProof-comma_no_space', 'black', u'Εισαγωγή κενού μετά από κόμμα.', re.M | re.I)
        xps(curSub, u"(\\b[όο],)\\s(τι\\b)", 'Text-XProof-that_comma', 'black', u'Διαγραφή κενού σε «ό, τι»', re.M | re.I)
        xps(curSub, u"(?<=\\bο),(?=τιδήποτε)", 'Text-XProof-whatever', 'black', u'Διόρθωση του «ο,τιδήποτε».', re.M | re.I)
        xps(curSub, u"\\bοτι\\b", 'Text-XProof-that_0a', 'black', u'Τονισμός ατόνιστου «οτι».', re.M | re.I)
        xps(curSub, u"(?<=\\bαπό\\sό)(?<=τι\\b)", 'Text-XProof-from_whatever', 'black', u'Από ό,τι, ποτέ από ότι.', re.M | re.I)
        xps(curSub, u",…", 'Text-XProof-comma_ellipsis', 'black', u'Διαγραφή κόμματος πριν από αποσιωπητικά.', re.M | re.I)
        xps(curSub, u'\\bδε(?=\\s[«"]?'+thene_n+')', 'Text-XProof-not_n_should', 'black', u'ΔΕ/ΔΕΝ: Γραμματικώς ορθή προσθήκη του "ν" στο «δε».', re.M | re.I)
        xps(curSub, u'\\bδεν(?=\\s(?!["«]?'+thene_n+'))', 'Text-XProof-not_n_shouldnt', 'black', u'ΔΕ/ΔΕΝ: Γραμματικώς ορθή αφαίρεση του "ν" από το «δεν».', re.M | re.I)
        xps(curSub, u"\\bδε\\b", 'Text-XProof-always_n_shouldnt', 'black', u'ΔΕΝ/+: Πρόταση μετατροπής σε «δεν» αν είναι «δε».', re.M | re.I)
        xps(curSub, u'\\bμη(?=\\s["«]?'+thene_n+')', 'Text-XProof-donot_n_should', 'black', u'', re.M | re.I)
        xps(curSub, u'\\bμην(?=(?:[.!;,]|["«]?\\s(?![αάεέηήιίοόυύωώκξπτψ]|μπ|ντ|γκ)))', 'Text-XProof-donot_n_shouldnt', 'black', u'ΜΗ: Γραμματικώς ορθή αφαίρεση του "ν" από το "μην".', re.M | re.I)
        xps(curSub, u'(\\bσ?τη)(?=\\s["«]?'+thene_n+')', 'Text-XProof-fem_the_should', 'black', u'Γραμματικώς ορθή προσθήκη του "ν" στο "τη".', re.M | re.I)
        xps(curSub, u'(?<=\\bείσ)ασ(?=τε\\b)', 'Text-XProof-you_are_plural', 'black', u'SUGG: Εσείς *είστε* το ορθό. Επίσης πιο σύντομο.', re.M | re.I)
        xps(curSub, u'(?<=\\b[μσ])(ε)(\\s)(?=[σμ][έε]να\\b)', 'Text-XProof-to_with_me_you', 'black', u"FIX: Μ' εμένα, μ' εσένα, σ' εμένα, σ' εσένα", re.M | re.I)
        xps(curSub, u'\\Bάνε\\b', 'Text-XProof-they_ane', 'black', u'SUGG: αν είναι Γʹ πληθ. πρόσωπο, πιο σωστό είναι το «-ούν»', re.M | re.I)
        xps(curSub, u'(?<=\\bπερ)εταί(?=ρω\\b)', 'Text-XProof-further', 'black', u'FIX: Ορθογραφικώς ορθό το «περαιτέρω».', re.M | re.I)
        xps(curSub, u'\\b(?:γιός?|γιοί|γιών|γιούς?)\\b', 'Text-XProof-son', 'black', u'FIX: «γιος» είναι μονοσύλλαβο και δεν τονίζεται', re.M | re.I)
        xps(curSub, u'(?<=\\bεν[ώω]πι)([ώω])(?=ν\\b)', 'Text-XProof-against', 'black', u'FIX: Ορθογραφικώς ορθό το «ενώπιον».', re.M | re.I)
        xps(curSub, u"\\b(?<=[Κκ])αι(\\s)'?γ[ωώ]\\b", 'Text-XProof-me_too', 'black', u'FIX: «Κι εγώ».', re.M | re.I)
        xps(curSub, u"\\b(?<=[Κκ])αι(\\s)'?σ[υύ]\\b", 'Text-XProof-you_too', 'black', u'FIX: «Κι εσύ».', re.M | re.I)
        xps(curSub, u'^"|(?<=\\s)"', 'Text-XProof-greek_quotes_start', 'black', u'FMT: Αλλαγή εισαγωγικών (πιο πιθανό το "«").', re.M | re.I)
        xps(curSub, u'(?:"$)|(?:"(?=[\\s.,!;…]))', 'Text-XProof-greek_quotes_end', 'black', u'FMT: Αλλαγή εισαγωγικών (πιο πιθανό το "»").', re.M | re.I)
        xps(curSub, u"(\\w)'(\\w)", 'Text-XProof-single_quote_squeeze', 'black', u'FMT: Κολλημένη απόστροφος.', re.M | re.I)
        xps(curSub, u'\\bσα\\b', 'Text-XProof-like_n', 'black', u'FIX: Προσθήκη του "ν" στο τέλος του "σα".', re.M | re.I)
        xps(curSub, u'(?<=[.;!]\\s)\\p{Ll}', 'Text-XProof-period_start_lc', 'black', u'Αρχή πρότασης με πεζό;', re.M)
        xps(curSub, u'\\b([Σσ])υνέλ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_syn_l', 'black', u'Λανθασμένη αύξηση σε προστακτική; (συν+λ)', re.M | re.I)
        xps(curSub, u'\\b([Σσ])υνέ(?=[^λ]\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_syn', 'black', u'Λανθασμένη αύξηση σε προστακτική; (συν)', re.M | re.I)
        xps(curSub, u'\\b([Εε]π)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_epi', 'black', u'Λανθασμένη αύξηση σε προστακτική; (επί)', re.M | re.I)
        xps(curSub, u'\\b([Εε]παν)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_epi_an', 'black', u'Λανθασμένη αύξηση σε προστακτική; (επί+ανά)', re.M | re.I)
        xps(curSub, u'\\b([Ππ]αρ)[έή](?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_para', 'black', u'Λανθασμένη αύξηση σε προστακτική; (παρά)', re.M | re.I)
        xps(curSub, u'\\b([Υυ]π)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_ypo', 'black', u'Λανθασμένη αύξηση σε προστακτική; (υπό)', re.M | re.I)
        xps(curSub, u'\\b([Αα]ντ)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_anti', 'black', u'Λανθασμένη αύξηση σε προστακτική; (αντί)', re.M | re.I)
        xps(curSub, u'\\b([Ππ]ρ)οσέ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_pros', 'black', u'Λανθασμένη αύξηση σε προστακτική; (προς)', re.M | re.I)
        xps(curSub, u'\\b([Αα]ν)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_ana', 'black', u'Λανθασμένη αύξηση σε προστακτική; (ανά)', re.M | re.I)
        xps(curSub, u'\\b([Δδ]ι)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_dia_1', 'black', u'Λανθασμένη αύξηση σε προστακτική; (διά: διέ–)', re.M | re.I)
        xps(curSub, u'\\b([Δδ]ι)ε(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_dia_2', 'black', u'Λανθασμένη αύξηση σε προστακτική; (διά: διε–)', re.M | re.I)
        xps(curSub, u'\\b([Αα]π)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_apo', 'black', u'Λανθασμένη αύξηση σε προστακτική; (από)', re.M | re.I)
        xps(curSub, u'\\b([Εε]ξ)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_ek', 'black', u'Λανθασμένη αύξηση σε προστακτική; (εκ)', re.M | re.I)
        xps(curSub, u'\\b([Κκ]ατ)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_kata', 'black', u'Λανθασμένη αύξηση σε προστακτική; (κατά)', re.M | re.I)
        xps(curSub, u'\\b([Μμ]ετ)έ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_meta', 'black', u'Λανθασμένη αύξηση σε προστακτική; (μετά)', re.M | re.I)
        xps(curSub, u'\\b([Ππ]ερ)ιέ(?=\\w+[εέ]\\b)', 'Text-XProof-wrong_imperative_peri', 'black', u'Λανθασμένη αύξηση σε προστακτική; (περί)', re.M | re.I)
        xps(curSub, u'(?<=\\bεπικεφαλ)(?:είς|ών|ούς|ή)\\b', 'Text-XProof-head', 'black', u'Το «επικεφαλής» είναι άκλιτο (επί κεφαλής).', re.M | re.I)
        xps(curSub, u'(?<=[όο]ντ)ουσ(?=αν\\b)', 'Text-XProof-past_cont_nonoff', 'black', u"Γʹ πληθ. παρατατικού: «-όνταν» είναι το σωστό και πιο σύντομο.", re.M | re.I)
        xps(curSub, u"'(?<=[ΆΈΉΊΌΎΏ])", 'Text-XProof-apostrophe_accented', 'black', u'Απόστροφος πριν από τονισμένο κεφαλαίο.', re.M)
        xps(curSub, u"\\bν\\b(?!')", 'Text-XProof-single_n', 'black', u'Σκέτο «ν» λέξη από μόνο του;', re.M | re.I)
        xps(curSub, u'\\.\\.', 'Text-XProof-two_periods', 'black', u'Ακριβώς δύο τελείες.', re.M | re.I)
        xps(curSub, u'\\b[ηή]\\b', 'Text-XProof-h_h', 'black', u'Άρθρο «η» ή διαζευκτικό «ή»;', re.M | re.I)
        xps(curSub, u'\\.(?=\\s\\p{Ll})', 'Text-XProof-period_start_lc2', 'green', u'VRFY: Μήπως εδώ ήθελε κόμμα αντί για τελεία;', re.M)
        xps(curSub, u'ν[όο]μ[όο](?=ς?\\b)', 'Text-XProof-law_prefecture', 'green', u'VRFY: Νόμος και τάξη ή νομός Αττικής;', re.M | re.I)
        xps(curSub, u'\\b(σ?τη)ν(?=\\s[«"]?(?!'+thene_n+'))', 'Text-XProof-fem_the_shouldnt', 'black', u'Γραμματικώς ορθή αφαίρεση του "ν" από το «την/στην».', re.M | re.I)
        xps(curSub, u"\\b(σ)(τ(?:[ηο]ν?|α|ους|ις))(?=\\s'?\\p{Ll}\\w+(?:[ωώ]|[αυ][ιν]?|ει?)\\b)", 'Text-XProof-not_into', 'green', u"VRFY: «Στο»=«Εις το» (+ επίθετο/ουσιαστικό) ή «Σ' το»=«Σου το» (+ ρήμα);", re.M | re.I)
        xps(curSub, u'\\b([Ππ]ο)υ\\b', 'Text-XProof-where_1', 'black', u'Είναι ορθώς ατόνιστο το «που»;\n    (δηλαδή: ο/η/το οποίος/α/ο); Επίσης, μήπως είναι «όπου» (=«εκεί που»);', re.M | re.I)
        xps(curSub, u'\\b([Ππ]ο)ύ\\b', 'Text-XProof-where_2', 'green', u'VRFY: Είναι ορθώς τονισμένο το «πού» (δηλαδή: μιλάμε για τόπο);', re.M | re.I)
        xps(curSub, u'\\bπ[όο]δι[άα]\\b', 'Text-XProof-feet_apron', 'green', u'VRFY: τα πόδια μου πονούν ή η ποδιά μου με στενεύει;', re.M | re.I)
        xps(curSub, u'\\bόρ(?:οι|η)\\b', 'Text-XProof-terms_mountains', 'green', u'VRFY: οι όροι του συμβολαίου ή σαν τα ψηλά όρη;', re.M | re.I)
        xps(curSub, u'(?<=\\bχ)(εί|ή)(?=(?:ρας?|ρες)\\b)', 'Text-XProof-hand_widow', 'green', u'VRFY: η χείρα του Θεού ή η χήρα του συγχωρεμένου;', re.M | re.I)
        xps(curSub, u'(?:\\b[Ββ]ρ)[άα]δ[υι][άα]\\b', 'Text-XProof-evenings_evening', 'green', u'VRFY: μια βραδιά ή πολλά βράδια;', re.M | re.I)
        xps(curSub, u'\\bμύες\\b', 'Text-XProof-muscles', 'green', u'VRFY: οι μύες, των μυών, τους μυς· αν αιτιατική, φεύγει το "ε".', re.M | re.I)
        xps(curSub, u'\\b([Ππ])ως\\b', 'Text-XProof-what_1', 'green', u'VRFY: Ατόνιστο «πως» (πως=ότι, πώς=με ποιον τρόπο;)', re.M | re.I)
        xps(curSub, u'\\b([Ππ])ώς\\b', 'Text-XProof-what_2', 'green', u'VRFY: Τονισμένο «πώς» (πώς=με ποιον τρόπο;, πως=ότι).', re.M | re.I)
        xps(curSub, u'\\b[Όό]τι\\b', 'Text-XProof-that_is_correct', 'green', u'VRFY: Σωστό «ότι»; (ότι=πως, ό,τι=οτιδήποτε).', re.M | re.I)
        xps(curSub, u'\\b[Όό],τι\\b', 'Text-XProof-whatever_is_correct', 'green', u'VRFY: Σωστό «ό,τι»; (ό,τι=οτιδήποτε, ότι=πως).', re.M | re.I)
        xps(curSub, u"\\b([μσ])ε\\s'", 'Text-XProof-bad_apo_1', 'green', u'VRFY: Μπήκε σωστά η απόστροφος; (με/σε)', re.M | re.I)
        xps(curSub, u'(?<=\\b[ΜμΣσΤτ]ο)ύ\\b', 'Text-XProof-mine_thine_accented_m', 'green', u'VRFY: Ορθώς τονισμένο εγκλιτικό; (αρσενικό/ουδέτερο)', re.M | re.I)
        xps(curSub, u'(?<=\\p{Ll})\\sαν\\b(?=.*,)', 'Text-XProof-comma_if_comma', 'green', u'VRFY: Ίσως θέλει κόμμα πριν το «αν» (υποπρόταση).', re.M | re.I)
        xps(curSub, u'(?<=\\b[Ττ])ή(?=ς\\b)', 'Text-XProof-mine_thine_accented_f', 'green', u'VRFY: Ορθώς τονισμένο εγκλιτικό; (θηλυκό)', re.M | re.I)
        xps(curSub, u'\\bτο\\s(?:ότι|πως)\\b', 'Text-XProof-verbose_that', 'green', u'VRFY: Ίσως ταιριάζει «που» αντί για «το ότι» (κομμάτι αμερικανισμός).\n   Δείτε μήπως μπορείτε να χρησιμοποιήσετε ουσιαστικό αντί για ρήμα.', re.M | re.I)
        xps(curSub, u'\\bτο (πο[υύ])\\b', 'Text-XProof-verbose_where', 'green', u'VRFY: Ίσως ταιριάζει σκέτο «πού», αν μιλάμε για τόπο.', re.M | re.I)
        xps(curSub, u'\\bπολ(?:ύ|λή|λοί)\\b', 'Text-XProof-much_a_lot', 'green', u'VRFY: «πολύ» + ρήμα ή επίθετο (θέλω, καλό) ή «πολλή» + θηλυκό ουσιαστικό (δουλειά)\n   ή «πολλοί» + αρσενικό ουσιαστικό (άνθρωποι);', re.M | re.I)
        xps(curSub, u'\\bπο?ι[όο]\\b', 'Text-XProof-pjio', 'green', u'VRFY: «πιο πολύ» ή «ποιο πράγμα»; (κανένα τους δεν τονίζεται!)', re.M | re.I)
        xps(curSub, u'\\bψ[ιη]λ([όή]ς?)\\b', 'Text-XProof-thin_tall', 'green', u'VRFY: «ψιλή» (λεπτή) ή «ψηλή» (όχι κοντή).', re.M | re.I)
        xps(curSub, u'(?<=\\bλόγ)ο\\b', 'Text-XProof-because_of', 'green', u'VRFY: Μήπως εννοεί «λόγω» (εξ αιτίας);', re.M | re.I)
        xps(curSub, u'(?<=\\bβάσ)η\\b(?=\\sτ)', 'Text-XProof-based_on', 'green', u'VRFY: Μήπως εννοεί «βάσει» (με βάση);', re.M | re.I)
        xps(curSub, u'(?<=ραλ)(ει|η)(?=φθ(?:είς?|ούν)\\b)', 'Text-XProof-accept_miss_ambiguity', 'green', u'VRFY: Παραλείπομαι = θα παραλΕΙφθώ ή παραλαμβάνομαι = θα παραλΗφθώ;', re.M | re.I)
        xps(curSub, u'(εί|ή|ί)(?=στε\\b)', 'Text-XProof-imperative_or_passive', 'green', u'VRFY: Είναι προστακτική αορίστου ενεργητικής φωνής (οδηγήστε τον στην φυλακή ή συνεχίστε την αφήγηση)\n   ή ενεστώτας παθητικής φωνής (εσείς οδηγείστε στο χάος);', re.M | re.I)
        xps(curSub, u'(?<=\\bδουλ)εία(?=ς?\\b)', 'Text-XProof-slavery', 'green', u'VRFY: εδώ μιλάει για τη δουλεία ή για τη δουλειά;', re.M | re.I)
        xps(curSub, u'(?<=\\bπαιδ)ία\\b', 'Text-XProof-children_play ', 'green', u'VRFY: τα παιδία παίζει ή τα παιδιά εννοεί;', re.M | re.I)
        xps(curSub, u'\\b[άα]λλ?[άα]\\b', 'Text-XProof-but_other', 'green', u'VRFY: αλλά (όμως, but), άλλα (έτερα, other) ή αλά (από το γαλλικό à la);', re.M | re.I)
        xps(curSub, u'\\b[άα]λλο[υύ]\\b', 'Text-XProof-elsewhere_others', 'green', u"VRFY: άλλου (sb else's) ή αλλού (elsewhere);", re.M | re.I)
        xps(curSub, u'\\b[όο]π[όο]τε\\b', 'Text-XProof-anytime_thus', 'green', u'VRFY: «Όποτε κάνω κάτι»=«κάθε φορά που» ή «οπότε βγάζω αυτό το συμπέρασμα»=«συνεπώς»;', re.M | re.I)
        xps(curSub, u'\\bγε?ια\\b', 'Text-XProof-for_bye', 'green', u'VRFY: «Για να σου πω» ή «Γεια σου κι εσένα»;', re.M | re.I)
        xps(curSub, u'\\bπ[όο]σ[όο]\\b', 'Text-XProof-much_amount', 'green', u'VRFY: «Χρηματικό ποσό» ή «Πόσο πολύ μου έλειψες»;', re.M | re.I)
        xps(curSub, u'\\bα[ίι]τ[ίι]α\\b', 'Text-XProof-cause_reasons', 'green', u'VRFY: «Η αιτία της καταστροφής» ή «τα αίτια του πολέμου»;', re.M | re.I)
        xps(curSub, u'\\bχ[άα]λι[άα]\\b', 'Text-XProof-mess_carpets', 'green', u'VRFY: «Χάλια η κατάσταση» ή «πήγα τα χαλιά για καθάρισμα»;', re.M | re.I)
        xps(curSub, u'\\b(?:αν|να)\\b', 'Text-XProof-if_to', 'green', u'VRFY: «αν» ή «να»;', re.M | re.I)
        xps(curSub, u'\\wς\\w', 'Text-XProof-sigma_teliko', 'green', u'VRFY: σίγμα τελικό στη μέση λέξης;', re.M)
        xps(curSub, u'^-\\s([αάβγδεέζηήθιίκλμνξοόπρστυύφχψωώ])', 'Text-XProof-dialog_small', 'black', u'Αρχή διαλόγου με μικρό χωρίς αποσιωπητικά', re.M)
        xps(curSub, u"(\\bεξ)'", 'Text-XProof-ex_no_apostrophe', 'black', u"Το εξ δεν παίρνει απόστροφο! (εκτός αν είναι το έξω → έξ' από 'δώ)", re.M | re.I)
        xps(curSub, u"(?<=\\bκ)αι(\\s)'?(?=[μσ](?:ένα|άς)\\b)", 'Text-XProof-and_me_you', 'black', u'FIX:Κι εμένα, κι εσένα, κι εμάς, κι εσάς.', re.M | re.I)
        xps(curSub, u'(\\b(?:για|από)\\s)([μσ](?:ένα|[αά]ς))', 'Text-XProof-for_me_with', 'black', u"ΓΙΑ/ΑΠΟ 'ΜΕΝΑ: δεν έχει απόστροφο, ας βάλουμε μία.", re.M | re.I)
        xps(curSub, u'\\bπ[όο]τ[έε]\\b', 'Text-XProof-whenever_never', 'green', u'VRFY: «Πότε θα κάνει ξαστεριά;» ή «Ποτέ δεν θα πεθάνουμε, κουφάλα νεκροθάφτη»;', re.M | re.I)
        xps(curSub, u'(?<=σ)[ωο](?=ρ(?:ός?|ο[ίύ]ς?|ών)\\b)', 'Text-XProof-corpse_heap', 'green', u'VRFY: είναι ΜΙΑ σορός (το πτώμα) και ΕΝΑΣ σωρός (τα πράγματα στο γραφείο μου).', re.M | re.I)
        xps(curSub, u'\\bπο?ι[αά]\\b', 'Text-XProof-pjia', 'green', u'VRFY: «τώρα πια» ή «ποια είναι αυτή»; (κανένα τους δεν τονίζεται!)', re.M | re.I)
        xps(curSub, u'\\bσυν[έε]δρ[ίι]α\\b', 'Text-XProof-session_convention', 'green', u'VRFY: μία συνεδρία με ψυχίατρο ή πολλά συνέδρια με συνέδρους; ιδού η απορία.', re.M | re.I)
        xps(curSub, u'\\bάνηκε\\b', 'Text-XProof-belonged', 'black', u'FIX: «ανήκε» είναι το σωστό', re.M | re.I)
        xps(curSub, u'\\b[Δδ][ίι]κ[ήη](?=ς?\\b)', 'Text-XProof-trial_mine', 'green', u'VRFY: η δίκη του αιώνα ή η δική μου ευκαιρία;', re.M | re.I)
        xps(curSub, u"(?<=\\b(?:για|από)\\s)'([μσ])α(?=ς\\b)", 'Text-XProof-for_us_you_accent', 'black', u"ΓΙΑ/ΑΠΟ 'ΜΑΣ/'ΣΑΣ: αν αφαίρεση, τότε παίρνει τόνο.", re.M | re.I)
        xps(curSub, u"(?<=\b(?:για|από) )'(?=[μσ](?:ένα|[αά]ς))", 'Text-XProof-for_me_without', 'black', u"ΓΙΑ/ΑΠΟ ΜΕΝΑ: έχει απόστροφο, ας τη σβήσουμε.", re.M | re.I)
        xps(curSub, u'\\b([εέ]να|σ?το)(?=\\s[«"]?\\w+[αοηάήό]\\b)', 'Text-XProof-male_final_n', 'black', u'Μήπως θέλει "ν" επειδή ακολουθεί αρσενικό επίθετο ή ουσιαστικό;', re.M | re.I)
        xps(curSub, u'(?<=\\b[Κκ])ανά(?=ς?\\b)', 'Text-XProof-any_male_neutral', 'black', u'«Κάνα ψιλό», όχι «γάμος στην Κανά».', re.M | re.I)
        xps(curSub, u"[΄'][ΑAΕEΗHIΙΟOYΥΩ]", 'Text-XProof-apostrophe_tonos', 'black', u"Απόστροφος αντί για τόνος;", re.M | re.I)
        xps(curSub, u'«(?=[\\s;.!,])', 'Text-XProof-incorrect_closing_quote', 'black', u'Άνοιγμα εισαγωγικών πριν από στίξη ή κενό;', re.M | re.I)
        xps(curSub, u'(\\bκι)(?=,)', 'Text-XProof-short_and', 'black', u'«Κι» πριν από στίξη.', re.M | re.I)
        xps(curSub, u"(?<=\\bσ')\\s(?=τ(?:[οη]ν?|α|ους|ις))", 'Text-XProof-my_sto', 'black', u"XXX: Τι να το κάνεις το κενό στο \"σ' το\"; ☺", re.M | re.I)
        xps(curSub, u'(?<=^<i>)…', 'Text-XProof-my_italics_ellipsis', 'black', u'XXX: Τι να τα κάνεις τα … μετά από italics; ☺', re.M | re.I)
        xps(curSub, u'\\s♫$', 'Text-XProof-my_last_note', 'black', u'XXX: Πιθανώς περιττή νότα στο τέλος.', re.M | re.I)
        xps(curSub, u'—$', 'Text-XProof-my_em_dash', 'black', u'XXX: Μήπως θα έπρεπε να είναι ενωτικό;', re.M | re.I)
        xps(curSub, u'(?<=\\d)[,.](?=\\d{3}\\b)', 'Text-XProof-my_digits', 'black', u'XXX: middle dot · για χιλιάδες', re.M | re.I)
        xps(curSub, u'(?<=\\d):(?=\\d{2}\\b)', 'Text-XProof-my_hour', 'black', u'XXX: ώρα λεπτά με ratio ∶', re.M | re.I)
        xps(curSub, u'\\A–…', 'Text-XProof-no_dialog_change', 'black', u'XXX: δεν αλλάζει πρόσωπο', re.M | re.I)
        xps(curSub, u' –', 'Text-XProof-space_endash', 'black', u'XXX: κενό en dash —', re.M | re.I)
        xps(curSub, u'(?<=\\p{Lu})\\.\\s(?=\\p{Lu})', 'Text-XProof-my_spaced_caps', 'black', u'ΧΧΧ: κεφαλαίο τελεία κενό κεφαλαίο', re.M)
        xps(curSub, u'όσασταν\\b', 'Text-XProof-b_plyth_paratatikoy', 'black', u'Βʹ πληθ. ενεστώτα: «γνωρίζεστε», Βʹ πληθ. παρατατικού: «γνωριζόσαστε»', re.M | re.I)
        xps(curSub, u'\\b(άσ)(τ(?:ον?|η?ν|ους|α))', 'Text-XProof-let_it_be', 'black', u'Είναι δύο λέξεις: άσε τον, άρα αποκοπή: άσ\' τον.', re.M | re.I)
        xps(curSub, u'(?<=\\bεπιπλ[εέ])ω(?=ν\\b)', 'Text-XProof-moreover', 'black', u'Το «επιπλέον» είναι άκλιτο και γράφεται με "ο" (αυτός που επιπλέει γράφεται με "ω").', re.M | re.I)
        xps(curSub, u'(?<=\\b(?:πιθαν|δυνατ))ώ(?=ν\\b)', 'Text-XProof-possibly_probably', 'black', u'Τα «πιθανόν», «δυνατόν» είναι άκλιτα και γράφονται με "ό"\n    (το «πιθανώς» γράφεται με "ω", όπως και τα «των δυνατών», «των πιθανών»)..', re.M | re.I)
        xps(curSub, u'([.…!?,:;])([[.…!?,:;])', 'Text-XProof-superfluous_punctuation_multi', 'black', u'FMT: Διπλή στίξη, διαλέξτε ένα από τα δύο.', re.M | re.I)
        xps(curSub, u'[,.](?=…)', 'Text-XProof-superfluous_punctuation', 'black', u'FMT: Περιττή στίξη πριν από αποσιωπητικά.', re.M | re.I)
        xps(curSub, u'»([!;])', 'Text-XProof-punctuation_and_closing_quotes_1', 'black', u'FMT:Μήπως η στίξη να πάει εντός των εισαγωγικών;', re.M | re.I)
        xps(curSub, u'\\.»', 'Text-XProof-punctuation_and_closing_quotes_2', 'black', u'FMT:Μήπως η τελεία να πάει μετά τα εισαγωγικά;', re.M | re.I)
        xps(curSub, u'\\s([ντθ]α|τ?οι?|η|[σμ]ε|για)\\n', 'Text-XProof-eol_short_word', 'black', u'FMT: Σύντομη λέξη στο τέλος της αράδας.', re.M | re.I)
        xps(curSub, u'^…\\s', 'Text-XProof-initial_ellipsis_space', 'black', u'FMT: κενό μετά από αποσιωπητικά στην αρχή της γραμμής', re.M | re.I)
        xps(curSub, u'\\A-\\s…', 'Text-XProof-bol_dash_ellipsis', 'black', u'FMT: Αν προτιμάτε χωρίς κενό μεταξύ παύλας διαλόγου και αποσιωπητικών.', re.M | re.I)
        xps(curSub, u'\\s?(\w+\p{Ll})-\\n(\\p{Ll}+\\b)\\s?', 'Text-XProof-eol_dash', 'black', u'FMT: Σημείωση ενωτικού που σπάει λέξη.', re.M | re.I)
        xps(curSub, u',\\Z', 'Text-XProof-comma_at_end', 'black', u'FMT: Κόμμα στο τέλος υπότιτλου;', re.M | re.I)
        xps(curSub, u'[@*]+', 'Text-XProof-comment_possibly', 'green', u'VRFY: Σχόλιο από μεταφραστή προς επιμελητή;', re.M | re.I)
        xps(curSub, u'\\b(\\p{Lu}{2,})\\b', 'Text-XProof-word_all_caps', 'green', u'VRFY: λέξη όλη με κεφαλαία', re.M)
        xps(curSub, u'\b(ψ[έε])μ(μ[άα])', 'Text-XProof-sweet_little_lies', 'black', u'SPELL: το ψέμα γράφεται πια με ένα «μ»', re.M | re.I)
