# DMM DVD catalogue crawl

Updated: 2026-08-31. Strategy: `dmm-catalog-v2`.

## Discovery and identity

- Visit maker directories and their syllabary/pagination pages first. Maker lists cover works without actress metadata.
- Supplement with the date-sorted DVD catalogue and complete actress directories, including directory pagination.
- On a list, follow only its rendered immediate next page. Details have higher scheduler priority than list continuations. FIFO queues prevent one freshly discovered branch from continually taking precedence over siblings.
- Accept only canonical DVD detail URLs, single maker/label/actress partitions, the date-sorted catalogue, and directory URLs. Normalize trailing slashes and remove referral queries and page=1 aliases. Reject facet combinations, limit, price, view, RSS, searches and other services.
- Do not recursively follow recommended details. Discover missing makers from details; labels supplement explicitly capped maker partitions.
- Keep the DVD URL/CID as RawHtmlItem identity. HTML canonical tags may point at a different video service and must not replace it. Raw version, task and storage contract remain unchanged.

The observed total catalogue advertised 493,146 records but stopped at page 417 (50,040 positions). This is why a single global list is insufficient. Counts and availability change; queue exhaustion is not proof of complete site coverage.

## Persistence and recovery

Default JOBDIR is `jobdir/dmm-catalog-v2`; `DMM_JOBDIR` or Scrapy `-s JOBDIR=...` can select another directory. Use a new directory on first upgrade. Existing legacy/mixed queues are rejected, not deleted or silently migrated. Keep APP_TASK stable for the lifetime of a job.

- `dmm-strategy.json`: strategy/task guard.
- Native Scrapy queue, request fingerprints and spider state: graceful restart/resume.
- `dmm-coverage.json`: stored-item counter, partition totals/pages/references, incomplete/capped partitions and failures; written on close.
- `dmm-failures.jsonl`: failed requests, invalid pages or failed item storage. These require review/recovery; native JOBDIR fingerprints track scheduled requests, not successful storage. Hard kills and exhausted retries can leave gaps.

Only rendered pagination is traversed. A repeated page body, invalid range or missing detail structure is reported rather than expanding a bad branch.

## Runtime settings

Spider defaults: concurrency 8, minimum delay 0.25 s, AutoThrottle target concurrency 4, start delay 0.5 s, maximum delay 60 s, request timeout 30 s, retry count 3. Robots rules are enabled. Scrapy command-line `-s` overrides spider defaults; deployment configuration should match the effective settings rather than leave contradictory environment values.

No automatic full-job restart is enabled by this spider. Production restart policy and durable mount ownership belong to nas.ops.

## Validation before release

- 25 DMM regression tests plus 46 framework tests passed in EvaScrapy; one existing NATS coroutine warning remained.
- Real local crawl and restart saved 168 + 88 = 256 distinct HTML objects, with zero overlap, redirects or parse/storage failures; object identity/path checks passed.
- An instrumented list-only crawl traversed all 26 pages of maker 40039 and collected 3,021 unique detail URLs, equal to its displayed total, then finished naturally. This did not download all 3,021 details.
- These checks validate the strategy and graceful resume. Full-site completeness, long-run NAS memory and total duration still require production observation.
