# -*- coding: utf-8 -*-
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem


class TokyotoshoSpider(BaseSpider):
    version = '1.0.0'
    name = 'tokyotosho'
    allowed_domains = ['www.tokyotosho.info']
    start_urls = [
        'https://www.tokyotosho.info/'
    ]

    deep_start_urls = [
        'https://www.tokyotosho.info/'
    ]

    rules = (
        Rule(LinkExtractor(allow='www.tokyotosho.info/\?page=([0-9]|10)&cat=0', ), follow=True, callback='handle_list'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='www.tokyotosho.info/\?', ), follow=True, callback='handle_list'),
    )

    def handle_list(self, response: Response) -> Request:
        torrents = response.css('td.desc-top a[type="application/x-bittorrent"]::attr(href)').extract()
        if len(torrents) > 0:
            for torrent in torrents:
                request = Request(url=torrent, callback=self.handle_item, dont_filter=True)
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
