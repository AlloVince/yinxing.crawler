# -*- coding: utf-8 -*-
"""Public-only SeHuaTang Discuz pages and openly exposed torrent attachments."""
import math
import re
import time
from urllib.parse import parse_qs, urlsplit

from scrapy import Request
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class SehuatangSpider(BaseSpider):
    name = 'sehuatang'
    version = '1.0.0'
    allowed_domains = ['www.sehuatang.net', 'xia.djhdhs.us']
    board_ids = (2, 36, 37, 160, 104, 38, 151, 39)
    start_urls = [
        'https://www.sehuatang.net/forum-{}-1.html'.format(board_id)
        for board_id in board_ids
    ]
    deep_start_urls = start_urls

    # The rules deliberately begin at the public forum index.  No login,
    # cookie, invite-code, challenge-solving, or guessed private board URL is
    # used.  Every rule is constrained to the boards below; attachment links
    # are followed only when a scoped public thread exposes them in its HTML.
    board_pattern = r'(?:2|36|37|160|104|38|151|39)'
    rules = (
        Rule(LinkExtractor(
            allow=(
                r'/(?:forum\.php\?mod=forumdisplay&fid=' + board_pattern
                + r'(?:[&#][^#]*)?|forum-' + board_pattern
                + r'-\d+\.html)$'
            )
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'/(?:forum\.php\?mod=viewthread&tid=\d+[^#]*|thread-\d+-\d+-\d+\.html)$'
        ), follow=True, process_request='scope_thread_request'),
        Rule(LinkExtractor(
            allow=r'/forum\.php\?mod=attachment&[^#]*'
        ), follow=False, callback='handle_attachment'),
    )
    deep_rules = rules
    custom_settings = {
        'CLOSESPIDER_ITEMCOUNT': 0,
        # The site returns HTTP 403 to Scrapy's default user agent after the
        # entry page.  Match a normal browser request while keeping crawling
        # rate controlled by the deployment settings.
        'USER_AGENT': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/140.0.0.0 Safari/537.36'
        ),
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': (
                'text/html,application/xhtml+xml,application/xml;q=0.9,'
                'image/avif,image/webp,*/*;q=0.8'
            ),
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        },
    }

    _SAFE_ID_RE = re.compile(r"\bvar\s+safeid\s*=\s*['\"]([^'\"]+)['\"]")
    _BOARD_PATH_RE = re.compile(r'/forum-(\d+)-(\d+)\.html$')
    _THREAD_PATH_RE = re.compile(r'/thread-(\d+)-(\d+)-\d+\.html$')
    _THREAD_QUERY_RE = re.compile(r'/forum\.php\?mod=viewthread&tid=(\d+)')
    _BOARD_RE = re.compile(
        r'/forum-(?:2|36|37|160|104|38|151|39)-\d+\.html$'
        r'|/forum\.php\?mod=forumdisplay&fid=(?:2|36|37|160|104|38|151|39)(?:[&#]|$)'
    )

    def start_requests(self):
        """Use native board URLs; the equivalent SEO paths return HTTP 403."""
        for entry_url in self.start_urls:
            match = self._BOARD_PATH_RE.search(entry_url)
            if match:
                board_id, page = match.groups()
                entry_url = (
                    'https://www.sehuatang.net/forum.php?mod=forumdisplay'
                    '&fid={}&page={}'.format(board_id, page)
                )
            yield Request(entry_url, callback=self._parse, dont_filter=True)

    async def start(self):
        """Apply the scoped native-URL start logic on Scrapy 2.13+."""
        for request in self.start_requests():
            yield request

    def _parse(self, response: Response, **kwargs):
        """Retry any SeHuaTang confirmation page before applying the rules."""
        safe_id = self._SAFE_ID_RE.search(response.text)
        if safe_id and not response.meta.get('sehuatang_safe_retry'):
            self.logger.info('Retrying SeHuaTang page with confirmation cookie: %s', response.url)
            meta = {
                key: response.meta[key]
                for key in ('cookiejar', 'sehuatang_scope')
                if key in response.meta
            }
            meta['sehuatang_safe_retry'] = True
            return [Request(
                response.url,
                callback=self._parse,
                cookies={'_safe': safe_id.group(1)},
                dont_filter=True,
                meta=meta,
            )]

        if safe_id:
            self.logger.warning('SeHuaTang confirmation gate still present after cookie retry: %s', response.url)
        return super()._parse(response, **kwargs)

    def scope_thread_request(self, request, response):
        """Keep traversal scoped and restricted to the first thread page."""
        if 'authorid=' in request.url:
            return None
        response_meta = response.request.meta if response.request else {}
        if not self._BOARD_RE.search(response.url) and not response_meta.get(
            'sehuatang_scope'
        ):
            return None
        match = self._THREAD_PATH_RE.search(request.url)
        if match:
            tid, page = match.groups()
            if page != '1':
                return None
            target_tid = tid
            request = request.replace(
                url=response.urljoin(
                    'forum.php?mod=viewthread&tid={}&page={}'.format(tid, page)
                )
            )
        else:
            target_tid = self._THREAD_QUERY_RE.search(request.url).group(1)
            page = parse_qs(urlsplit(request.url).query).get('page', ['1'])[0]
            if page != '1':
                return None

        source_thread = self._THREAD_QUERY_RE.search(response.url)
        if source_thread and source_thread.group(1) != target_tid:
            return None
        request.meta['sehuatang_scope'] = True
        return request

    def normalize_thread_request(self, request, response):
        """Backward-compatible alias for callers/tests using the old name."""
        return self.scope_thread_request(request, response)

    def parse_start_url(self, response: Response):
        """Pass SeHuaTang's JavaScript confirmation gate once.

        The public entry page serves a generated confirmation page before the
        forum.  Its JavaScript writes ``_safe=<safeid>`` and reloads the same
        URL.  Scrapy does not run that JavaScript, so reproduce only that
        documented page transition and leave all other cookies untouched.
        """
        safe_id = self._SAFE_ID_RE.search(response.text)
        request_meta = response.request.meta if response.request else {}
        if safe_id and not request_meta.get('sehuatang_safe_retry'):
            self.logger.info('Retrying SeHuaTang entry page with confirmation cookie')
            yield Request(
                response.url,
                cookies={'_safe': safe_id.group(1)},
                dont_filter=True,
                meta={'sehuatang_safe_retry': True},
            )
            return

        if safe_id:
            self.logger.warning('SeHuaTang confirmation gate still present after cookie retry')

    def handle_attachment(self, response: Response):
        safe_id = self._SAFE_ID_RE.search(response.text)
        if safe_id and not response.meta.get('sehuatang_safe_retry'):
            self.logger.info(
                'Retrying SeHuaTang attachment with confirmation cookie: %s',
                response.url,
            )
            meta = {
                key: response.meta[key]
                for key in ('cookiejar', 'sehuatang_scope')
                if key in response.meta
            }
            meta['sehuatang_safe_retry'] = True
            return Request(
                response.url,
                callback=self.handle_attachment,
                cookies={'_safe': safe_id.group(1)},
                dont_filter=True,
                meta=meta,
            )

        # A login/challenge response is HTML even when the original link was
        # named *.torrent.  Discuz torrent files are bencoded dictionaries;
        # this cheap check prevents those pages becoming false items.
        body = response.body.lstrip()
        content_type = response.headers.get('Content-Type', b'').lower()
        disposition = response.headers.get('Content-Disposition', b'').lower()
        looks_like_torrent = (
            body.startswith(b'd') and b'4:info' in body[:4096]
            and (b'torrent' in content_type or b'torrent' in disposition
                 or 'torrent' in response.url.lower())
        )
        if not looks_like_torrent:
            self.logger.info('Skipping non-public/non-torrent attachment: %s', response.url)
            return None

        return TorrentFileItem(
            url=response.url,
            from_url=response.request.headers.get('Referer', b'').decode(
                'utf-8', errors='replace'
            ),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
