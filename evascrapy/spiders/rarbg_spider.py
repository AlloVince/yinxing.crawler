# -*- coding: utf-8 -*-
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, Request
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


class RarbgSpider(BaseSpider):
    version = '1.0.0'
    name = 'rarbg'
    allowed_domains = ['rarbgprx.org']
    start_urls = [
        'https://rarbgprx.org/torrents.php',
    ]

    deep_start_urls = [
        'https://rarbgprx.org/torrents.php',
    ]

    rules = (
        Rule(LinkExtractor(allow='torrents.php\?category', ), follow=True),
        Rule(LinkExtractor(allow='torrent/\w+', ), follow=True, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='torrents.php\?category', ), follow=True),
        Rule(LinkExtractor(allow='torrent/\w+', ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        torrents = response.css('a[href^="/download.php?id="]::attr(href)').extract()
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
