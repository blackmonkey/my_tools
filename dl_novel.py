# -*- coding: utf-8 -*-
import codecs, requests, sys, re, functools, urllib, pprint, os, time
from urllib.parse import urljoin
from bookmarks import BOOKMARKS

def tr(tag, msg):
	sys.stdout.write('[%s] %s\n' % (tag, msg))

def log(msg):
	tr('INFO', msg)

def err(msg):
	tr('ERRO', msg)

def wrn(msg):
	tr('WARN', msg)

REQUEST_TIMEOUT = 60 # 1 minutes
REQUEST_MAX_RETRY = 5
CHARSET_PAT = re.compile(b'content\s*=\s*"\s*text\s*/\s*html\s*;\s*charset\s*=\s*([^"]+)\s*"')
def get_html(url, encoding):
	content = ''
	for retry in range(REQUEST_MAX_RETRY):
		try:
			r = requests.get(url, timeout = REQUEST_TIMEOUT)
			if r.status_code == 200:
				content = r.content
				break
			else:
				wrn('retry ' + str(retry) + ' getting ' + url)
				time.sleep(30)
		except:
			wrn('retry ' + str(retry) + ' getting ' + url)
			time.sleep(30)

	if len(content) < 1:
		err('failed to get %s, content is empty' % (url))
		return ''

	html_encoding = [encoding]
	charsets = CHARSET_PAT.findall(content)
	if len(charsets) > 0:
		coding = charsets[0].decode()
		html_encoding.insert(0, coding)
		if coding.lower() == 'gbk':
			html_encoding.insert(1, 'gb18030')
			html_encoding.insert(2, 'gb2312')

	decoded_html = None
	for coding in html_encoding:
		try:
			decoded_html = codecs.decode(content, coding)
			return decoded_html
		except UnicodeDecodeError:
			pass

	# to here, the HTML content is failed to be decoded with any known encoding
	wrn('failed to decode with encoding:' + str(html_encoding))
	pprint.pprint(content)
	return ''

def cmp_str_int(first, second):
	return int(first) - int(second)

####################################################################################################
# Utilities of http://www.pbtxt.com
####################################################################################################

CONTENT_LINK_PAT_pbtxt = re.compile(r'<dd><a href="([0-9]+).html">(.+?)</a></dd>')
SECTION_CONTENT_PAT_pbtxt = re.compile(r'(?:&nbsp;)+.*?(?=<br\s|<div\s)')
WEBSITE_PAT_pbtxt = re.compile(r'www.pbtxt.com', re.I)
def get_content_links_pbtxt(link):
	return get_content_links_common(link, CONTENT_LINK_PAT_pbtxt)

def get_section_pbtxt_1(link, title):
	html = get_html(link, 'utf8')
	paragraphs = SECTION_CONTENT_PAT_pbtxt.findall(html)
	if len(paragraphs) == 0:
		return title + '\r\n\r\n' + link + '\r\n\r\n'
	for i in range(len(paragraphs)):
		paragraphs[i] = re.sub(WEBSITE_PAT_pbtxt, '', paragraphs[i].replace('&nbsp;', ' ').strip())
	return title + '\r\n\r\n' + '\r\n\r\n'.join(paragraphs) + '\r\n\r\n'

ALL_CONTENT_PAT_pbtxt = re.compile(r'<div\s+id\s*=\s*"content[0-9]+"\s+class\s*=\s*"content\s+novel[0-9]+\s+chapter[0-9]+\s*"\s*>(.+)<div\s+class\s*=\s*"other_links"\s*>')
def get_section_pbtxt(link, title):
	html = get_html(link, 'utf8')
	content = ALL_CONTENT_PAT_pbtxt.findall(html)
	if len(content) == 0:
		content = link
	else:
		content = content[0].replace('&nbsp;', ' ')
		content = re.sub(re.compile(r'www\.pbtxt\.com', re.I), '', content)
		content = re.sub(re.compile(r'pbtxt\.com 平板电子书', re.I), '', content)
		content = re.sub(re.compile(r'<br\s*/>'), '\n', content)
		content = re.sub(re.compile(r'<a\s+href\s*=[^>]+>[^<]+</a>'), '', content)
		content = re.sub(re.compile(r'<script\s*[^>]+>[^<]+</script>'), '', content)
		content = re.sub(re.compile(r'<div\s*[^>]+>[^<]*</div>'), '', content)
		content = re.sub(re.compile(r'\n\s+'), '\r\n\r\n', content).strip()
	return title + '\r\n\r\n' + content + '\r\n\r\n'

####################################################################################################
# Utilities of http://www.boquge.com/
####################################################################################################

CONTENT_LINK_PAT_boquge = re.compile(r'<a href="/book/[0-9]+/([0-9]+).html">(.+?)</a>')
SECTION_CONTENT_PAT_boquge = re.compile(r'<div id="txtContent">\s+(.*?)<br/>\s+</div>', re.S)
REMOVE_PATS_boquge = [
	re.compile(r"<div class='gad2'><script type='text/javascript'>try\{mad1\(\);\} catch\(ex\)\{\}</script></div>", re.I),
	re.compile(r'www.boquge.com', re.I)
]
def get_content_links_boquge(link):
	return get_content_links_common(link, CONTENT_LINK_PAT_boquge)

