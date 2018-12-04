# -*- coding: utf-8 -*-
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


class EztvSpider(BaseSpider):
    version = '1.0.0'
    name = 'eztv'
    allowed_domains = ['eztv.io']
    start_urls = [
        'https://eztv.io'
    ]

    deep_start_urls = [
        'https://eztv.io'
    ]

    rules = (
        Rule(LinkExtractor(allow='/page_(1|2|3|4|5|6|7|8|9)$', ), follow=True, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/page_\d+$', ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        torrents = response.css('a[href$=".torrent"]::attr(href)').extract()
        if len(torrents) < 1:
            return
        for torrent in torrents:
            request = DownloadRequest(
                url=torrent,
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
