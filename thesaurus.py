# -*- coding: utf-8 -*-

from os.path import exists
import pickle, zlib

class cThesaurus:
    def __init__(self, ThesaurusFile):
        if not(exists(ThesaurusFile)):
            raise IOError("Thesaurus file not found")

        with open(ThesaurusFile, 'rb') as f:
            dump = zlib.decompress(f.read())

        self.thesaurus = pickle.loads(dump, encoding='latin1')

    def check(self, word):
        return self.thesaurus[word] if word in self.thesaurus else None
