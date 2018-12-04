# -*- coding: utf-8 -*-
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response
from evascrapy.items import TorrentFileItem


class YtsSpider(BaseSpider):
    version = '1.0.0'
    name = 'yts'
    allowed_domains = ['yts.am']
    start_urls = [
        'https://yts.am'
    ]

    deep_start_urls = [
        'https://yts.am'
    ]

    rules = (
        Rule(LinkExtractor(allow='/browse-movies?page=(1|2|3|4|5|6|7|8|9)$', ), follow=True),
        Rule(LinkExtractor(allow='/movie/\w+', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/download/\w+', ), callback='handle_item'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/browse-movies?page=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='/movie/\w+', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/download/\w+', ), callback='handle_item'),
    )

    def handle_item(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.request.headers.get('Referer', '').decode('utf-8'),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
