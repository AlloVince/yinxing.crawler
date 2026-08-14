# -*- coding: utf-8 -*-
import math
import time

from scrapy.http import JsonRequest, Request, Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import RawJsonItem


class DmmSpider(BaseSpider):
    version = '2.0.0'
    name = 'dmm'
    allowed_domains = ['video.dmm.co.jp', 'api.video.dmm.co.jp']
    start_urls = ['https://video.dmm.co.jp/av/list/']
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules

    search_api_url = 'https://api.video.dmm.co.jp/graphql'
    search_page_size = 120
    search_query = '''
        query AvContentIds($limit: Int!, $offset: Int!) {
          legacySearchPPV(
            limit: $limit
            offset: $offset
            floor: AV
            sort: SALES_RANK_SCORE
            facetLimit: 1
            includeExplicit: true
            excludeUndelivered: true
          ) {
            result {
              contents { id }
              pageInfo { totalCount }
            }
          }
        }
    '''
    detail_query = '''
        query ContentWithReviews($id: ID!, $sort: ReviewSort!) {
          ppvContent(id: $id) {
            id
            floor
            title
            notices
            isNoIndex
            isAllowForeign
            description
            contentType
            releaseStatus
            isExclusiveDelivery
            wishlistCount
            duration
            makerReleasedAt
            announcements {
              body
              __typename
            }
            featureArticles {
              link {
                url
                text
                __typename
              }
              __typename
            }
            saleStartDate
            saleEndDate
            deliveryStartDate
            packageImage {
              mediumUrl
              largeUrl
              __typename
            }
            sampleImages {
              number
              imageUrl
              largeImageUrl
              __typename
            }
            mostPopularContentImage {
              ... on ContentSampleImage {
                largeImageUrl
                imageUrl
                __typename
              }
              ... on PackageImage {
                largeUrl
                mediumUrl
                __typename
              }
              __typename
            }
            sample2DMovie {
              highestMovieUrl
              hlsMovieUrl
              __typename
            }
            sampleVRMovie {
              highestMovieUrl
              __typename
            }
            weeklyRanking: ranking(term: Weekly)
            monthlyRanking: ranking(term: Monthly)
            pricing {
              lowestRegularPriceInclusiveTax
              lowestEffectivePriceInclusiveTax
              hasMultiplePrices
              sale {
                name
                id
                endAt
                discountRate
                __typename
              }
              pointRewardCampaign {
                name
                id
                endAt
                promotionId
                rate
                __typename
              }
              __typename
            }
            products {
              id
              priority
              deliveryUnit {
                id
                priority
                streamMaxQualityGroup
                downloadMaxQualityGroup
                __typename
              }
              pricing {
                regularPriceInclusiveTax
                effectivePriceInclusiveTax
                __typename
              }
              expireDays
              licenseType
              shopName
              __typename
            }
            actresses {
              id
              name
              nameRuby
              imageUrl
              bustTop
              bust
              waist
              hip
              height
              ppvSummary(floor: AV) {
                contentCount
                __typename
              }
              __typename
            }
            histrions {
              id
              name
              __typename
            }
            genres {
              id
              name
              __typename
            }
            maker {
              id
              name
              __typename
            }
            series {
              id
              name
              __typename
            }
            label {
              id
              name
              __typename
            }
            directors {
              id
              name
              __typename
            }
            makerContentId
            relatedTags(limit: 99) {
              ... on ContentTagGroup {
                tags {
                  id
                  name
                  __typename
                }
                __typename
              }
              ... on ContentTag {
                id
                name
                __typename
              }
              __typename
            }
          }
          reviewSummary(contentId: $id) {
            average
            total
            withCommentTotal
            distributions {
              total
              withCommentTotal
              rating
              __typename
            }
            __typename
          }
          reviews(contentId: $id, sort: $sort, limit: 10, offset: 0) {
            items {
              id
              title
              rating
              reviewerId
              nickname
              isPurchased
              comment
              helpfulCount
              service
              isExposure
              publishDate
              __typename
            }
          }
        }
    '''
    review_sort = 'HELPFUL_COUNT_DESC'

    async def start(self):
        for url in self.start_urls:
            yield Request(url, cookies={'age_check_done': '1'})

    def parse_start_url(self, response: Response):
        yield self._build_search_request(offset=0)

    def _build_search_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'query': self.search_query,
                'variables': {'limit': self.search_page_size, 'offset': offset},
            },
            callback=self.parse_search_results,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': self.start_urls[0],
            },
            meta={'offset': offset},
        )

    def parse_search_results(self, response: Response):
        result = response.json()['data']['legacySearchPPV']['result']
        contents = result['contents']

        for content in contents:
            yield self._build_detail_request(content['id'])

        next_offset = response.meta['offset'] + len(contents)
        if contents and next_offset < result['pageInfo']['totalCount']:
            yield self._build_search_request(offset=next_offset)

    def _build_detail_request(self, content_id: str) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'operationName': 'ContentWithReviews',
                'query': self.detail_query,
                'variables': {'id': content_id, 'sort': self.review_sort},
            },
            callback=self.parse_detail,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': self.start_urls[0],
            },
            meta={
                'content_id': content_id,
                'detail_url': f'https://video.dmm.co.jp/av/content/?id={content_id}',
            },
        )

    def parse_detail(self, response: Response) -> RawJsonItem:
        payload = response.json()
        if payload.get('errors'):
            raise RuntimeError('DMM detail GraphQL errors: %s' % payload['errors'])

        data = payload.get('data') or {}
        if not data.get('ppvContent'):
            raise RuntimeError('DMM detail GraphQL returned no content: %s' % response.meta['content_id'])

        return RawJsonItem(
            url=response.meta['detail_url'],
            version=self.version,
            task=self.settings.get('APP_TASK'),
            timestamp=math.floor(time.time()),
            content=payload,
        )
