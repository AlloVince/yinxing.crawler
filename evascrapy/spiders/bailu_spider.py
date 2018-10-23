# -*- coding: utf-8 -*-
import math
import time
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, Request
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


domain = os.environ.get('DOMAIN') or 'www.100aa.pw'


class BailuSpider(BaseSpider):
    version = '1.0.0'
    name = 'bailu'
    allowed_domains = [domain]
    start_urls = [
        'http://%s' % domain,
    ]

    deep_start_urls = [
        'http://%s' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='forum-(2|36|37|38|55|76|77)-(1|2|3|4|5|6|7|8|9)\.html', ), follow=True),
        Rule(LinkExtractor(allow='thread-\d+-1-1.html', ), follow=True, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='forum-(2|36|37|38|55|76|77)-[-\w]+\.html', ), follow=True),
        Rule(LinkExtractor(allow='thread-\d+-1-1.html', ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        torrents = response.css('a[href^="forum.php?mod=attachment"]:contains("torrent")::attr(href)').extract()
        if len(torrents) < 1:
            return
        for torrent in torrents:
            request = DownloadRequest(
                url=response.urljoin(torrent),  # relative url to absolute
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
