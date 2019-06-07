# -*- coding: utf-8 -*-
import os
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem

domain = os.environ.get('DOMAIN') or 'onejav.com'


class OnejavSpider(BaseSpider):
    version = '1.0.0'
    name = 'onejav'
    allowed_domains = [domain]
    start_urls = [
        'https://%s/new' % domain,
    ]

    deep_start_urls = [
        'https://%s/actress/' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='/new\?page=(1|2|3|4|5|6|7|8|9|10)$', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/.+\.torrent$', ), follow=True, callback='handle_item'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/actress/\?page=\d+', ), follow=True),
        Rule(LinkExtractor(allow='/actress/[^/]+', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/.+\.torrent$', ), follow=True, callback='handle_item'),
    )

    def handle_item(self, response: Response) -> TorrentFileItem:
        from_url = response.request.headers.get('Referer', None)
        return TorrentFileItem(
            url=response.url,
            from_url=str(from_url, encoding='utf-8') if from_url else None,
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
