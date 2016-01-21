# packages python2-beautifulsoup4
# python2-lxml
import requests
import re
from bs4 import BeautifulSoup

def remove_multiple_spaces(text):
    return ' '.join(text.split())

def translate(word):
    url_arg = '%20'.join(word.split())
    r = requests.get('http://www.wordreference.com/engr/%s' % url_arg)
    soup = BeautifulSoup(r.content, 'lxml')

    div = soup.find('div', attrs={'id': 'articleWRD'})
    rows = div.findAll('tr', attrs={'class': 'even'})
    rows += div.findAll('tr', attrs={'class': 'odd'})

    res = []
    last_frm = None

    for row in rows:
        tooltips = row.findAll('em', attrs={'class': 'tooltip POS2'})
        tooltips += row.findAll('em', attrs={'class': 'POS2'})
        for tooltip in tooltips:
            tooltip.decompose()
        frmW = row.find('td', attrs={'class': 'FrWrd'})
        toW = row.find('td', attrs={'class': 'ToWrd'})

        last_frm = frmW if frmW is not None else last_frm

        if toW is not None:
            text = remove_multiple_spaces((last_frm.text if last_frm is not None else '') + ' ' + toW.text)
            if text not in res:
                res.append( text )

    return res

