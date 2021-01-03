import requests
import time
from bs4 import BeautifulSoup

# ========== settings ==========
# domain(no trailing slash)
DOMAIN = 'https://www.yourdomain.com'
# start url
BASE_URL = 'https://www.yourdomain.com/dir/'
# link list
URL_LIST = './internal_links.txt'
# output file(markdown)
OUTPUT_FILE = './report.md'
# interval time(sec)
INTERVAL_SLEEP = 1


# ========== views ==========
def outputToFile(basicInfo, linkInfo, mediaInfo):
    with open(OUTPUT_FILE, 'a') as f:
        f.write(basicInfo)
        f.write(linkInfo)
        f.write(mediaInfo)


def formatInvalidLinkText(links):
    deadLinkListText = ''
    deadLinkText = ''
    movedLinkListText = ''
    movedLinkText = ''
    if len(links['dead']) > 0:
        for dead in links['dead']:
            deadLinkListText += '- ' + dead + '\n'

        deadLinkText = f'''
### Dead Link List (404 Not Found)
{deadLinkListText}

<br>
        '''

    if len(links['moved']) > 0:
        for moved in links['moved']:
            movedLinkListText += '- ' + moved + '\n'

        movedLinkText = f'''
### Redirected Link List (301/302 Moved Permanently/Temporarily)
{movedLinkListText}

<br>
        '''
    return [deadLinkText, movedLinkText]


def formatBasicInfo(url, httpStatus, meta):
    if httpStatus > 400:
        prefix = 'CRITICAL: '
    elif httpStatus > 300:
        prefix = 'WARN: '
    else:
        prefix = ''

    return f"""
# {prefix}{url}

Basic Information
| item        | value                 |
| :-          | :-                    |
| url         | {url}                 |
| httpStatus  | {httpStatus}          |
| title       | {meta['title']}       |
| description | {meta['description']} |
| keywords    | {meta['keywords']}    |

<br>

    """


def formatLinkInfo(cnt, links):
    [deadLinkText, movedLinkText] = formatInvalidLinkText(links)
    return f"""
## Link Analysis

| Invalid item                   | count          |
| :-                             | :-:            |
| Empty Link('' or no href attr) | {cnt['empty']} |
| Temporary Link suspected(#)    | {cnt['temp']}  |
| Dead Link(404)                 | {cnt['dead']}  |
| Redirected Link(301, 302)      | {cnt['moved']} |

<br>

{deadLinkText}

{movedLinkText}
    """


def formatMediaInfo(cnt, links):
    [deadLinkText, movedLinkText] = formatInvalidLinkText(links)
    return f"""
## Media Analysis

| type | total | dead | moved |
|:-|:-:|:-:|:-:|
| css     | {cnt['stylesheet']['total']} | {cnt['stylesheet']['dead']} | {cnt['stylesheet']['moved']} |
| js      | {cnt['script']['total']}     | {cnt['script']['dead']}     | {cnt['script']['moved']}     |
| font    | {cnt['font']['total']}       | {cnt['font']['dead']}       | {cnt['font']['moved']}       |
| favicon | {cnt['icon']['total']}       | {cnt['icon']['dead']}       | {cnt['icon']['moved']}       |
| img     | {cnt['img']['total']}        | {cnt['img']['dead']}        | {cnt['img']['moved']}        |

<br>

{deadLinkText}

{movedLinkText}
    """


# ========== utils ==========
def getFullPath(url, basePath=BASE_URL):
    # no protocol
    if url.startswith('//'):
        url = 'https:' + url
    # absolute path
    elif url.startswith('/'):
        url = DOMAIN + url
    # relative path
    elif not url.startswith('http'):
        url = basePath + url
    return url


# ========== logics ==========
def getMetaInfo(soup):
    meta = {}
    # Title
    meta_title = soup.find('title')
    meta['title'] = meta_title.get_text() if len(
        meta_title) > 0 else '(not set)'
    # Description
    meta_description = soup.find('meta', {'name': 'description'})
    meta['description'] = meta_description.get(
        'content') if meta_description else '(not set)'
    # Keywords
    meta_keywords = soup.find('meta', {'name': 'keywords'})
    meta['keywords'] = meta_keywords.get(
        'content') if meta_keywords else '(not set)'

    return meta


