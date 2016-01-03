from mparser import MarkupParser

class TagText(object):
    def __init__(self):
        self.text = ''
        self.tags = []
        self.markup = ''

    @property
    def markup(self):
        return self._get_markup()

    @markup.setter
    def markup(self, value):
        self.__markup = value
    
    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, value):
        self.__text = value

    @property
    def tags(self):
        return self.__tags

    @tags.setter
    def tags(self, value):
        self.__tags = value

    def _get_markup(self):
        res = self.text
        for tag in self.tags:
            pos0, pos1, color = tag.start, tag.stop, tag.attributes['background']
            markup_open = '<span background="' + color + '">'
            markup_close = '</span>'
            res = res[:pos0] + markup_open + res[pos0:]
            pos1 += len(markup_open) if pos1 > pos0 else 0
            for tmpTag in self.tags:
                tmpTag.start += len(markup_open) if tmpTag.start > pos0 else 0
                tmpTag.stop += len(markup_open) if tmpTag.stop > pos0 else 0
            res = res [:pos1] + markup_close + res[pos1:]
            for tmpTag in self.tags:
                tmpTag.start += len(markup_close) if tmpTag.start > pos1 else 0
                tmpTag.stop += len(markup_close) if tmpTag.stop > pos1 else 0
        return res

    def add_tag(self, tag):
        self.__tags.append(tag)

    def parse_markup(self, markup):
        m_parser = MarkupParser(markup)
        self.text = m_parser.text
        self.tags = m_parser.tags

    def replace_markup(self, orig_text, new_text):
        self.markup.replace(orig_text, new_text)

    def replace_parsed(self, orig_text, new_text):
        if self.text == '':
            return
        len_diff = len(new_text) - len(orig_text)
        pos = self.text.find(orig_text)
        while pos >= 0:
            self.text = self.text.replace(orig_text, new_text, 1)
            for tag in self.tags:
                tag.start += 0 if tag.start < pos else len_diff
                tag.stop += 0 if tag.stop < pos else len_diff
            pos =  self.text.find(orig_text)




