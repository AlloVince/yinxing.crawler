# -*- coding: utf-8 -*-
"""AnimeTosho's anime torrent archive and current listing pages."""
import math
import time

from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class AnimeToshoSpider(BaseSpider):
    version = '1.0.0'
    name = 'animetosho'
    allowed_domains = ['animetosho.org', 'storage.animetosho.org']
    start_urls = ['https://animetosho.org/']
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'\?page=\d+$'), follow=True),
        Rule(LinkExtractor(
            allow=r'/storage/torrent/[0-9a-f]{40}/[^?]+\.torrent$'
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