def getLinkInfo(soup):
    # link analysis
    count = {}
    links = {}

    count['empty'] = 0  # href='' or no href attribute
    count['temp'] = 0  # href='#'
    count['dead'] = 0  # 404
    count['moved'] = 0  # 301, 302
    links['dead'] = []  # 404 link
    links['moved'] = []  # 301, 302 link

    for link in soup.find_all('a'):
        href = link.get('href')
        if not href or href == '':
            count['empty'] += 1
            continue
        elif href == '#':
            count['temp'] += 1
            continue
        elif href.startswith('javascript'):
            continue

        href = getFullPath(href)

        linkStatus = requests.get(href).status_code
        if linkStatus == 404:
            links['dead'].append(href)
        elif linkStatus == 301 or linkStatus == 302:
            links['moved'].append(href)

    count['dead'] = len(links['dead'])
    count['moved'] = len(links['moved'])

    return [count, links]


def getMediaInfo(soup):
    count = {}
    links = {}

    count['stylesheet'] = {'total': 0, 'dead': 0, 'moved': 0}
    count['icon'] = {'total': 0, 'dead': 0, 'moved': 0}
    count['font'] = {'total': 0, 'dead': 0, 'moved': 0}
    count['script'] = {'total': 0, 'dead': 0, 'moved': 0}
    count['img'] = {'total': 0, 'dead': 0, 'moved': 0}

    links['dead'] = []
    links['moved'] = []

    # link tag
    for link in soup.find_all('link'):
        href = getFullPath(link.get('href'))

        # only stylesheet, icon, preload(font)
        # https://www.w3schools.com/tags/att_link_rel.asp
        # css: rel=stylesheet
        # favicon: rel=icon
        # font: rel=preload as=font
        rel = link.get('as') if link.get('as') else link.get('rel')[0]
        if rel == 'stylesheet' \
                or rel == 'icon' \
                or rel == 'font':
            count[rel]['total'] += 1
            linkStatus = requests.get(href).status_code
            if linkStatus == 404:
                count[rel]['dead'] += 1
                links['dead'].append(href)
            elif linkStatus == 301 or linkStatus == 302:
                count[rel]['moved'] += 1
                links['moved'].append(href)

    # script tag
    for js in soup.find_all('script'):
        src = js.get('src')

        if src:
            count['script']['total'] += 1
            src = getFullPath(js.get('src'))
            jsLinkStatus = requests.get(src).status_code
            if jsLinkStatus == 404:
                count['script']['dead'] += 1
                links['dead'].append(href)
            elif jsLinkStatus == 301 or jsLinkStatus == 302:
                count['script']['moved'] += 1
                links['moved'].append(href)

    # img tag
    for img in soup.find_all('img'):
        image = img.get('src')
        if image:
            count['img']['total'] += 1
            image = getFullPath(image)
            imgLinkStatus = requests.get(image).status_code
            if imgLinkStatus == 404:
                count['img']['dead'] += 1
                links['dead'].append(href)
            elif imgLinkStatus == 301 or imgLinkStatus == 302:
                count['img']['moved'] += 1
                links['moved'].append(href)

    return [count, links]


def inspectUrl(url):
    res = requests.get(url)
    httpStatus = res.status_code

    soup = BeautifulSoup(res.text, 'html.parser')

    # TDK
    meta = getMetaInfo(soup)
    basicInfo = formatBasicInfo(url, httpStatus, meta)

    if (httpStatus == 200):
        # link analysis
        [count, links] = getLinkInfo(soup)
        linkInfo = formatLinkInfo(count, links)

        # media analysis
        [mcount, mlinks] = getMediaInfo(soup)
        mediaInfo = formatMediaInfo(mcount, mlinks)
    else:
        linkInfo = ''
        mediaInfo = ''

    outputToFile(basicInfo, linkInfo, mediaInfo)

    return


def main():
    with open(URL_LIST, 'r') as f:
        for url in f.readlines():
            print(url)
            inspectUrl(url.strip())
            time.sleep(INTERVAL_SLEEP)


if __name__ == '__main__':
    main()
