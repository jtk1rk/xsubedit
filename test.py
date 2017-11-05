from zlib import compress
from random import random

def CDM(str1, str2):
    _str1 = ''.join(str(elem) for elem in str1) if isinstance(str1, list) else str1
    _str2 = ''.join(str(elem) for elem in str2) if isinstance(str2, list) else str2
    cstr1 = compress(_str1)
    cstr2 = compress(_str2)
    cresult = compress(_str1 + _str2)
    return len(cresult) / float( len(cstr1) + len(cstr2) )

def lognot(s):
    return ['1' if i == '0' else '0' for i in s]

def rndstr(sz):
    return ''.join([ '0' if random() < 0.5 else '1' for i in xrange(sz) ])

#a = rndstr(100)
#b = rndstr(50)
#print CDM(a, b)
