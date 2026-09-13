# -*- coding: utf-8 -*-
"""JAVJunkies date archives and its legacy JavaScript torrent links."""
import html
import math
import re
import time

from bencodepy import BencodeDecodeError, BencodeDecoder
from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class JavjunkiesSpider(BaseSpider):
    name = 'javjunkies'
    version = '1.0.0'
    allowed_domains = ['javjunkies.org']
    start_urls = ['https://javjunkies.org/main/']
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'/main/\d{4}/\d{2}-\d{2}-18(?:/\d+)?/?$'),
             follow=False, callback='open_download_gate'),
    )
    deep_rules = (
        Rule(LinkExtractor(allow=r'/main/\d{4}/(?:\d{2}/|\d{2}-\d{2}-18(?:/\d+)?/?)$'),
             follow=False, callback='open_download_gate'),
    )
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'USER_AGENT': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/140.0.0.0 Safari/537.36'
        ),
        'CLOSESPIDER_ITEMCOUNT': 0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'DOWNLOAD_DELAY': 0.5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 30,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'RETRY_TIMES': 3,
        'TELNETCONSOLE_ENABLED': False,
    }
    download_pattern = re.compile(r"JOpen\(['\"]([^'\"]*file=[^'\"]+)")
    download_key_pattern = re.compile(r'Jl\.php\?kEy=(\d+)')
    archive_pattern = re.compile(r'/main/\d{4}/\d{2}-\d{2}-18(?:/\d+)?/?$')
    torrent_decoder = BencodeDecoder(
        encoding='utf-8', encoding_fallback='value', dict_ordered=True,
    )

    def parse_start_url(self, response: Response):
        onclicks = response.css('a[onclick*="location.href"]::attr(onclick)').getall()
        archive_urls = []
        for onclick in onclicks:
            match = re.search(r"location\.href=['\"]([^'\"]+)", onclick)
            if not match:
                continue
            url = response.urljoin(html.unescape(match.group(1)))
            if self.archive_pattern.search(url):
                archive_urls.append(url)
        if not archive_urls:
            archive_urls = [response.url]
        if not self.settings.getbool('APP_RUN_DEEP'):
            archive_urls = archive_urls[:1]
        for url in archive_urls:
            yield response.follow(url, callback=self.open_download_gate)

    def open_download_gate(self, response: Response):
        key_match = self.download_key_pattern.search(response.text)
        archive_urls = []
        for href in response.css('a::attr(href)').getall():
            url = response.urljoin(html.unescape(href))
            if url != response.url and self.archive_pattern.search(url):
                archive_urls.append(url)

        if not key_match:
            self.logger.warning('Skipping archive without a download key: %s', response.url)
            for url in archive_urls:
                yield response.follow(url, callback=self.open_download_gate)
            return

        download_urls = []
        for encoded in self.download_pattern.findall(response.text):
            link = html.unescape(encoded)
            download_urls.append(
                response.urljoin('/main/Jl.php?kEy=' + key_match.group(1) + link)
            )
        yield response.follow(
            '/JJ1.php',
            callback=self.parse_jj1,
            meta={
                'archive_urls': archive_urls,
                'download_urls': download_urls,
                'from_url': response.url,
                'dont_redirect': True,
                'handle_httpstatus_list': [302],
            },
            dont_filter=True,
        )

    def parse_jj1(self, response: Response):
        for url in response.meta['archive_urls']:
            yield response.follow(url, callback=self.open_download_gate, priority=-10)
        for url in response.meta['download_urls']:
            yield Request(
                url,
                callback=self.handle_torrent,
                meta={'from_url': response.meta['from_url']},
                priority=10,
            )

    def handle_torrent(self, response: Response):
        body = response.body.lstrip()
        if not body.startswith(b'd') or b'4:info' not in body:
            self.logger.warning('Skipping non-torrent download: %s', response.url)
            return None
        try:
            torrent, consumed = self.torrent_decoder.decode_dict(body, 0)
        except (BencodeDecodeError, IndexError, KeyError, RecursionError, TypeError, ValueError):
            self.logger.warning('Skipping malformed torrent: %s', response.url)
            return None
        if not isinstance(torrent.get('info'), dict):
            self.logger.warning('Skipping torrent without info: %s', response.url)
            return None
        if consumed != len(body):
            self.logger.warning(
                'Discarding %d trailing bytes from torrent: %s',
                len(body) - consumed, response.url,
            )
            body = body[:consumed]
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta.get('from_url', response.url),
            task=self.settings.get('APP_TASK'), version=self.version,
            timestamp=math.floor(time.time()), body=body,
        )