def get_section_boquge(link, title):
	html = get_html(link, 'utf8')
	content = SECTION_CONTENT_PAT_boquge.findall(html)
	if len(content) == 0:
		return title + '\r\n\r\n' + link + '\r\n\r\n'
	for i in range(len(content)):
		content[i] = content[i].replace('&nbsp;', ' ')
		for pat in REMOVE_PATS_boquge:
			content[i] = re.sub(pat, '', content[i])
		content[i] = content[i].split('<br/>')
		lines = []
		for l in content[i]:
			l = l.strip()
			if len(l) > 0:
				lines.append(l)
		content[i] = '\r\n\r\n'.join(lines)
	return title + '\r\n\r\n' + '\r\n\r\n'.join(content) + '\r\n\r\n'

####################################################################################################
# Utilities of https://www.book9.net/
####################################################################################################

CONTENT_LINK_PAT_book9 = re.compile(r'<dd><a href="/[0-9_]+/([0-9]+).html">(.+?)</a>')
SECTION_CONTENT_PAT_book9 = re.compile(r'(?:&nbsp;)+.*?(?=<br\s|<div\s)')

def get_content_links_book9(link):
	return get_content_links_common(link, CONTENT_LINK_PAT_book9)

def get_section_book9(link, title):
	html = get_html(link, 'utf8')
	paragraphs = SECTION_CONTENT_PAT_book9.findall(html)
	if len(paragraphs) == 0:
		return title + '\r\n\r\n' + link + '\r\n\r\n'
	for i in range(len(paragraphs)):
		paragraphs[i] = paragraphs[i].replace('&nbsp;', ' ').strip()
	return title + '\r\n\r\n' + '\r\n\r\n'.join(paragraphs) + '\r\n\r\n'

####################################################################################################
# General utilities
####################################################################################################

def cmp_content_links_common(first, second):
	return cmp_str_int(first[0], second[0])

def get_content_links_common(link, regpat, suffix = '.html'):
	html = get_html(link, 'utf8')
	content_links = regpat.findall(html)
	content_links.sort(key=functools.cmp_to_key(cmp_content_links_common))
	unique_links = []
	for i in range(len(content_links)):
		sectionNo, sectionTitle = content_links[i]
		content_info = (urljoin(link, sectionNo + suffix), sectionTitle)
		if len(unique_links) == 0 or content_info != unique_links[-1]:
			unique_links.append(content_info)
	return unique_links

def get_content_links(link):
	log('downloading content lists')
	if '.boquge.com' in link:
		return get_content_links_boquge(link)
	elif 'book9.net' in link:
		return get_content_links_book9(link)
	return get_content_links_pbtxt(link)

def get_section(link, title):
	log('downloading ' + title)
	if '.boquge.com' in link:
		return get_section_boquge(link, title)
	elif 'book9.net' in link:
		return get_section_book9(link, title)
	return get_section_pbtxt(link, title)

def download_novel(novelName, contentLink, bookmarkLink):
	log('---- checking %s ----' % (novelName))
	content_links = get_content_links(contentLink)
#	pprint.pprint(content_links)

	foundBookmark = False
	newSections = []

	fname = novelName + '.txt'
	fencoding = 'gb18030'

	dumpTitle = True
	if os.path.exists(fname):
		fp = codecs.open(fname, 'r', fencoding)
		lines = fp.readlines()
		fp.close()

		lineCount = 0
		for l in lines:
			if len(l.strip()) > 0:
				lineCount += 1
		if lineCount < 2:
			fp = codecs.open(fname, 'w', fencoding)
		else:
			fp = codecs.open(fname, 'a', fencoding)
			dumpTitle = False
	else:
		fp = codecs.open(fname, 'w', fencoding)

	for i in range(len(content_links)):
		sectionLink, sectionTitle = content_links[i]
		if sectionLink == bookmarkLink:
			foundBookmark = True
			log('Found bookmark ' + sectionTitle)
			if dumpTitle:
				fp.write(novelName)
				fp.write('\r\n\r\n')
		elif foundBookmark:
			fp.write(get_section(sectionLink, sectionTitle))

	fp.close()

	if not foundBookmark:
		log('Not found bookmark ' + bookmarkLink)
		return bookmarkLink
	return content_links[-1][0]

for novelName in BOOKMARKS:
	bookmarkLink = download_novel(novelName, BOOKMARKS[novelName][0], BOOKMARKS[novelName][1])
	BOOKMARKS[novelName][1] = bookmarkLink

print('DONE')
fp = codecs.open('bookmarks.py', 'w', 'utf-8')
fp.write('# -*- coding: utf-8 -*-\n')
fp.write('BOOKMARKS = {\n')
fp.write('\t# name : [content_link, bookmark_link]\n')
novelNames = list(BOOKMARKS.keys())
novelNames.sort()
for novelName  in novelNames:
	fp.write("\t'%s' : ['%s', '%s'],\n" % (novelName, BOOKMARKS[novelName][0], BOOKMARKS[novelName][1]))
fp.write('}\n')
fp.close()
