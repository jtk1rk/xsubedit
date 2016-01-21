# packages python2-beautifulsoup4
# python2-lxml
import requests
import re
from bs4 import BeautifulSoup

def meaning(word):
    url_arg = '+'.join(word.split())
    r = requests.get('http://www.thefreedictionary.com/%s' % url_arg)
    soup = BeautifulSoup(r.content, 'lxml')

    div = soup.find('div', attrs={'id': 'MainTxt'})
    meanings = div.findAll('div', attrs={'class': 'ds-list'})
    if meanings == '':
        meanings = div.findAll('div', attrs={'class': 'ds-single'})

    res = []
    for meaning in meanings:
        if meaning.find('span', attrs={'class': 'trans'}) or meaning.find(True, {'lang': True}):
            continue
        res.append(meaning.text)

    return res