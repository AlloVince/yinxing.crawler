# -*- coding: utf-8 -*-
"""TorrentFunk's public JSON catalogue and direct torrent-file host."""
import math
import os
import time

import scrapy
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


domain = os.getenv('TORRENTFUNK_DOMAIN', 'www.torrentfunk2.com')


class TorrentfunkSpider(BaseSpider):
    name = 'torrentfunk'
    version = '1.0.0'
    allowed_domains = [domain, 'f.t0r.space', 'ft.t0r.space']
    categories = (
        'movies', 'television', 'games', 'music', 'software', 'anime',
        'ebooks', 'adult',
    )
    max_pages = 10  # The API exposes at most the first 1,000 rows per query.
    start_urls = [
        'https://%s/api/latest.json?category=%s&limit=100&page=1'
        % (domain, category)
        for category in categories
    ]
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 0,
        # The API documents transient 503s and may drop datacenter connections.
        'RETRY_TIMES': 10,
    }

    def parse_start_url(self, response: Response):
        yield from self.parse_api(response)

    def parse_api(self, response: Response):
        try:
            payload = response.json()
        except ValueError:
            self.logger.warning('Ignoring non-JSON response: %s', response.url)
            return

        if payload.get('status') != 'ok':
            self.logger.warning('TorrentFunk API error at %s: %s', response.url, payload)
            return

        results = payload.get('results') or []
        for torrent in results:
            torrent_url = torrent.get('torrent_file')
            if not torrent_url or not torrent_url.lower().split('?', 1)[0].endswith('.torrent'):
                continue
            yield scrapy.Request(
                response.urljoin(torrent_url),
                callback=self.handle_torrent,
                meta={'from_url': torrent.get('url') or response.url},
            )

        page = int(payload.get('page') or 1)
        if results and page < self._max_pages():
            next_url = response.url.replace('page=%d' % page, 'page=%d' % (page + 1))
            yield scrapy.Request(next_url, callback=self.parse_api)

    def _max_pages(self):
        try:
            return max(1, int(os.getenv('TORRENTFUNK_MAX_PAGES', self.max_pages)))
        except ValueError:
            return self.max_pages

    def handle_torrent(self, response: Response) -> TorrentFileItem:
        from_url = response.meta.get('from_url', '')
        return TorrentFileItem(
            url=response.url,
            from_url=from_url,
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
