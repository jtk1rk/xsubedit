import random

markup_escape = lambda text: text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
markup_unescape = lambda text: text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

class MarkupTag(object):
    def __init__(self,  text,  pos):
        self.__text = text
        self.__pos = pos

    def append(self, char):
        self.text += char

    def is_complete(self):
        return self.text[-1] == '>'

    @property
    def text(self):
        return self.__text

    @text.setter
    def text(self, txt):
        self.__text = txt

    @property
    def tag_type(self):
        if len(self.text) <= 1:
            return None
        else:
            return 'close' if self.text[1] == '/' else 'open'

    @property
    def name(self):
        tmp_text = self.text
        tag_name = ''
        while len(tmp_text) > 0 and not tmp_text[0] in ['>',  ' ']:
            if not tmp_text[0] in ['<',  '/']:
                tag_name += tmp_text[0]
            tmp_text = tmp_text[1:]
        return tag_name

    @property
    def attributes(self):
        res = {}
        attr_start = self.text.find(' ')
        attr_stop = self.text.find('>')
        if attr_start == -1 or attr_stop == -1:
            return res
        attr_text = self.text[attr_start:attr_stop].strip()
        if attr_text == '':
            return res
        for attr_pair in attr_text.split():
            if len(attr_pair.split('=')) < 2:
                raise ValueError('Invalid tag attributes')
            res[attr_pair.split('=')[0]] = attr_pair.split('=')[1].strip('"')
        return res

    @property
    def pos(self):
        return self.__pos

class MarkupTagList(object):
    def __init__(self):
        self.tag_list = []

    def is_empty(self):
        return len(self.tag_list) == 0

    @property
    def last(self):
        return self.tag_list[-1] if not(self.is_empty()) else None

    def __iter__(self):
        return iter(self.tag_list)

    def __get__(self, index):
        return self.tag_list[index]

    def __len__(self):
        return len(self.tag_list)

    def get_list(self):
        return self.tag_list

    def new_tag(self,  pos):
        self.tag_list.append(MarkupTag('<', pos))

class Tag(object):
    def __init__(self, tag_name, start, stop, attributes):
        self.name = tag_name
        self.start = start
        self.stop = stop
        self.attributes = attributes
        self.__id = str(random.getrandbits(32))

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def start(self):
        return self.__start

    @start.setter
    def start(self, value):
        self.__start = value

    @property
    def stop(self):
        return self.__stop

    @stop.setter
    def stop(self, value):
        self.__stop = value

    @property
    def attributes(self):
        return self.__attributes

    @attributes.setter
    def attributes(self, value):
        self.__attributes = value

    @property
    def start_str(self):
        return '<%s %s>' % (self.name, ' '.join(['%s="%s"' % (a, self.attributes[a]) for a in self.attributes.keys()]))

    @property
    def stop_str(self):
        return '</%s>' % self.name

class MarkupParser:
    def __init__(self,  markup):
        self.markup_text = markup
        self.__tags = []
        self.__text = ''
        self.parse()

    def parse(self):
        markup_list= MarkupTagList()
        text = self.markup_text

        res_text = ''
        char_pos = 0

        # parse markup tags from text
        while len(text) > 0:
            last_tag = markup_list.last if markup_list.last else None

            if text[0] == '<':
                if not last_tag or last_tag.is_complete():
                    markup_list.new_tag(char_pos)
                else:
                    raise ValueError('Malformed markup')

            elif text[0] == '>':
                if last_tag and not last_tag.is_complete():
                    last_tag.append('>')
                else:
                    raise ValueError('Malformed markup')

            else:
                if last_tag and not last_tag.is_complete():
                    last_tag.append(text[0])
                else:
                    char_pos += 1
                    res_text += text[0]

            text = text[1:]

        # process tags
        self.__text = res_text
        if markup_list.is_empty():
            return

        tag_filo = []

        for tag in markup_list:
            if tag.tag_type == 'close' and len(tag_filo) > 0:
                if tag_filo[-1].tag_type == 'open' and tag_filo[-1].name == tag.name:
                    self.__tags.append(Tag(tag.name, tag_filo[-1].pos, tag.pos, tag_filo[-1].attributes))
                    tag_filo.pop()
                else:
                    raise ValueError('Incorrect order of open/close markup tags')
            else:
                tag_filo.append(tag)

    @property
    def text(self):
        return self.__text

    @property
    def tags(self):
        return self.__tags
