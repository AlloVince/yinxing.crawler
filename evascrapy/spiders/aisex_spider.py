# -*- coding: utf-8 -*-
import math
import time
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, FormRequest
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class DownloadRequest(FormRequest):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


domain = os.environ.get('DOMAIN') or 'www.aisex.com'


class AisexSpider(BaseSpider):
    version = '1.0.0'
    name = 'aisex'
    allowed_domains = [domain, 'www.jandown.com']
    start_urls = [
        'http://%s/bt/index.php' % domain,
    ]

    deep_start_urls = [
        'http://%s/bt/index.php' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='bt/thread.php\?fid=(16|4|5|22|11|6|23|24)$', ), follow=True),
        Rule(LinkExtractor(allow='bt/thread.php\?fid=(16|4|5|22|11|6|23|24)&page=(1|2|3|4|5|6|7|8|9)$', ), follow=True),
        Rule(LinkExtractor(allow='bt/htm_data/\d+/\d+/\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='link.php\?ref=\w+$', ), follow=False, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='bt/thread.php\?fid=(16|4|5|22|11|6|23|24)$', ), follow=True),
        Rule(LinkExtractor(allow='bt/thread.php\?fid=(16|4|5|22|11|6|23|24)&page=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='bt/htm_data/\d+/\d+/\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='link.php\?ref=\w+$', ), follow=False, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        [path, code] = response.request.url.split('=')
        if not code:
            return
        request = DownloadRequest(
            url='http://www.jandown.com/fetch.php',  # relative url to absolute
            callback=self.handle_item,
            formdata={'code': code},
            dont_filter=True
        )
        request.meta['from_url'] = response.url
        yield request

    def handle_item(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta['from_url'],
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
