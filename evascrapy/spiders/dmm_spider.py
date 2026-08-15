# -*- coding: utf-8 -*-
"""DMM DVD spider: actress index -> actress-filtered lists -> details."""

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


class DmmSpider(BaseSpider):
    version = '1.0.0'
    name = 'dmm'
    allowed_domains = ['www.dmm.co.jp']

    actress_index_url = 'https://www.dmm.co.jp/mono/dvd/-/actress/'
    list_page_size = 120
    age_check_cookies = {'age_check_done': '1'}

    # The actress directory is the entry point.  The unfiltered ranking list
    # is intentionally not used because DMM limits the result set there.
    start_urls = [actress_index_url]
    deep_start_urls = [
        'https://www.dmm.co.jp/mono/dvd/-/list/=/sort=date/',
        'https://www.dmm.co.jp/mono/dvd/-/genre/=/display=syllabary/sort=ranking/',
        'https://www.dmm.co.jp/mono/dvd/-/maker/',
        'https://www.dmm.co.jp/mono/dvd/-/series/=/keyword=a/sort=ruby/',
        'https://www.dmm.co.jp/mono/dvd/-/actress/=/keyword=a/',
    ]

    rules = (
        # Actress directory and its syllabary/pagination pages.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/actress(?:/|$)',
            ),
            follow=True,
        ),
        # Each actress list is followed, including its pagination links.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/list/=/article=actress/id=\d+/',
            ),
            follow=True,
        ),
        # Only detail pages become RawHtmlItems.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/detail/=/cid=[^/]+/',
            ),
            follow=False,
            callback='handle_item',
        ),
    )
    deep_rules = (
        # Directory entry pages.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/(?:actress|maker|series)(?:/|$)',
            ),
            follow=True,
        ),
        # Filtered list pages, including pagination.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/list/=/article=(?:actress|series|maker|keyword)/id=\d+/',
            ),
            follow=True,
        ),
        # Detail pages.
        Rule(
            LinkExtractor(
                allow=r'mono/dvd/-/detail/=/cid=[^/]+/',
            ),
            follow=True,
            callback='handle_item',
        ),
    )

    async def start(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                dont_filter=True,
                cookies=self.age_check_cookies,
            )

    def _build_request(self, rule_index, link):
        """Normalize DMM links and request the maximum list page size."""
        url = link.url.split('?', 1)[0]
        if '/mono/dvd/-/list/=' in url and '/limit=' not in url:
            url = url.rstrip('/') + '/limit=%d/' % self.list_page_size

        request = Request(
            url=url,
            callback=self._callback,
            errback=self._errback,
            cookies=self.age_check_cookies,
        )
        request.meta.update(rule=rule_index, link_text=link.text)
        return request
