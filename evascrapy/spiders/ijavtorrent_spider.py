# -*- coding: utf-8 -*-
"""iJavTorrent's public paginated catalogue and torrent downloads."""
import math
import time

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class IjavtorrentSpider(BaseSpider):
    name = 'ijavtorrent'
    version = '1.0.0'
    allowed_domains = ['ijavtorrent.com', 'sukebei.nyaa.si']
    start_urls = ['https://ijavtorrent.com/']
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'/\?page=[1-9]\d*$'), follow=True),
        Rule(
            LinkExtractor(allow=r'/download/[1-9]\d*$'),
            follow=False,
            callback='handle_torrent',
        ),
    )
    deep_rules = rules
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'CLOSESPIDER_ITEMCOUNT': 0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 4,
        'DOWNLOAD_DELAY': 0.2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.5,
        'AUTOTHROTTLE_MAX_DELAY': 30,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
        'RETRY_TIMES': 3,
        'TELNETCONSOLE_ENABLED': False,
    }

    def handle_torrent(self, response: Response):
        body = response.body.lstrip()
        if not body.startswith(b'd') or b'4:info' not in body:
            self.logger.warning('Skipping non-torrent download: %s', response.url)
            return None

        return TorrentFileItem(
            url=response.url,
            from_url=response.meta.get('from_url', response.url),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
