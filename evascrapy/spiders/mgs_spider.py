"""MGS video raw HTML crawler.

Deep runs walk the complete MGS catalogue pagination and schedule every
distinct product detail URL. The catalogue advertises its total and range
on each page, so the spider keeps those values in stats instead of treating
an empty queue as proof of full coverage.
"""

import json
import re
from pathlib import Path
from typing import ClassVar
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

from scrapy import Request

from evascrapy.base_spider import BaseSpider


class MgsSpider(BaseSpider):
    version = '0.2.0'
    name = 'mgs'
    strategy = 'mgs-catalog-v2'
    allowed_domains: ClassVar = ['www.mgstage.com']
    start_urls: ClassVar = [
        'https://www.mgstage.com/search/cSearch.php?sort=popular&list_cnt=120&type=top',
    ]
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules
    detail_path = re.compile(r'^/product/product_detail/[^/?#]+/?$', re.ASCII)
    count_pattern = re.compile(
        r'([\d,]+)タイトル中\s*([\d,]+)[～〜－-]([\d,]+)タイトル\s*([\d,]+)ページ目'
    )
    custom_settings: ClassVar = {
        'USER_AGENT': 'Mozilla/5.0',
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {'Cookie': 'adc=1; coc=1'},
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        jobdir = crawler.settings.get('JOBDIR')
        if jobdir:
            spider.job_path = Path(jobdir)
            marker = spider.job_path / 'mgs-strategy.json'
            identity = {'strategy': cls.strategy, 'task': crawler.settings.get('APP_TASK')}
            if marker.exists():
                if json.loads(marker.read_text()) != identity:
                    raise ValueError('MGS JOBDIR strategy/task mismatch; use a new directory')
            else:
                legacy = ('requests.seen', 'requests.queue', 'spider.state')
                if any((spider.job_path / name).exists() for name in legacy):
                    raise ValueError('Legacy MGS JOBDIR rejected; use a new catalogue directory')
                spider.job_path.mkdir(parents=True, exist_ok=True)
                marker.write_text(json.dumps(identity) + '\n')
        return spider

    def handle_item(self, response):
        response.meta['detail_url'] = response.url
        self.logger.info('mgs detail url=%s external_id=%s', response.url, response.url.rstrip('/').rsplit('/', 1)[-1])
        return super().handle_item(response)

    def start_requests(self):
        for url in self.start_urls:
            yield self.catalogue_request(url)

    async def start(self):
        for url in self.start_urls:
            yield self.catalogue_request(url)

    def catalogue_request(self, url):
        return Request(url, headers={'Cookie': 'adc=1; coc=1'}, callback=self.parse_listing)

    def detail_url(self, href, response):
        url = urljoin(response.url, href)
        parts = urlsplit(url)
        if parts.scheme not in {'http', 'https'} or parts.netloc != 'www.mgstage.com':
            return None
        if not self.detail_path.fullmatch(parts.path):
            return None
        return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip('/') + '/', '', ''))

    @staticmethod
    def page_number(url):
        page = parse_qs(urlsplit(url).query).get('page', ['1'])[0]
        return int(page) if page.isdigit() else 1

    @staticmethod
    def next_page_url(url):
        parts = urlsplit(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        query['page'] = [str(MgsSpider.page_number(url) + 1)]
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True), ''))

    def parse_listing(self, response):
        body = response.xpath('string(//body)').get('')
        count = self.count_pattern.search(body)
        if not count:
            self.logger.error('mgs listing missing count url=%s', response.url)
            self.crawler.stats.inc_value('mgs/listing_failures')
            return

        total, first, last, page = (int(value.replace(',', '')) for value in count.groups())
        actual_page = self.page_number(response.url)
        details = sorted(
            {
                url
                for href in response.css('a[href*="/product/product_detail/"]::attr(href)').getall()
                if (url := self.detail_url(href, response))
            }
        )
        if page != actual_page or last - first + 1 != len(details):
            self.logger.error(
                'mgs listing range mismatch url=%s advertised=%s-%s page=%s details=%s',
                response.url,
                first,
                last,
                page,
                len(details),
            )
            self.crawler.stats.inc_value('mgs/listing_failures')
            return

        self.crawler.stats.inc_value('mgs/list_pages')
        self.crawler.stats.set_value('mgs/advertised_titles', total)
        self.crawler.stats.set_value('mgs/last_page', page)
        self.crawler.stats.inc_value('mgs/detail_references', len(details))
        self.logger.info(
            'mgs listing page=%s range=%s-%s advertised=%s details=%s',
            page,
            first,
            last,
            total,
            len(details),
        )
        for url in details:
            yield Request(url, headers={'Cookie': 'adc=1; coc=1'}, callback=self.handle_item)

        if last < total:
            yield self.catalogue_request(self.next_page_url(response.url))
