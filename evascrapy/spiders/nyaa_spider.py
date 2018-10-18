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


class NyaaSpider(BaseSpider):
    version = '1.0.0'
    name = 'nyaa'
    allowed_domains = ['sukebei.nyaa.si', 'nyaa.si']
    start_urls = [
        'https://sukebei.nyaa.si/',
        'https://nyaa.si/'
    ]

    deep_start_urls = [
        'https://sukebei.nyaa.si/',
        'https://nyaa.si/'
    ]

    rules = (
        Rule(LinkExtractor(allow='sukebei.nyaa.si/\?p=([0-9]|10)', ), follow=True, callback='handle_list'),
        Rule(LinkExtractor(allow='nyaa.si/\?p=([0-9]|10)', ), follow=True, callback='handle_list'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='sukebei.nyaa.si/\?', ), follow=True, callback='handle_list'),
        Rule(LinkExtractor(allow='nyaa.si/\?', ), follow=True, callback='handle_list'),
    )

    def handle_list(self, response: Response) -> Request:
        torrents = response.css('td a[href$=torrent]::attr(href)').extract()
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
