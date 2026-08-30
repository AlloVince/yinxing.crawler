# -*- coding: utf-8 -*-
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class YtsSpider(BaseSpider):
    version = '1.1.0'
    name = 'yts'
    allowed_domains = ['yts.gg']
    start_urls = ['https://yts.gg/']
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'/browse-movies(?:\?page=\d+|/[^/?]+(?:/[^/?]+)*)?$'), follow=True),
        Rule(LinkExtractor(allow=r'/movies/[^/?]+$'), follow=True),
        Rule(LinkExtractor(allow=r'/torrent/download/[A-Fa-f0-9]+$'), follow=False, callback='handle_item'),
    )
    deep_rules = rules

    def handle_item(self, response: Response) -> TorrentFileItem:
        from_url = response.request.headers.get('Referer', b'')
        if isinstance(from_url, bytes):
            from_url = from_url.decode('utf-8', errors='replace')
        return TorrentFileItem(url=response.url, from_url=from_url,
                               task=self.settings.get('APP_TASK'), version=self.version,
                               timestamp=math.floor(time.time()), body=response.body)
