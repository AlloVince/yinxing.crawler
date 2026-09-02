# -*- coding: utf-8 -*-
"""XXXClub's public cursor-paginated catalogue and torrent downloads."""
import math
import re
import time

from scrapy import Request
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class XxxclubSpider(BaseSpider):
    name = 'xxxclub'
    version = '1.0.0'
    allowed_domains = ['xxxclub.to']
    start_urls = ['https://xxxclub.to/torrents/browse/all/']
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': 'Mozilla/5.0 (compatible; EvaScrapy/2.1.12)',
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
    # Current listing entries use a tilde followed by a negative numeric id
    # (for example ``/torrents/details/~-734765937293015000``).  The
    # recommended-torrent links still use positive ids.
    detail_pattern = re.compile(r'/torrents/details/~?-?\d+$')
    download_pattern = re.compile(r'/torrents/download/[0-9a-f]{40}$')

    def parse_start_url(self, response: Response):
        yield from self.parse_listing(response)

    def parse_listing(self, response: Response):
        for href in response.css('a[href^="/torrents/details/"]::attr(href)').getall():
            if not self.detail_pattern.fullmatch(href):
                continue
            detail_url = response.urljoin(href)
            yield Request(
                detail_url,
                callback=self.parse_detail,
                meta={'from_url': response.url, 'detail_url': detail_url},
            )

        next_href = response.css(
            '.browsepagination a[data-no-instant]::attr(href)'
        ).get()
        if next_href:
            next_url = response.urljoin(next_href)
            if next_url != response.url:
                yield response.follow(next_url, callback=self.parse_listing)

    def parse_detail(self, response: Response):
        for href in response.css(
            'a[href^="/torrents/download/"]::attr(href)'
        ).getall():
            if not self.download_pattern.fullmatch(href):
                continue
            torrent_url = response.urljoin(href)
            yield Request(
                torrent_url,
                callback=self.handle_torrent,
                meta={'from_url': response.url, 'detail_url': torrent_url},
            )

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
