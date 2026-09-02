# -*- coding: utf-8 -*-
"""Shana Project's public anime release torrent feed."""
import math
import time

from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class ShanaProjectSpider(BaseSpider):
    version = '1.1.0'
    name = 'shanaproject'
    allowed_domains = ['www.shanaproject.com', 'media.shanaproject.com']
    start_urls = ['https://www.shanaproject.com/']
    deep_start_urls = ['https://www.shanaproject.com/']
    rules = (
        # Shana's catalogue uses /anime/<page>/ for pagination.
        Rule(LinkExtractor(allow=r'/anime/[1-9]\d*/$'), follow=True),
        Rule(LinkExtractor(allow=r'/download/\d+/$'), follow=False,
             callback='handle_torrent'),
    )
    deep_rules = rules
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 0,
        # The media host intermittently resets concurrent connections.
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 0.5,
        'RETRY_TIMES': 5,
    }

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
