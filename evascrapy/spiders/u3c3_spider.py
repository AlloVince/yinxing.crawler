# -*- coding: utf-8 -*-
"""U3C3's public U3C3 catalogue and direct torrent files."""
import math
import re
import time
from urllib.parse import parse_qs, urlencode, urlsplit

from scrapy import Request
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class U3c3Spider(BaseSpider):
    name = 'u3c3'
    version = '1.0.0'
    allowed_domains = ['u3c3.com']
    start_urls = ['https://u3c3.com/?type=U3C3&p=1']
    deep_start_urls = start_urls
    rules = ()
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
    fallback_max_pages = 14047

    def parse_start_url(self, response: Response):
        yield from self.parse_listing(response)

    def parse_listing(self, response: Response):
        for href in response.css('a[href^="/torrent/"][href$=".torrent"]::attr(href)').getall():
            torrent_url = response.urljoin(href)
            yield Request(
                torrent_url,
                callback=self.handle_torrent,
                meta={'from_url': response.url, 'detail_url': torrent_url},
            )

        query = parse_qs(urlsplit(response.url).query)
        try:
            page = int(query.get('p', ['1'])[0])
        except ValueError:
            self.logger.warning('Ignoring invalid page URL: %s', response.url)
            return

        total_pages = self._total_pages(response)
        if total_pages is None:
            total_pages = self.fallback_max_pages
        if page >= total_pages:
            return

        next_query = {'type': query.get('type', ['U3C3'])[0], 'p': page + 1}
        yield response.follow(
            '?' + urlencode(next_query),
            callback=self.parse_listing,
        )

    @staticmethod
    def _total_pages(response: Response):
        match = re.search(r'\btotalPages\s*:\s*(\d+)', response.text)
        return int(match.group(1)) if match else None

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
