# coding:utf-8

from __future__ import print_function


import os
import re
import sys
import os.path
import zipfile
import codecs
from bs4 import BeautifulSoup
import chardet
from chardet.universaldetector import UniversalDetector


# rulebak="^第[零一二三四五六七八九十百千0123456789]*[章|卷|回|節]"
# rulebak="^第[零一二三四五六七八九十百千0123456789]*[章|回|節]"

def clean(in_file, out_file):
	# print(detcect_encoding(in_file))
	raw = codecs.open(in_file, 'r', 'gb2312', errors="ignore")
	text = BeautifulSoup(raw, "html.parser").text
	raw.close()
	header = r'''更多精校小说尽在知轩藏书下载：http://www.zxcs.me/'''
	text = text.replace(header, "").replace("=", "")
	# os. remove(in_file)


def detcect_encoding(s):
	"""
	UTF includes ISO8859-1，
	GB18030 includes GBK，
	GBK includes GB2312，
	GB2312 includes ASCII

	"""
	CODES = ['UTF-8', 'UTF-16', 'GB18030', 'BIG5']
	# UTF-8 BOM prefix
	UTF_8_BOM = b'\xef\xbb\xbf'
	if type(s) == str:
		with open(s, 'rb') as f:
			data = f.read()
	elif type(s) == bytes:
		data = s
	else:
		raise TypeError('unsupported argument type!')

	# iterator charset
	for code in CODES:
		try:
			data.decode(encoding=code)
			if 'UTF-8' == code and data.startswith(UTF_8_BOM):
				return 'UTF-8-SIG'
			return code
		except UnicodeDecodeError:
			continue
	return 'GB18030'
	# raise UnicodeDecodeError('unknown charset!')


def detcect_encoding_v2(filepath):
	detector = UniversalDetector()
	detector.reset()
	for each in open(filepath, 'rb'):
		detector.feed(each)
		if detector.done:
			break
	detector.close()
	fileencoding = detector.result['encoding']
	confidence = detector.result['confidence']
	if fileencoding is None:
		fileencoding = 'unknown'
		confidence = 0.99
	return fileencoding, confidence * 100


