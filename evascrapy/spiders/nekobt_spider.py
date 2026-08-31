# -*- coding: utf-8 -*-
"""nekoBT's public anime torrent index."""
import math
import time

from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class NekoBTSpider(BaseSpider):
    version = '1.0.0'
    name = 'nekobt'
    allowed_domains = ['nekobt.to']
    start_urls = ['https://nekobt.to/']
    deep_start_urls = ['https://nekobt.to/search']
    rules = (
        Rule(LinkExtractor(allow=r'/search(?:\?.*)?$'), follow=True),
        Rule(LinkExtractor(allow=r'/torrents/\d+$'), follow=True),
        Rule(LinkExtractor(
            allow=r'/api/v1/torrents/\d+/download\?public=true$'
        ), follow=False, callback='handle_torrent'),
    )
    deep_rules = rules
    custom_settings = {'CLOSESPIDER_ITEMCOUNT': 0}

    def handle_torrent(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.request.headers.get('Referer', b'').decode(
                'utf-8', errors='replace'
            ),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
