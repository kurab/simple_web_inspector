import requests
import shutil
import time
from bs4 import BeautifulSoup

# settings
# domain (no trailing slash)
DOMAIN = 'https://www.yourdomain.com'
# start url (with trailing slash)
BASE_URL = 'https://www.yourdomain.com/dir/'
# site depth
DEPTH = 5
# interval sleep time(sec)
INTERVAL_SLEEP = 1
# output file
OUTPUT_FILE = './internal_links.txt'
# temporary files
TEMP_FILE = './temp_links.txt'
TEMP_FILE2 = './temp_links2.txt'


def parseUrlAndSaveInternalLinks(startUrl):
    res = requests.get(startUrl)
    httpStatus = res.status_code

    print('fetched URL: ' + startUrl)
    print('status code: ' + str(httpStatus))
    if httpStatus != 200:
        return

    soup = BeautifulSoup(res.text, 'html.parser')

    with open(OUTPUT_FILE, 'r') as fDup:
        duplicatedLinkCheck = [line.strip() for line in fDup.readlines()]

    with open(OUTPUT_FILE, 'a') as fOut:
        with open(TEMP_FILE2, 'a') as fTmp:
            for url in soup.find_all('a'):
                href = url.get('href')
                # exclude
                # - no href attribute
                # − empty href
                # − anchor link, javascript
                if not href \
                        or href == '' \
                        or href.startswith(('#', 'javascript')):
                    continue
                # - external links
                elif href.startswith('http') and not href.startswith(BASE_URL):
                    continue

                # make url full path
                # no protocol
                if href.startswith('//'):
                    href = 'https:' + href
                # absolute path
                elif href.startswith('/'):
                    href = DOMAIN + href
                # relative path
                elif not href.startswith('http'):
                    href = BASE_URL + href

                # register only new links
                if href not in duplicatedLinkCheck:
                    duplicatedLinkCheck.append(href)
                    print("  new link: " + href)
                    fOut.write(href + '\n')
                    fTmp.write(href + '\n')

    return


def main():
    parseUrlAndSaveInternalLinks(BASE_URL)

    for i in range(DEPTH):
        shutil.move(TEMP_FILE2, TEMP_FILE)
        print('\n--- Attempt: ' + str(i + 1))
        with open(TEMP_FILE) as f:
            for url in f.readlines():
                parseUrlAndSaveInternalLinks(url.strip())
                time.sleep(INTERVAL_SLEEP)

    return


if __name__ == '__main__':
    main()
