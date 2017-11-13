#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import requests

def translate(to_translate):
    to_language = 'el'
    language = 'en'
    agents = {'User-Agent':"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)"}
    before_trans = b'class="t0">'
    link = "http://translate.google.com/m?hl=%s&sl=%s&q=%s" % (to_language, language, to_translate.replace(" ", "+"))
    r = requests.get(link, headers=agents)
    page = r.content
    result = page[page.find(before_trans) + len(before_trans):]
    result = result.split(b"<")[0]
    return [result.decode()] if result != '' else []
