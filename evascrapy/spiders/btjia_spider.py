# -*- coding: utf-8 -*-
import re
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


regex = re.compile(r'attach-dialog-fid-1-aid-(\d+)-ajax-1.htm$')


class BtjiaSpider(BaseSpider):
    version = '1.0.0'
    name = 'btjia'
    allowed_domains = ['www.btjia.com']
    start_urls = [
        'http://www.btjia.com/'
    ]

    deep_start_urls = [
        'http://www.btjia.com/'
    ]

    rules = (
        Rule(LinkExtractor(allow='forum-index-fid-(1|9).htm$', ), follow=True),
        Rule(LinkExtractor(allow='forum-index-fid-(1|9)-page-(1|2|3|4|5|6|7|8|9)\.htm$', ), follow=True),
        Rule(LinkExtractor(allow='thread-index-fid-(1|9)-tid-\d+.htm$', ), follow=False, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='forum-index-fid-(1|9).htm$', ), follow=True),
        Rule(LinkExtractor(allow='forum-index-fid-(1|9)-page-\d+\.htm$', ), follow=True),
        Rule(LinkExtractor(allow='thread-index-fid-(1|9)-tid-\d+.htm$', ), follow=False, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        torrents = response.css('a[href$="-ajax-1.htm"]:contains("torrent")::attr(href)').extract()
        if len(torrents) < 1:
            return
        for torrent in torrents:
            match = regex.search(torrent)
            if not match:
                continue

            url = response.urljoin('/attach-download-fid-1-aid-%s.htm' % match.group(1))
            request = DownloadRequest(
                url=url,
                callback=self.handle_item,
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
