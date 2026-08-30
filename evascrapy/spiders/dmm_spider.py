# -*- coding: utf-8 -*-
"""DMM DVD spider: lists and actress-filtered lists -> details."""

import os

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


class DmmSpider(BaseSpider):
    version = '1.0.0'
    name = 'dmm'
    allowed_domains = ['www.dmm.co.jp']
    # A DMM run is expected to be interrupted and resumed over multiple days.
    # Keep its queue in a spider-specific directory: the mounted jobdir has
    # previously also been used by FANZA and must not be consumed as DMM state.
    custom_settings = {
        'JOBDIR': os.getenv('DMM_JOBDIR', 'jobdir/dmm'),
    }

    actress_index_url = 'https://www.dmm.co.jp/mono/dvd/-/actress/'
    age_check_cookies = {'age_check_done': '1'}

    # The actress directory is the entry point.  The unfiltered ranking list
    # is intentionally not used because DMM limits the result set there.
    start_urls = [actress_index_url]
    # APP_RUN_DEEP is enabled by the full-crawl deployment.  Keep that mode
    # on the same bounded discovery graph instead of switching to a ranking
    # page whose result set is limited and whose links expose filter facets.
    deep_start_urls = start_urls

    rules = (
        # Actress directory and its syllabary/pagination pages.
        Rule(
            LinkExtractor(
                allow=r'/mono/dvd/-/actress(?:/=/keyword=[a-z]+)?/?$',
            ),
            follow=True,
        ),
        # Follow only the canonical actress list and its numeric pagination.
        # DMM renders limit/price/view/rss and n1..n8 facet combinations on
        # the same page; those are alternate filters, not additional pages.
        Rule(
            LinkExtractor(
                allow=r'/mono/dvd/-/list/=/article=actress/id=\d+/(?:page=\d+/)?$',
            ),
            follow=True,
        ),
        # Only detail pages become RawHtmlItems.
        Rule(
            LinkExtractor(
                allow=r'/mono/dvd/-/detail/=/cid=[^/?]+/?$',
            ),
            follow=False,
            callback='handle_item',
        ),
    )
    # Full mode uses the same bounded rules.  Keeping one rule tuple prevents
    # the two execution modes from drifting apart.
    deep_rules = rules

    async def start(self):
        for url in self.start_urls:
            yield Request(
                url=url,
                dont_filter=True,
                cookies=self.age_check_cookies,
            )

    def _build_request(self, rule_index, link):
        """Build requests with the age-check cookie for DMM links."""
        url = link.url.split('?', 1)[0]

        request = Request(
            url=url,
            callback=self._callback,
            errback=self._errback,
            cookies=self.age_check_cookies,
        )
        request.meta.update(rule=rule_index, link_text=link.text)
        return request
