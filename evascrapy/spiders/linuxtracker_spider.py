# -*- coding: utf-8 -*-
"""LinuxTracker's public Linux and open-source torrent catalogue."""
import math
import re
import time

from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class LinuxTrackerSpider(BaseSpider):
    version = '1.0.0'
    name = 'linuxtracker'
    allowed_domains = ['linuxtracker.org']
    start_urls = [
        'https://linuxtracker.org/?lang=en',
        'https://linuxtracker.org/index.php?page=torrents',
    ]
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(
            allow=r'index\.php\?page=torrents(?:&pagenumber=\d+)?$'
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'(?:index\.php|/\?page)=torrent-details&id=[0-9a-f]{40}'
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'index\.php\?id=[0-9a-f]{40}&page=downloadcheck'
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'download\.php\?f=[^#]+\.torrent&id=[0-9a-f]{40}'
        ), follow=False, callback='handle_torrent'),
    )
    deep_rules = rules
    custom_settings = {'CLOSESPIDER_ITEMCOUNT': 0}

    def handle_torrent(self, response: Response) -> TorrentFileItem:
        if not re.search(r'\.torrent(?:&|$)', response.url, re.I):
            return None
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
