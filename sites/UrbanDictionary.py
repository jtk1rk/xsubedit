# packages python2-beautifulsoup4
# python2-lxml
import requests
from bs4 import BeautifulSoup

def meaning(word):
    arg = '+'.join(word.split())
    r = requests.get("http://www.urbandictionary.com/define.php?term=%s" % arg)
    soup = BeautifulSoup(r.content, 'lxml')

    resText = soup.find("div",attrs={"class":"meaning"}).text
    return [resText]

