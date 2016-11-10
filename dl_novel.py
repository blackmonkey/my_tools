# -*- coding: utf-8 -*-
import codecs, requests, sys, re, functools, urllib
from urllib.parse import urljoin

import pprint

BOOKMARKS = {
	# name : [content_link, bookmark_link]
	'超星空文明' : ['http://www.pbtxt.com/83065/', 'http://www.pbtxt.com/83065/24492429.html'],
	'大瞬移时代' : ['http://www.pbtxt.com/84833/', 'http://www.pbtxt.com/84833/24480540.html'],
	'飞天' : ['http://www.pbtxt.com/10129/', 'http://www.pbtxt.com/10129/24497931.html'],
	'魔法高材生' : ['http://www.pbtxt.com/76935/', 'http://www.pbtxt.com/76935/24497609.html'],
	'天启之门' : ['http://www.pbtxt.com/34782/', 'http://www.pbtxt.com/34782/24493585.html'],
	'我的时空穿梭手机' : ['http://www.pbtxt.com/76223/', 'http://www.pbtxt.com/76223/24499978.html'],
	'我有个时空门' : ['http://www.pbtxt.com/82775/', 'http://www.pbtxt.com/82775/24483227.html'],
}

REQUEST_TIMEOUT = 60 # 1 minutes

def tr(tag, msg):
	sys.stdout.write('[%s] %s\n' % (tag, msg))

def log(msg):
	tr('INFO', msg)

def err(msg):
	tr('ERRO', msg)

def get_html(url, encoding):
	r = requests.get(url, timeout = REQUEST_TIMEOUT)
	if r.status_code != 200:
		err('failed to get %s : %d' % (url, r.status_code))
		return ''
	return codecs.decode(r.content, encoding)

def cmp_str_int(first, second):
	return int(first) - int(second)

####################################################################################################
# Utilities of http://www.pbtxt.com
####################################################################################################

def cmp_content_links_pbtxt(first, second):
	return cmp_str_int(first[0], second[0])

CONTENT_LINK_PAT_pbtxt = re.compile(r'<dd><a href="([0-9]+).html">(.+?)</a></dd>')
SECTION_CONTENT_PAT_pbtxt = re.compile(r'(?:&nbsp;)+.*?(?=<br\s|<div\s)')
def get_content_links_pbtxt(link):
	html = get_html(link, 'gb18030')
	content_links = CONTENT_LINK_PAT_pbtxt.findall(html)
	content_links.sort(key=functools.cmp_to_key(cmp_content_links_pbtxt))
	for i in range(len(content_links)):
		sectionNo, sectionTitle = content_links[i]
		content_links[i] = (urljoin(link, sectionNo + '.html'), sectionTitle)
	return content_links

def get_section_pbtxt(link, title):
	html = get_html(link, 'gb18030')
	paragraphs = SECTION_CONTENT_PAT_pbtxt.findall(html)
	if len(paragraphs) == 0:
		return title + '\n\n' + link + '\n\n'
	for i in range(len(paragraphs)):
		paragraphs[i] = paragraphs[i].replace('&nbsp;', ' ').strip()
	return title + '\n\n' + '\n\n'.join(paragraphs) + '\n\n'

####################################################################################################
# General utilities
####################################################################################################

def get_content_links(link):
	log('downloading content lists')
	return get_content_links_pbtxt(link)

def get_section(link, title):
	log('downloading ' + title)
	return get_section_pbtxt(link, title)

def download_novel(novelName, contentLink, bookmarkLink):
	log('---- checking %s ----' % (novelName))
	content_links = get_content_links(contentLink)
#	pprint.pprint(content_links)

	foundBookmark = False
	newSections = []
	fp = None
	for i in range(len(content_links)):
		sectionLink, sectionTitle = content_links[i]
		if sectionLink == bookmarkLink:
			foundBookmark = True
			log('Found bookmark ' + sectionTitle)
			fp = codecs.open(novelName + '.txt', 'w', 'gb18030')
			fp.write(novelName)
			fp.write('\n\n')
		elif foundBookmark:
			fp.write(get_section(sectionLink, sectionTitle))
	if not foundBookmark:
		log('Not found bookmark ' + bookmarkLink)
		return

	fp.close()
	return content_links[-1][0]

for novelName in BOOKMARKS:
	bookmarkLink = download_novel(novelName, BOOKMARKS[novelName][0], BOOKMARKS[novelName][1])
	BOOKMARKS[novelName][1] = bookmarkLink

print('=' * 40)
pprint.pprint(BOOKMARKS)
