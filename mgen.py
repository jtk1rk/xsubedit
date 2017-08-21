from mparser import Tag

def str_insert(st, subst, pos):
    return st[:pos] + subst + st[pos:] if pos < len(st) else st + subst

class MarkupGenerator:
    def __init__(self, text, tags):
        self.tagList = tags
        self.text = text
        self.markup = self.markup_gen()

    def add_offset(self, pos, offset):
        for tag in self.tagList:
            if tag.start > pos:
                tag.start += offset
            if tag.stop > pos:
                tag.stop += offset

    def markup_gen(self):
        res = self.text
        offset = 0
        for tag in self.tagList:
            ts = tag.start_str
            res = str_insert(res, ts, tag.start)
            self.add_offset(tag.start, len(ts))
            ts = tag.stop_str
            res = str_insert(res, ts, tag.stop)
            self.add_offset(tag.start, len(ts))
        return res

