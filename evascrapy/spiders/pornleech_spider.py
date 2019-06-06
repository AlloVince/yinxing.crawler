# -*- coding: utf-8 -*-
import os
import re
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem
import bencode


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


domain = os.environ.get('DOMAIN') or 'pornleech.is'


class PornleechSpider(BaseSpider):
    version = '1.0.0'
    name = 'pornleech'
    allowed_domains = [domain]
    start_urls = [
        'http://%s/index.php?page=torrents' % domain,
    ]

    deep_start_urls = [
        'http://%s/index.php?page=torrents' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='^/index\.php.+pages=(1|2|3|4|5|6|7|8|9|10)$', ), follow=True),
        Rule(LinkExtractor(allow='.+-\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='download\.php.+\.torrent$', ), follow=False, callback='handle_item'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='^/index\.php.+pages=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='.+-\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='download\.php.+\.torrent$', ), follow=False, callback='handle_item'),
    )

    def handle_item(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.request.headers.get('Referer', None),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
