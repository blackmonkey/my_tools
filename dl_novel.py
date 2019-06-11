# -*- coding: utf-8 -*-
import codecs, requests, sys, re, functools, urllib, pprint, os, time
from urllib.parse import urljoin
from urllib.parse import quote as urlquote
from urllib.parse import unquote as urlunquote
from bookmarks import BOOKMARKS
from timeit import default_timer as timer

# can download noval from http://downnovel.com/

def tr(tag, msg):
	sys.stdout.write('[%s] %s\n' % (tag, msg))

def log(msg):
	tr('INFO', msg)

def err(msg):
	tr('ERRO', msg)

def wrn(msg):
	tr('WARN', msg)

def web_proxy_params(url):
	return {'u':url, 'b':'4', 'f':'norefer'}

def un_web_proxy_url(match):
	return urlunquote(match.group(1))

WEB_PROXY_URL_PAT = re.compile('/browse\.php\?u=(http.*?)&amp;b=4')
def un_web_proxy_html(html):
	return WEB_PROXY_URL_PAT.sub(un_web_proxy_url, html)

REQUEST_TIMEOUT = 60 # 1 minutes
REQUEST_MAX_RETRY = 5
CHARSET_PAT = re.compile(b'content\s*=\s*"\s*text\s*/\s*html\s*;\s*charset\s*=\s*([^"]+)\s*"')
USE_WEB_PROXY = False
g_referer = 'http://webproxy.to/'
def get_html(url, encoding):
	global g_referer
	content = ''
	for retry in range(REQUEST_MAX_RETRY):
		try:
			if USE_WEB_PROXY:
				r = requests.get('http://webproxy.to/browse.php', params=web_proxy_params(url), headers={'Referer': g_referer}, timeout=REQUEST_TIMEOUT)
			else:
				r = requests.get(url, headers={'Referer': g_referer}, timeout = REQUEST_TIMEOUT)
			g_referer = r.url
			if r.status_code == 200:
				content = r.content
				break
			else:
				wrn('got status {}, retry {} getting {}'.format(r.status_code, retry, url))
				time.sleep(30)
		except Exception as e:
			wrn('got except {}, retry {} getting {}'.format(e, retry, url))
			time.sleep(30)

	if len(content) < 1:
		err('failed to get {}, content is empty'.format(url))
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
			return un_web_proxy_html(decoded_html) if USE_WEB_PROXY else decoded_html
		except UnicodeDecodeError:
			pass

	# to here, the HTML content is failed to be decoded with any known encoding
	wrn('failed to decode with encoding:' + str(html_encoding))
	pprint.pprint(content)
	return ''

def cmp_str_int(first, second):
	return int(first) - int(second)

####################################################################################################
# Utilities of http://www.77nt.com
####################################################################################################

CONTENT_LINK_PAT_77nt = re.compile(r'<dd><a href="https://www.77nt.com/[0-9]+/([0-9]+).html">(.+?)</a></dd>') if USE_WEB_PROXY else re.compile(r'<dd><a href="([0-9]+).html">(.+?)</a></dd>')
SECTION_CONTENT_PAT_77nt = re.compile(r'(?:&nbsp;)+.*?(?=<br\s|<div\s)')
WEBSITE_PAT_77nt = re.compile(r'www.77nt.com', re.I)
def get_content_links_77nt(link):
	return get_content_links_common(link, CONTENT_LINK_PAT_77nt)

def get_section_77nt_1(link, title):
	html = get_html(link, 'utf8')
	paragraphs = SECTION_CONTENT_PAT_77nt.findall(html)
	if len(paragraphs) == 0:
		return title + '\r\n\r\n' + link + '\r\n\r\n'
	for i in range(len(paragraphs)):
		paragraphs[i] = re.sub(WEBSITE_PAT_77nt, '', paragraphs[i].replace('&nbsp;', ' ').strip())
	return title + '\r\n\r\n' + '\r\n\r\n'.join(paragraphs) + '\r\n\r\n'

ALL_CONTENT_PAT_77nt = re.compile(r'<div\s+id\s*=\s*"content[0-9]+"\s+class\s*=\s*"content\s+novel[0-9]+\s+chapter[0-9]+\s*"\s*>(.+)<div\s+class\s*=\s*"other_links"\s*>')
def get_section_77nt(link, title):
	html = get_html(link, 'utf8')
	content = ALL_CONTENT_PAT_77nt.findall(html)
	if len(content) == 0:
		content = link
	else:
		content = content[0].replace('&nbsp;', ' ')
		content = re.sub(re.compile(r'www\.77nt\.com', re.I), '', content)
		content = re.sub(re.compile(r'77nt\.com 平板电子书', re.I), '', content)
		content = re.sub(re.compile(r'<br\s*/>'), '\n', content)
		content = re.sub(re.compile(r'<a\s+href\s*=[^>]+>[^<]+</a>'), '', content)
		content = re.sub(re.compile(r'<script\s*[^>]+>[^<]+</script>'), '', content)
		content = re.sub(re.compile(r'<div\s*[^>]+>[^<]*</div>'), '', content)
		content = re.sub(re.compile(r'\n\s+'), '\r\n\r\n', content).strip()
	return title + '\r\n\r\n' + content + '\r\n\r\n'

####################################################################################################
# Utilities of http://www.boquge.com/
####################################################################################################

CONTENT_LINK_PAT_boquge = re.compile(r'<a href="https://www.boquge.com/book/[0-9]+/([0-9]+).html">(.+?)</a>') if USE_WEB_PROXY else re.compile(r'<a href="/book/[0-9]+/([0-9]+).html">(.+?)</a>')
SECTION_CONTENT_PAT_boquge = re.compile(r'<div id="txtContent">\s+(.*?)(?:<br/>)?\s+</div>', re.S)
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

#	fp = codecs.open(link.split('/')[-2], 'w', 'utf8')
#	fp.write(html)
#	fp.close()

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
	return get_content_links_77nt(link)

def get_section(link, title):
	log('downloading ' + title)
	if '.boquge.com' in link:
		return get_section_boquge(link, title)
	elif 'book9.net' in link:
		return get_section_book9(link, title)
	return get_section_77nt(link, title)

def download_novel(novelName, contentLink, bookmarkLink):
	log('---- checking %s ----' % (novelName))
	content_links = get_content_links(contentLink)
#	pprint.pprint(content_links)

	foundBookmark = False
	newSections = []

	fname = novelName + '.txt'
	fencoding = 'utf8'

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


if __name__ == '__main__':
	start = timer()
	for novelName in BOOKMARKS:
		bookmarkLink = download_novel(novelName, BOOKMARKS[novelName][0], BOOKMARKS[novelName][1])
		BOOKMARKS[novelName][1] = bookmarkLink
	end = timer()

	print('DONE')
	print('Total time: %.3f seconds' % (end - start))

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
