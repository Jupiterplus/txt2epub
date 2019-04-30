#usr/binenv python
#-*-coding:utf-8-*-

from bs4 import BeautifulSoup
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError,URLError
from urllib.parse import quote
import json


baseurl = "http://www.jjwxc.net/onebook.php?novelid=6620"

def add_para(baseurl, **kargs):
    request = baseurl
    for k, v in kargs.items():
        request += "&" + k + "=" + quote(v)
    return request
if(__name__=="__main__"):
	for i in range(1,2):
		url = add_para(baseurl, chapterid=str(i))
		with open("{}.txt".format(i),"w+") as f:
			user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			print(url)
			req = Request(url, headers={'User-Agent': user_agent})
			data = urlopen(req).read().decode('gb2312')
			soup = BeautifulSoup(data,"lxml")
			txt = soup.find('div',attrs={"class":"noveltext"})
			print(data)