class TXT:
	"""
	parse text to structrues
	"""

	def __init__(self, text):
		self.text = text

	@classmethod
	def fromfile(cls, filepath):
		try:
			encoding = detcect_encoding(filepath)
			raw = codecs.open(filepath, 'r', encoding, errors="ignore")
			return cls(BeautifulSoup(raw, "html.parser").text.strip())
		except Exception as e:
			tb = sys.exc_info()[2]
			raise e.with_traceback(tb)

	def parse(self):
		title_rule = u'\s*【?第[零一兩二三四五六七八九十百千○0123456789]*[卷]】?'
		data = re.split(title_rule, self.text)
		string = data[0]
		if len(data) > 1:
			for vol in data[1:]:
				title = vol.split('\n')[0].strip('\r')
				string += "".join(re.split(title, vol))
		title_rule = u'\s*【?第[零一兩二三四五六七八九十百千○0123456789]*[章|集|回|篇|节|節]】?'
		data = re.split(title_rule, string)
		metadata = data[0].replace('\r', '').strip()
		self.title = metadata.split('\n')[0].replace(
			"书名：", '').replace("《", "").replace("》", "").strip()
		try:
			self.author = re.split(u"作者：", metadata.split('\n')[1])[1]
			# print(self.title)
			# print(self.author)
		except Exception as e:
			# print("author ")
			self.title = re.split(u"作者：", metadata.split('\n')[0])[0].strip()
			self.author = re.split(u"作者：", metadata.split('\n')[0])[1].strip()
			# print(self.title)
			# print(self.author)
		try:
			self.desc = "".join(re.split(re.escape(self.author), metadata)[
								1:]).replace('正文', '').strip('\n')
		except Exception as e:
			# print("desc")
			self.desc = "".join(re.split(u"【?[内容|作品]?[简介|介绍]】?：?", metadata)[
								1:]).replace('正文', '').strip('\n')
		finally:
			# print(self.desc)
			pass

		content = data[1:]
		self.chapters = []
		idx = 0
		for ch in content:
			if ch.strip():
				idx += 1
				self.chapters.append(Chapter(ch, idx))
		self.chapter_num = idx

	def exclude(self, dirtystr, replacer=""):
		self.text = self.text.replace(dirtystr, "").strip()

	def create_mimetype(self, epub):
		epub.writestr('mimetype', 'application/epub+zip',
								  compress_type=zipfile.ZIP_STORED)

	def create_container(self, epub):
		container_info = '''<?xml version="1.0" encoding="UTF-8" ?>
		<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
			<rootfiles> 
				<rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/> 
			</rootfiles>
		</container>
		'''
		epub.writestr('META-INF/container.xml', container_info,
					  compress_type=zipfile.ZIP_STORED)

	def create_content(self, epub):
		"""
		<title>:题名
		<creator>：责任者
		<subject>：主题词或关键词
		<description>：内容描述
		<contributor>：贡献者或其它次要责任者
		<date>：日期
		<type>：类型
		<format>：格式
		<identifier>：标识符
		<source>：来源
		<language>：语种
		<relation>：相关信息
		<coverage>：履盖范围
		<rights>：权限描述
		"""
		content_info = '''<?xml version="1.0" encoding="UTF-8"?>
		<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
		<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
			<dc:title>%(title)s</dc:title>
			<dc:creator>%(author)s</dc:creator>
			<dc:description>%(description)s</dc:description>
			<meta name="cover" content="cover" />
			<dc:subject>网络小说</dc:subject>
			<dc:publisher>Python出版社</dc:publisher>
			<dc:date>2019-04-29</dc:date>
			<dc:identifier id="BookId">9780198005629</dc:identifier>
			<dc:language>zh</dc:language>
			<dc:coverage>中国</dc:coverage>
			<dc:rights>版权</dc:rights>
		 </metadata>
		 <manifest>
			  %(manifest)s
			<item id="ncx" href="content.ncx" media-type="application/x-dtbncx+xml"/>
			<item id="content" href="content.html" media-type="application/xhtml+xml"/>
			<item id="cover" href="cover.jpg" media-type="image/jpeg"/>
			<item id="css" href="main.css" media-type="text/css"/>
			<item id="css" href="fonts.css" media-type="text/css"/>
		  </manifest>
		  <spine toc="ncx">
			  %(spine)s
		  </spine>
		</package>
		'''

		manifest = ''
		spine = ''
		for idx in range(self.chapter_num):
			manifest += '<item id="chapter%d.html" href="chapter%d.html" media-type="application/xhtml+xml"/>' % (
				idx + 1, idx + 1)
			spine += '<itemref idref="chapter%d.html"/>' % (idx + 1)
		epub.writestr('OPS/content.opf', content_info % {
			'title': self.title,
			'author': self.author,
			'description': self.desc,
			'manifest': manifest,
			'spine': spine, },
			compress_type=zipfile.ZIP_STORED)

		ncx = '''<?xml version="1.0" encoding="utf-8"?>
		<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
		<ncx version="2005-1" xmlns="http://www.daisy.org/z3986/2005/ncx/">
		<head>
		  <meta name="dtb:uid" content=" "/>
		  <meta name="dtb:depth" content="-1"/>
		  <meta name="dtb:totalPageCount" content="0"/>
		  <meta name="dtb:maxPageNumber" content="0"/>
		</head>
		 <docTitle><text>%(title)s</text></docTitle>
		 <docAuthor><text>%(creator)s</text></docAuthor>
		<navMap>
		%(navpoints)s
		</navMap>
		</ncx>
		'''
		navpoint = '''<navPoint id='%s' class='level1' playOrder='%d'>
		<navLabel> <text>%s</text> </navLabel>
		<content src='%s'/></navPoint>'''
		navpoints = []
		for chap in self.chapters:
			title = chap.info()['title']
			idx = chap.info()['id']
			navpoints.append(navpoint % ("chapter{}.html".format(
				idx), idx, "第{}章 {}".format(idx, title), "chapter{}.html".format(idx)))

		epub.writestr('OPS/content.ncx', ncx % {
			'title': self.title,
			'creator': self.author,
			'navpoints': '\n'.join(navpoints)},
			compress_type=zipfile.ZIP_STORED)

	def create_stylesheet(self, epub):
		for css_info in ['main.css', 'fonts.css']:
			if os.path.isfile('assets/' + css_info):
				epub.write('assets/' + css_info, 'OPS/' + css_info,
						   compress_type=zipfile.ZIP_STORED)

	def create_cover(self, epub, img='cover.jpg'):
		if os.path.isfile(img):
			epub.write(img, 'OPS/' + 'cover.jpg',
					   compress_type=zipfile.ZIP_DEFLATED)

	def create_archive(self, filename, cover='cover.jpg'):
		epub_name = '%s.epub' % filename
		epub = zipfile.ZipFile(epub_name, 'w')
		self.create_mimetype(epub)
		self.create_container(epub)
		self.create_content(epub)
		self.create_stylesheet(epub)
		self.create_cover(epub, cover)
		for chap in self.chapters:
			basename = "chapter{}.html".format(chap.info()['id'])
			epub.writestr('OPS/' + basename, str(chap),
						  compress_type=zipfile.ZIP_DEFLATED)
		epub.close()

	def __str__(self):
		return str({'title': self.title, 'author': self.author, 'description': self.desc, 'chapter count': self.chapter_num})


class Chapter:

	def __init__(self, data, idx):
		self.data = data.strip()
		self.idx = idx
		self.count = len(re.findall(r'[\u4E00-\u9FFF]', data))
		self.parse()

	def parse(self):
		self.title = self.data.split('\n')[0].strip('\r')
		self.body = "".join(re.split(re.escape(self.title), self.data))
		text = self.body.replace('\u3000\u3000', "</p>\n<p>")
		string = ''
		string += '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">'''
		string += "\n<head>"
		string += "\n<title>" + self.title + "</title>"
		string += '''\n<link href="fonts.css" type="text/css" rel="stylesheet"/>
					 <link href="main.css" type="text/css" rel="stylesheet"/>'''
		string += "\n</head>"
		string += "\n<body>"
		string += '\n<div class="logo"></div>'
		# <img alt="logo" class="logo" width="960" src="cover.jpg"/>
		string += '\n<h2 class="head">第%d章<br/><b> %s</b></h2>\n<p>' % (
			self.idx, self.title)
		string += text
		string += "</p>"
		string += "\n</body>"
		string += "\n</html>"
		self.string = string

	def export(self, filepath):
		with open(filepath, "w", encoding="utf8") as f:
			f.write(self.string)

	def __str__(self):
		return self.string

	def info(self):
		return {'id': self.idx, 'title': self.title, 'count': self.count}


if __name__ == '__main__':
	path = "./txt/"
	for txt in os.listdir(path):
		if txt.endswith('.txt'):
			basename = os.path.splitext(txt)[0]
			print(path + txt)
			detcect_encoding(path + txt)
			parser = TXT(path + txt)
			parser.exclude(r'''更多精校小说尽在知轩藏书下载：http://www.zxcs.me/''')
			parser.exclude(r'''更多精校小说尽在知轩藏书下载：http://www.zxcs8.com/''')
			parser.exclude(r"=")
			parser.parse()
			parser.create_archive("epub/" + basename)
