# -*- coding: utf-8 -*-
import math
import os
import re
import time
from urllib.parse import urlencode

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


class NyaaSpider(BaseSpider):
    version = '1.1.0'
    name = 'nyaa'
    allowed_domains = ['sukebei.nyaa.si', 'nyaa.si']
    start_urls = [
        'https://sukebei.nyaa.si/',
        'https://nyaa.si/'
    ]

    deep_start_urls = [
        'https://sukebei.nyaa.si/',
        'https://nyaa.si/'
    ]

    # The old ``([0-9]|10)`` expression also matched the prefix of p=100,
    # while not expressing the actual listing boundary.  Keep the rule
    # limited to query listing pages: download/detail links must never be
    # followed as CrawlSpider pages.
    _listing_url = r'https?://(?:sukebei\.)?nyaa\.si/\?(?:[^#]*&)?(?:p=\d+|c=\d+(?:_\d+)?|q=[^#&]+)'
    rules = (
        Rule(
            LinkExtractor(allow=_listing_url),
            follow=True,
            callback='handle_list',
        ),
    )
    deep_rules = rules
    custom_settings = {
        # Do not inherit a publisher/container-level 15,000-item circuit
        # breaker for this explicitly unbounded, restartable crawl.
        'CLOSESPIDER_ITEMCOUNT': 0,
    }

    # The values mirror the site's public category selector.  They are a
    # fallback for a transient page that renders without the selector; normal
    # runs still discover the selector first so additions remain visible.
    category_codes = tuple(
        f'{group}_{subgroup}'
        for group, subgroups in ((1, range(5)), (2, range(3)), (3, range(4)),
                                 (4, range(5)), (5, range(3)), (6, range(3)))
        for subgroup in subgroups
    )

    # This is deliberately opt-in.  Category + pagination traversal is the
    # complete coverage path; search terms are useful for recovering gaps or
    # applying a targeted backfill without baking in a guessed word list.
    search_terms_env = 'NYAA_SEARCH_TERMS'

    @classmethod
    def _search_terms(cls):
        value = os.environ.get(cls.search_terms_env, '')
        return tuple(term.strip() for term in re.split(r'[,\n]+', value) if term.strip())

    def parse_start_url(self, response: Response):
        yield from self.handle_list(response)

        # Search is a supplement to the deterministic category walk.  Terms
        # are supplied as comma/newline separated text, e.g. ``anime,1080p``.
        for term in self._search_terms():
            yield response.follow('?' + urlencode({'q': term}), callback=self.handle_list)

    def handle_list(self, response: Response) -> Request:
        # Every category is linked in the site's own filter form.  Following
        # those links makes the crawl independent of the current front-page
        # distribution and avoids relying on a hand-maintained word list.
        seen_categories = set()
        for value in response.css('select[name="c"] option::attr(value)').getall():
            if value != '0_0' and re.fullmatch(r'\d+_\d+', value):
                seen_categories.add(value)
        for value in (*self.category_codes, *sorted(seen_categories - set(self.category_codes))):
            yield response.follow(f'?c={value}', callback=self.handle_list)

        torrents = response.css('td a[href$=torrent]::attr(href)').extract()
        for torrent in torrents:
            request = DownloadRequest(
                url=response.urljoin(torrent),  # relative url to absolute
                callback=self.handle_item,
                dont_filter=True
            )
            request.meta['from_url'] = response.url
            request.meta['detail_url'] = request.url
            yield request

    def handle_item(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta['from_url'],
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
