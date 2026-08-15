# DMM 演员目录接口说明

本文记录 DMM AV 演员目录页的接口结构和分页规则。演员目录用于发现演员 ID；每发现一个演员，即可生成一个带 `actressIds` 筛选条件的影片列表任务。

## 1. 页面与接口

演员目录页面示例：

```text
https://video.dmm.co.jp/av/actress/?syllabary=a
```

GraphQL 接口：

```text
https://api.video.dmm.co.jp/graphql
```

GraphQL operation：

```text
ActressesSyllabary
```

核心查询字段：

```graphql
actresses(
  floor: $floor
  sort: $sort
  syllabary: $syllabary
  classification: $classification
  limit: $limit
  offset: $offset
)
```

## 2. 请求参数

| 参数 | 当前值 | 说明 |
| --- | --- | --- |
| `floor` | `AV` | 查询 AV 楼层演员 |
| `sort` | `NAME_ASC` | 按演员名称升序 |
| `syllabary` | 例如 `A` | 五十音分组；GraphQL 类型为 `[Syllabary!]` |
| `classification` | `AV` | 演员分类 |
| `limit` | `100` | 单页演员数量 |
| `offset` | `0` | 分页偏移量 |
| `hasThumbnailImageUrl` | `false` | 是否返回缩略图字段 |
| `shouldGetBookmark` | `false` | 是否返回登录用户收藏状态 |

爬虫只需要演员 ID 时，建议关闭图片和收藏字段：

```json
{
  "hasThumbnailImageUrl": false,
  "shouldGetBookmark": false
}
```

不要将登录会话、追踪 Cookie 或 token 写入代码、日志和文档。

## 3. GraphQL 查询结构

精简后的查询可以只保留演员发现所需字段：

```graphql
query ActressesSyllabary(
  $floor: Floor!
  $sort: ActressesSort!
  $syllabary: [Syllabary!]
  $classification: ActressClassification = AV
  $limit: Int = 100
  $offset: Int = 0
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
```

变量示例：

```json
{
  "floor": "AV",
  "sort": "NAME_ASC",
  "syllabary": ["A"],
  "classification": "AV",
  "limit": 100,
  "offset": 0
}
```

原始页面请求中 `syllabary` 传递的是单个字符串，例如：

```json
"syllabary": "A"
```

由于 GraphQL 类型声明为列表，代码中建议使用单元素数组：

```json
"syllabary": ["A"]
```

## 4. 五十音参数

演员页面 HTML 的导航链接确认了 47 个参数。页面 URL 使用小写值，GraphQL 枚举使用大写值。

```text
a, i, u, e, o
ka, ki, ku, ke, ko
sa, shi, su, se, so
ta, chi, tsu, te, to
na, ni, nu, ne, no
ha, hi, fu, he, ho
ma, mi, mu, me, mo
ya, yu, yo
ra, ri, ru, re, ro
wa, wo, n
```

对应 GraphQL 枚举：

```text
A, I, U, E, O
KA, KI, KU, KE, KO
SA, SHI, SU, SE, SO
TA, CHI, TSU, TE, TO
NA, NI, NU, NE, NO
HA, HI, FU, HE, HO
MA, MI, MU, ME, MO
YA, YU, YO
RA, RI, RU, RE, RO
WA, WO, N
```

需要保留以下特殊罗马字拼写：

```text
shi → SHI
chi → CHI
tsu → TSU
fu → FU
```

实现时可以从演员目录导航的 `href` 提取小写参数，再转换为大写枚举；不要根据普通五十音规则重新推导参数。

## 5. 返回数据

### 5.1 演员字段

| 字段 | 作用 | 是否为发现影片所必需 |
| --- | --- | --- |
| `id` | 演员 ID，用于 `actressIds` 筛选 | 是 |
| `name` | 演员名称 | 否，用于日志和排障 |
| `nameRuby` | 演员读音 | 否，用于日志和排障 |
| `imageUrl` | 演员图片 | 否 |
| `thumbnailImageUrl` | 演员缩略图 | 否 |
| `contentsCount` | 该演员关联内容数量 | 否，可用于规模评估 |
| `isFavorite` | 当前用户是否收藏 | 否，依赖登录态 |

### 5.2 分页字段

```json
{
  "pageInfo": {
    "offset": 0,
    "limit": 100,
    "hasNext": true,
    "totalCount": 1234
  }
}
```

演员目录分页应优先使用 `hasNext`，并保留以下安全条件：

```text
当前页有演员
且 hasNext=true
且下一页 offset 大于当前 offset
```

下一页 offset 建议使用实际返回数量计算：

```text
next_offset = offset + len(items)
```

不要把演员目录的 offset 与某个演员的影片列表 offset 混用。

## 6. 演员到影片列表

每取得一个演员，就生成一个独立的影片列表查询：

```json
{
  "filter": {
    "actressIds": {
      "ids": [{"id": "1044099"}],
      "op": "AND"
    }
  }
}
```

影片列表任务应保留自己的分页状态：

```text
actress_id=1044099, offset=0
actress_id=1044099, offset=120
actress_id=1044099, offset=240
...
```

整体抓取流程：

```text
47 个 syllabary
  → 演员目录分页
    → 演员 ID 去重
      → 每个演员生成 actressIds 列表任务
        → 演员影片列表分页到底
          → 内容 ID 去重
            → 详情请求
```

同一影片可能属于多个演员，因此不能直接累加不同演员的 `contentsCount`；详情请求必须按内容 ID 去重。

