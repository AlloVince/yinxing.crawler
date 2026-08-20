# -*- coding: utf-8 -*-
import math
import time

from scrapy.http import JsonRequest, Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import RawJsonItem


class FanzaSpider(BaseSpider):
    version = '2.2.0'
    name = 'fanza'
    allowed_domains = ['video.dmm.co.jp', 'api.video.dmm.co.jp']
    start_urls = ['https://video.dmm.co.jp/av/list/']
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules

    search_api_url = 'https://api.video.dmm.co.jp/graphql'
    search_page_size = 120
    regular_search_sort = 'DELIVERY_START_DATE'
    deep_search_sort = 'SALES_RANK_SCORE'
    regular_search_max_pages = 10
    actress_page_size = 100
    actress_syllabaries = (
        'A', 'I', 'U', 'E', 'O',
        'KA', 'KI', 'KU', 'KE', 'KO',
        'SA', 'SHI', 'SU', 'SE', 'SO',
        'TA', 'CHI', 'TSU', 'TE', 'TO',
        'NA', 'NI', 'NU', 'NE', 'NO',
        'HA', 'HI', 'FU', 'HE', 'HO',
        'MA', 'MI', 'MU', 'ME', 'MO',
        'YA', 'YU', 'YO',
        'RA', 'RI', 'RU', 'RE', 'RO',
        'WA', 'WO', 'N',
    )
    # actress_syllabaries = ()
    genres = (
        '2001', '1014', '1034', '1039', '1018', '5001', '5005', '4015', '6793', '79015',
        '4118', '514', '6968', '2011', '5048', '4008', '6965', '5075', '5076', '309021',
        '4073', '4057', '4122', '72', '6014', '6170', '5068', '5025', '1004', '6063',
        '5012', '4030', '1040', '6942', '307966', '4075', '4001', '4119', '5074', '6967',
        '1001', '1032', '1003', '1083', '6934', '527', '6954', '6948', '6938', '5008',
        '1033', '6947', '6943', '528', '6969', '5017', '4140', '1016', '6945', '1082',
        '2022', '4026', '553', '3011', '1021', '4123', '1022', '5010', '1013', '5023',
        '5014', '5067', '4007', '4106', '4059', '567', '524', '5', '4120', '1036',
        '1005', '3009', '4017', '2024', '4009', '6017', '4002', '97', '5069', '5007',
        '1075', '4033', '38', '4060', '6597', '6151', '4138', '25', '5059', '2003',
        '1028', '1071', '4031', '5009', '6574', '1041', '6069', '21', '5022', '5016',
        '5070', '5020', '5021', '28', '6609', '5063', '1015', '6944', '1026', '62',
        '5024', '1017', '1019', '55', '35', '3036', '4058', '6608', '4011', '4024',
        '6966', '4018', '1007', '6940', '4096', '6671', '617', '2006', '6970', '95',
        '48', '3003', '4098', '7267', '6955', '5072', '3029', '1030', '6007', '4010',
        '568', '6086', '3001', '308409', '5013', '4105', '4025', '6959', '1031', '3005',
        '4116', '2002', '6149', '2019', '6941', '6956', '5073', '5004', '6004', '6006',
        '5066', '6005', '4021', '4014', '42', '4023', '4034', '6548', '5015', '4114',
        '6935', '4006', '94', '1029', '64', '4111', '6964', '6972', '6957', '5071',
        '6925', '5019', '4019', '6533', '5006', '6070', '2012', '1012', '27', '93',
        '307935', '6958', '6949', '6950', '6974', '3033', '6002', '96', '3006', '4016',
        '6939', '1023', '1027', '6164', '102', '2023', '6963', '2005', '4139', '6566',
        '17', '4110', '88', '5002', '6961', '6946', '81', '300129', '6951', '59',
        '5003', '6555', '1069', '6003', '6937', '1085', '6952', '5011', '558', '2007',
        '3013', '6962', '5060', '18', '6108', '3015', '4124', '1086', '6960', '63',
        '3008', '2008', '3007', '3012', '1025', '6973', '6971', '1008', '2004', '6936',
        '4028', '1009', '4020', '5053', '4022', '6933', '6012', '569', '4005', '3014',
        '6975', '3032', '1011', '3035', '5062', '4013', '555', '6953', '5057', '5018',
        '1020', '3002',
    )
    actress_query = '''
        query ActressesSyllabary(
          $floor: Floor!
          $sort: ActressesSort!
          $syllabary: [Syllabary!]
          $classification: ActressClassification = AV
          $limit: Int!
          $offset: Int!
        ) {
          actresses(
            floor: $floor
            sort: $sort
            syllabary: $syllabary
            classification: $classification
            limit: $limit
            offset: $offset
          ) {
            items {
              id
              name
              nameRuby
              contentsCount
            }
            pageInfo {
              offset
              limit
              hasNext
              totalCount
            }
          }
        }
    '''
    search_query = '''
        query AvContentIds(
          $limit: Int!
          $offset: Int!
          $sort: ContentSearchPPVSort!
          $filter: ContentSearchPPVFilterInput
        ) {
          legacySearchPPV(
            limit: $limit
            offset: $offset
            floor: AV
            sort: $sort
            filter: $filter
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
        query ContentWithReviews($id: ID!, $sort: ReviewSort!, $i2iRecommendId: ID!) {
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
            recommendedContents(limit: 40, recommendId: $i2iRecommendId) {
              id
              trackingId
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
    i2i_recommend_id = '81b5e821'

    async def start(self):
        if self.settings.getbool('APP_RUN_DEEP'):
            for syllabary in self.actress_syllabaries:
                yield self._build_actress_request(syllabary=syllabary, offset=0)
            for genre_id in self.genres:
                yield self._build_search_request(offset=0, genre_id=genre_id)
            return

        yield self._build_search_request(offset=0, page=0)

    def _build_actress_request(self, syllabary: str, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'operationName': 'ActressesSyllabary',
                'query': self.actress_query,
                'variables': {
                    'floor': 'AV',
                    'sort': 'NAME_ASC',
                    'syllabary': [syllabary],
                    'classification': 'AV',
                    'limit': self.actress_page_size,
                    'offset': offset,
                },
            },
            callback=self.parse_actress_results,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': 'https://video.dmm.co.jp/av/actress/',
            },
            meta={
                'syllabary': syllabary,
                'offset': offset,
                'log_context': f'FANZA actress syllabary={syllabary} offset={offset}',
            },
        )

    def parse_actress_results(self, response: Response):
        payload = response.json()
        if payload.get('errors'):
            raise RuntimeError('DMM actress GraphQL errors: %s' % payload['errors'])

        result = (payload.get('data') or {}).get('actresses') or {}
        actresses = result.get('items') or []
        current_offset = response.meta['offset']

        for actress in actresses:
            actress_id = actress.get('id')
            if actress_id:
                yield self._build_search_request(offset=0, actress_id=actress_id)

        page_info = result.get('pageInfo') or {}
        next_offset = current_offset + len(actresses)
        self.logger.info(
            'FANZA actress_page syllabary=%s offset=%s returned=%s total=%s next=%s',
            response.meta['syllabary'],
            current_offset,
            len(actresses),
            page_info.get('totalCount'),
            bool(page_info.get('hasNext')),
        )
        if (
            actresses
            and page_info.get('hasNext')
            and next_offset > current_offset
        ):
            yield self._build_actress_request(
                syllabary=response.meta['syllabary'],
                offset=next_offset,
            )

    def _build_search_request(
        self,
        offset: int,
        actress_id: str = None,
        genre_id: str = None,
        page: int = 0,
    ) -> JsonRequest:
        search_filter = None
        search_sort = self.regular_search_sort
        log_context = f'FANZA latest_list page={page} offset={offset}'
        if actress_id:
            search_filter = {
                'actressIds': {
                    'ids': [{'id': actress_id}],
                    'op': 'AND',
                },
            }
            search_sort = self.deep_search_sort
            log_context = f'FANZA content_list actress_id={actress_id} offset={offset}'
        elif genre_id:
            search_filter = {
                'genreIds': {
                    'ids': [{'id': genre_id}],
                    'op': 'AND',
                },
            }
            search_sort = self.deep_search_sort
            log_context = f'FANZA content_list genre_id={genre_id} offset={offset}'

        return JsonRequest(
            url=self.search_api_url,
            data={
                'operationName': 'AvContentIds',
                'query': self.search_query,
                'variables': {
                    'limit': self.search_page_size,
                    'offset': offset,
                    'sort': search_sort,
                    'filter': search_filter,
                },
            },
            callback=self.parse_search_results,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': 'https://video.dmm.co.jp/av/actress/',
            },
            meta={
                'actress_id': actress_id,
                'genre_id': genre_id,
                'offset': offset,
                'mode': 'deep' if (actress_id or genre_id) else 'regular',
                'page': page,
                'log_context': log_context,
            },
        )

    def parse_search_results(self, response: Response):
        payload = response.json()
        if payload.get('errors'):
            raise RuntimeError('DMM search GraphQL errors: %s' % payload['errors'])

        result = payload['data']['legacySearchPPV']['result']
        contents = result.get('contents') or []

        for content in contents:
            yield self._build_detail_request(content['id'])

        current_offset = response.meta['offset']
        next_offset = current_offset + len(contents)
        total_count = result['pageInfo']['totalCount']
        if response.meta['mode'] == 'regular':
            next_page = response.meta['page'] + 1
            has_next = bool(
                contents
                and next_page < self.regular_search_max_pages
                and next_offset < total_count
            )
            self.logger.info(
                'FANZA latest_page page=%s offset=%s returned=%s total=%s next=%s',
                response.meta['page'],
                current_offset,
                len(contents),
                total_count,
                has_next,
            )
            if has_next and next_offset > current_offset:
                yield self._build_search_request(offset=next_offset, page=next_page)
            return

        has_next = bool(contents and next_offset < total_count)
        if response.meta['genre_id']:
            shard = f'genre_id={response.meta["genre_id"]}'
        else:
            shard = f'actress_id={response.meta["actress_id"]}'
        self.logger.info(
            'FANZA content_page %s offset=%s returned=%s total=%s next=%s',
            shard,
            current_offset,
            len(contents),
            total_count,
            has_next,
        )
        if has_next and next_offset > current_offset:
            yield self._build_search_request(
                offset=next_offset,
                actress_id=response.meta['actress_id'],
                genre_id=response.meta['genre_id'],
            )

    def _build_detail_request(self, content_id: str) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'operationName': 'ContentWithReviews',
                'query': self.detail_query,
                'variables': {
                    'id': content_id,
                    'sort': self.review_sort,
                    'i2iRecommendId': self.i2i_recommend_id,
                },
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
                'log_context': f'FANZA detail content_id={content_id}',
            },
        )

    def parse_detail(self, response: Response):
        payload = response.json()
        if payload.get('errors'):
            raise RuntimeError('DMM detail GraphQL errors: %s' % payload['errors'])

        data = payload.get('data') or {}
        ppv_content = data.get('ppvContent')
        if not ppv_content:
            raise RuntimeError('DMM detail GraphQL returned no content: %s' % response.meta['content_id'])

        yield RawJsonItem(
            url=response.meta['detail_url'],
            version=self.version,
            task=self.settings.get('APP_TASK'),
            timestamp=math.floor(time.time()),
            content=payload,
        )
