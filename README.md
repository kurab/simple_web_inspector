# Simple Web Inspector

This script does not cover all items should be tested. Script basically focuses on HTTP Status.

- internal_url_collector.py: create internal url list in site
- simple_web_inspector.py: test some items on url list

## Motivation

As a PM, I want to test developing web services comprehensively without minimum efforts.
I want to automatically test things that web site should sutisfy at least. And manage results history by git (with text file). And practice Python ^^

## Requirements

- Python 3.6 or higher
- requests
- bs4/BeautifulSoup

## Internal Link Collector

Script find all hyperlinks(a tag) on start page and repeat it on found links some times. You can set maximum iteration number in script: DEPTH.

Usage

```zsh
$ touch internal_links.txt
$ python internal_link_collector.py
```

## Simple Web Inspector

This script inspects following items:

- page url
- http status
- TDK
- empty link(href="" or not set)
- temporary link suspected(href="#")
- dead link(404)
- redirected link(301,302)
- count and status of css, js, font, favicon and img

see [sample/report.md](sample/report.md)

It will take much time to inspect whole web site. If you don't need to care about robot access to your development enviroment, adjust INTERVEL_SLEEP in code. still take much time. Take a break.

```zsh
$ python simple_web_inspector.py
```

## LICENSE

MIT

## note

Contact me if you need more Intelligent Automation Web Testing.
