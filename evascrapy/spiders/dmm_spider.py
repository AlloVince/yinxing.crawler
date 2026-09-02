"""DVD catalogue crawl; keep RawHtmlItem identities/storage unchanged.

Regular runs read the newest date-sorted catalogue and stop around 1,000
details. Deep runs traverse maker, actress and date catalogues. Never traverse
facets, sorting permutations, search, recommendations or other DMM services.
The strategy marker rejects legacy deep queues.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from typing import ClassVar
from urllib.parse import urljoin, urlsplit

from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


def _deep_enabled():
    return os.getenv('APP_RUN_DEEP', '').strip().lower() in {'1', 'true', 'yes', 'on'}


class DmmSpider(BaseSpider):
    version = '1.0.0'  # Raw HTML contract, not crawl-strategy version.
    name = 'dmm'
    allowed_domains: ClassVar = ['www.dmm.co.jp']
    origin = 'https://www.dmm.co.jp'
    prefix = '/mono/dvd/-/'
    strategy = 'dmm-catalog-v2'
    age_check_cookies: ClassVar = {'age_check_done': '1'}
    start_urls: ClassVar = [
        origin + prefix + 'list/=/sort=date/',
    ]
    deep_start_urls = [
        origin + prefix + 'maker/',
        origin + prefix + 'list/=/sort=date/',
        origin + prefix + 'actress/',
    ]
    rules = (
        Rule(
            LinkExtractor(allow=(r'/mono/dvd/-/detail/=/cid=[\w-]+/',)),
            callback='parse_detail',
            follow=False,
            process_links='process_detail_links',
            process_request='process_detail_request',
        ),
    )
    deep_rules = rules
    regular_max_items = 1000
    detail_pattern = re.compile(r'/mono/dvd/-/detail/=/cid=[\w-]+/', re.ASCII)
    directory_pattern = re.compile(
        r'/mono/dvd/-/(?:maker|actress)/(?:=/keyword=[a-z]+/(?:page=[1-9]\d*/)?)?'
    )
    list_pattern = re.compile(
        r'/mono/dvd/-/list/=/((?:article=(?:maker|label|actress)/id=[1-9]\d*/|sort=date/))'
        r'(?:page=[1-9]\d*/)?'
    )
    count_pattern = re.compile(
        r'([\d,]+)タイトル中\s*([\d,]+)[～〜－-]([\d,]+)タイトル\s*([\d,]+)ページ目'
    )

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.state = {}
        spider.job_path = None
        jobdir = crawler.settings.get('JOBDIR')
        if jobdir:
            spider.job_path = Path(jobdir)
            marker = spider.job_path / 'dmm-strategy.json'
            identity = {'strategy': cls.strategy, 'task': crawler.settings.get('APP_TASK')}
            if marker.exists():
                if json.loads(marker.read_text()) != identity:
                    raise ValueError('DMM JOBDIR strategy/task mismatch; use a new directory')
            else:
                legacy = ('requests.seen', 'requests.queue', 'spider.state')
                if any((spider.job_path / name).exists() for name in legacy):
                    raise ValueError('Legacy DMM JOBDIR rejected; preserve it and use a new directory')
                spider.job_path.mkdir(parents=True, exist_ok=True)
                marker.write_text(json.dumps(identity) + '\n')
        crawler.signals.connect(spider.item_stored, signal=signals.item_scraped)
        crawler.signals.connect(spider.item_failed, signal=signals.item_error)
        return spider

    def canonical_url(self, url):
        """Whitelist before scheduling; stripping a facet would lose page meaning."""
        parts = urlsplit(urljoin(self.origin, url))
        if parts.scheme not in {'http', 'https'} or parts.netloc != 'www.dmm.co.jp':
            return None
        path = parts.path.rstrip('/') + '/'
        path = re.sub(r'/page=1/$', '/', path)
        if any(p.fullmatch(path) for p in (
            self.detail_pattern, self.directory_pattern, self.list_pattern,
        )):
            return self.origin + path
        return None

    def request_for(self, url, **kwargs):
        url = self.canonical_url(url)
        if not url:
            return None
        if '/detail/' in url:
            callback, priority = self.parse_detail, 20
        elif '/list/' in url:
            callback = self.parse_list
            priority = -10 if 'article=actress/' in url else (5 if 'sort=date/' in url else 10)
        else:
            callback = self.parse_directory
            priority = -20 if '/actress/' in url else 8
        return Request(url, callback=callback, errback=self.request_failed,
                       cookies=self.age_check_cookies, priority=priority, **kwargs)

    def is_deep(self):
        return _deep_enabled()

    async def start(self):
        for url in self.start_urls:
            yield self.request_for(url)

    def parse_start_url(self, response, **kwargs):
        # Also accepts the CrawlSpider / external start-request entry point.
        if '/detail/' in response.url:
            return self.parse_detail(response)
        if '/list/' in response.url:
            return self.parse_list(response)
        return self.parse_directory(response)

    def process_detail_links(self, links):
        """Let CrawlSpider discover details, while keeping regular runs bounded."""
        if self.is_deep():
            return links
        remaining = self.regular_max_items - self.state.get('regular_items_scheduled', 0)
        selected = links[:max(0, remaining)]
        self.state['regular_items_scheduled'] = (
            self.state.get('regular_items_scheduled', 0) + len(selected)
        )
        return selected

    def process_detail_request(self, request):
        return request.replace(cookies=self.age_check_cookies, errback=self.request_failed)

    def links(self, response, selector='a::attr(href)'):
        return sorted({url for href in response.css(selector).getall()
                       if (url := self.canonical_url(response.urljoin(href)))})

    @staticmethod
    def page_number(url):
        match = re.search(r'/page=(\d+)/', url)
        return int(match[1]) if match else 1

    @staticmethod
    def partition(url):
        return re.sub(r'/page=\d+/$', '/', url)

    def next_page(self, response, links):
        root = self.partition(response.url)
        number = self.page_number(response.url)
        # Follow only the rendered immediate successor in the SAME partition.
        # Never synthesize page 418, follow "last" first or fan out every page.
        return next((url for url in links if self.partition(url) == root
                     and self.page_number(url) == number + 1), None)

    def check_response(self, response):
        if self.canonical_url(response.url) != response.url:
            self.record_failure(response.url, 'unexpected_redirect')
            raise CloseSpider('dmm_unexpected_redirect')

    def parse_directory(self, response, previous_signature=None):
        self.check_response(response)
        links = self.links(response)
        kind = 'maker' if '/maker/' in response.url else 'actress'
        catalogues = [u for u in links if f'/article={kind}/' in u and '/page=' not in u]
        if not catalogues:
            self.record_failure(response.url, 'empty_directory')
            return
        signature = hashlib.sha256('\n'.join(catalogues).encode()).hexdigest()
        if signature == previous_signature:
            self.record_failure(response.url, 'repeated_directory_page')
            return
        self.crawler.stats.inc_value('dmm/directory_pages')
        for url in catalogues:
            yield self.request_for(url)
        if '/keyword=' not in response.url:
            for url in links:
                if f'/{kind}/=/keyword=' in url and '/page=' not in url:
                    yield self.request_for(url)
        if url := self.next_page(response, links):
            yield self.request_for(url, cb_kwargs={'previous_signature': signature})

    def parse_list(self, response, previous_signature=None):
        self.check_response(response)
        links = self.links(response)
        details = self.links(response, '#list a::attr(href)')
        details = [u for u in details if '/detail/' in u]
        count = self.count_pattern.search(response.xpath('string(//body)').get(''))
        if not details or not count:
            self.record_failure(response.url, 'invalid_list')
            return
        total, first, last, page = (int(v.replace(',', '')) for v in count.groups())
        if page != self.page_number(response.url) or last - first + 1 != len(details):
            self.record_failure(response.url, 'list_range_mismatch')
            return
        signature = hashlib.sha256('\n'.join(details).encode()).hexdigest()
        if signature == previous_signature:
            self.record_failure(response.url, 'repeated_list_page')
            return
        root = self.partition(response.url)
        entry = self.state.setdefault('partitions', {}).setdefault(root, {
            'advertised': total, 'pages': 0, 'references': 0, 'finished': False,
        })
        entry.update(advertised=total, last_page=page, last_position=last)
        entry['pages'] += 1

        if not self.is_deep():
            entry['capped'] = True

        entry['references'] += len(details)
        self.crawler.stats.inc_value('dmm/list_pages')
        next_url = self.next_page(response, links)
        if self.is_deep():
            selected_details = details
        else:
            remaining = self.regular_max_items - self.state.get('regular_items_scheduled', 0)
            selected_details = details[:max(0, remaining)]
            self.state['regular_items_scheduled'] = (
                self.state.get('regular_items_scheduled', 0) + len(selected_details)
            )
        for url in selected_details:
            yield self.request_for(url)
        if not self.is_deep() and (
            self.state.get('regular_items_scheduled', 0) >= self.regular_max_items
        ):
            next_url = None
        visible_last = max([self.page_number(u) for u in links
                            if self.partition(u) == root] + [page])
        if self.is_deep() and page == 1 and total > visible_last * len(details):
            entry['capped'] = True
            self.crawler.stats.inc_value('dmm/capped_partitions')
            self.logger.warning('Catalogue capped: %s advertised=%s visible_pages=%s',
                                root, total, visible_last)
        if next_url:
            yield self.request_for(next_url, cb_kwargs={'previous_signature': signature})
        else:
            entry['finished'] = True
            if self.is_deep() and last < total:
                entry['capped'] = True
                self.logger.warning('Catalogue ended before advertised total: %s %s/%s', root, last, total)
                self.crawler.stats.inc_value('dmm/truncated_partitions')

    def parse_detail(self, response):
        self.check_response(response)
        if not self.detail_pattern.fullmatch(urlsplit(response.url).path) or not response.css('h1#title'):
            self.record_failure(response.url, 'invalid_detail')
            return
        # HTML canonical often points at video.dmm.co.jp. Keep the DVD URL/CID:
        # using that canonical would change downstream raw-object identities.
        yield self.handle_item(response)
        if not self.is_deep():
            return
        links = self.links(response)
        makers = [u for u in links if '/article=maker/' in u and '/page=' not in u]
        for url in makers:
            if url not in self.state.get('partitions', {}):
                yield self.request_for(url)
        # Labels are a bounded fallback for an oversized maker, not a second
        # full sweep of every sorting/filter combination.
        if any(self.state.get('partitions', {}).get(u, {}).get('capped') for u in makers):
            for url in links:
                if '/article=label/' in url and '/page=' not in url:
                    yield self.request_for(url)

    def record_failure(self, url, reason):
        self.crawler.stats.inc_value('dmm/failures')
        self.state['failures'] = self.state.get('failures', 0) + 1
        self.logger.warning('DMM incomplete: %s %s', reason, url)
        if self.job_path:
            with (self.job_path / 'dmm-failures.jsonl').open('a') as stream:
                stream.write(json.dumps({'url': url, 'reason': reason}) + '\n')

    def request_failed(self, failure):
        self.record_failure(failure.request.url, failure.type.__name__)

    def item_stored(self, item, response, spider):
        self.state['items_stored'] = self.state.get('items_stored', 0) + 1

    def item_failed(self, item, response, spider, failure):
        self.record_failure(response.url, 'item_pipeline_error')

    def closed(self, reason):
        partitions = self.state.get('partitions', {})
        summary = {
            'strategy': self.strategy, 'close_reason': reason,
            'items_stored': self.state.get('items_stored', 0),
            'failures': self.state.get('failures', 0),
            'unfinished_partitions': sum(not p['finished'] for p in partitions.values()),
            'capped_partitions': sum(bool(p.get('capped')) for p in partitions.values()),
            'partitions': partitions,
        }
        if self.job_path:
            temporary = self.job_path / 'dmm-coverage.json.tmp'
            temporary.write_text(json.dumps(summary, indent=2) + '\n')
            temporary.replace(self.job_path / 'dmm-coverage.json')
        self.logger.info('DMM audit: stored=%s failures=%s unfinished=%s capped=%s; '
                         'queue exhaustion alone does not prove full catalogue coverage',
                         summary['items_stored'], summary['failures'],
                         summary['unfinished_partitions'], summary['capped_partitions'])
