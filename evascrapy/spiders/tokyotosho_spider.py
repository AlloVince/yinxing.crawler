# -*- coding: utf-8 -*-
"""Tokyo Toshokan's public anime torrent listings."""
import math
import time

from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class TokyoToshoSpider(BaseSpider):
    version = '1.0.0'
    name = 'tokyotosho'
    allowed_domains = [
        'www.tokyotosho.info', 'ehtracker.org', 'nyaa.si',
        'www.anirena.com', 'raw.githubusercontent.com',
    ]
    start_urls = ['https://www.tokyotosho.info/']
    deep_start_urls = ['https://www.tokyotosho.info/?page=1&cat=0']
    rules = (
        Rule(LinkExtractor(allow=r'\?page=\d+&cat=\d+$'), follow=True),
        Rule(LinkExtractor(
            allow=r'https?://[^/]+/.+\.torrent(?:\?.*)?$'
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
