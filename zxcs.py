# coding:utf-8

"""
 知轩藏书downloader
"""

import re
import os
import sys
from unrar import rarfile
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen, urlretrieve
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from epub import TXT


BASEURL = "http://www.zxcs.me/post"
VOTEURL = "http://www.zxcs.me/content/plugins/cgz_xinqing/cgz_xinqing_action.php?action=show"


def add_para(baseurl, **kargs):
    request = baseurl
    for k, v in kargs.items():
        request += "&" + k + "=" + quote(str(v))
    return request


def add_para_v2(baseurl, **kargs):
    request = baseurl
    for _, v in kargs.items():
        request += "/" + quote(v)
    return request


class ZXCS:

    def __init__(self, url):
        self.TXT = None
        self._url = url.strip()
        self._author = ""
        self._title = ""
        self._postid = 0
        self._rarurls = []
        self._txturl = ""
        self._imgurl = ""
        self._vote = []
        self.rules = [r'''更多精校小说尽在知轩藏书下载：http://www.zxcs.me/''', r"="]
        self._parse()
        self.rar_download()
        self.execute()

    def _parse(self):
        self._postid = int(re.findall(r'\d+', self._url)[0])
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'

        req = Request(self._url, headers={'User-Agent': user_agent})
        data = urlopen(req).read().decode()
        soup = BeautifulSoup(data, "lxml")
        info = soup.find(
            'div', attrs={"id": "content"}).h1.text.split('（校对版全本）')
        self._title = info[0].replace("《", "").replace("》", "").strip()
        self._author = info[1].replace("作者：", "").strip()
        self._imgurl = soup.find('img', attrs={'title': "点击查看原图"})['src']

        v_req = Request(add_para(VOTEURL, id=self._postid),
                        headers={'User-Agent': user_agent})
        v_data = urlopen(v_req).read().decode()
        self._vote = [int(v) for v in v_data.split(',')]

        d_req = Request(soup.find('div', attrs={"class": "down_2"}).a[
                        'href'], headers={'User-Agent': user_agent})
        d_data = urlopen(d_req).read().decode()
        soup = BeautifulSoup(d_data, "lxml")
        self._rarurls = [item.a['href'] for item in soup.findAll(
            'span', attrs={"class": "downfile"})]

    def cover_download(self, filename="cover.jpg", overwrite=True):
        if overwrite or not os.path.exists(filename):
            urlretrieve(self._imgurl, filename)
        else:
            raise Exception(
                "{} alreadys exists! set overwrite=True to overwrite the file".format(filename))

    def rar_download(self):
        ebook = '%s.rar' % self._postid
        if not os.path.exists(ebook):
            urlretrieve(self._rarurls[0], ebook)
        rar = rarfile.RarFile(ebook)
        txtname = rar.namelist()[0]
        rar.extractall()
        os.remove(ebook)
        self.TXT = TXT.fromfile(txtname)
        os.remove(txtname)

    def add_rules(self, rule):
        self.rules.append(rule)

    def execute(self):
        for rl in self.rules:
            self.TXT.exclude(rl)
        self.TXT.parse()
        print()

    def export(self, filename, cover_name=None):
        if not cover_name:
            cover_name = '%d.jpg' % self._postid
            self.cover_download(cover_name)
            self.TXT.create_archive(filename, cover_name)
            os.remove(cover_name)
        else:
            self.TXT.create_archive(filename, cover_name)
        print("Ebook Generated Sucessfully!")

    @property
    def id(self):
        return self._postid

    @id.setter
    def id(self, value):
        self._postid = value

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def vote(self):
        return self._vote

    @vote.setter
    def vote(self, value):
        self._vote = value

if __name__ == "__main__":
    zxcs = ZXCS(sys.argv[1])
    zxcs.export(zxcs.title)
