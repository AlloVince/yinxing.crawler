# -*- coding: utf-8 -*-
"""Internet Archive's public Archive BitTorrent collection."""
import json
import math
import time

from scrapy import Request
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class ArchiveSpider(BaseSpider):
    version = '1.0.0'
    name = 'archive'
    allowed_domains = ['archive.org']
    start_urls = [
        'https://archive.org/advancedsearch.php?'
        'q=format:%22Archive%20BitTorrent%22&fl[]=identifier&rows=50&page=1&output=json'
    ]
    deep_start_urls = start_urls
    custom_settings = {'CLOSESPIDER_ITEMCOUNT': 0}

    def parse_start_url(self, response: Response):
        yield from self.parse_api(response)

    def parse_api(self, response: Response):
        data = json.loads(response.text)
        docs = data.get('response', {}).get('docs', [])
        for doc in docs:
            identifier = doc.get('identifier')
            if identifier:
                yield Request(
                    f'https://archive.org/details/{identifier}',
                    callback=self.parse_detail,
                )

        page = data.get('response', {}).get('start', 0) // max(len(docs), 1) + 2
        total = data.get('response', {}).get('numFound', 0)
        if docs and page <= math.ceil(total / len(docs)):
            yield response.request.replace(
                url=response.url.replace(
                    f'page={page - 1}', f'page={page}'
                ),
                callback=self.parse_api,
            )

    def parse_detail(self, response: Response):
        for href in response.css('a[href$="_archive.torrent"]::attr(href)').getall():
            url = response.urljoin(href)
            yield Request(
                url,
                callback=self.handle_torrent,
                meta={'from_url': response.url},
            )

    def handle_torrent(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta.get('from_url', response.url),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
