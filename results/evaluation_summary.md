# Evaluation summary

48 documents, 192 planted canaries (one per format per document), seeded and deterministic.

## Stage x format survival (oracle ground truth)

| stage | api_key | email | account_id | free_text |
|---|---|---|---|---|
| planted | 100.0% | 100.0% | 100.0% | 100.0% |
| ingest | 100.0% | 100.0% | 100.0% | 100.0% |
| summarise | 100.0% | 81.2% | 100.0% | 100.0% |
| chunk | 100.0% | 81.2% | 100.0% | 100.0% |
| redact | 60.4% | 10.4% | 45.8% | 100.0% |
| translate | 35.4% | 10.4% | 20.8% | 100.0% |
| mail | 31.2% | 10.4% | 18.8% | 89.6% |

## Detector recovery vs ground truth (share of survivors found)

| stage | audit detector | verbatim grep |
|---|---|---|
| planted | 100.0% | 48.4% |
| ingest | 100.0% | 48.4% |
| summarise | 100.0% | 50.8% |
| chunk | 100.0% | 44.3% |
| redact | 100.0% | 12.5% |
| translate | 66.2% | 16.2% |
| mail | 66.7% | 0.0% |

## Redactor honesty

| format | entered redact | survived | kill rate | claimed | false-claim rate |
|---|---|---|---|---|---|
| api_key | 48 | 29 | 39.6% | yes | 60.4% |
| email | 39 | 5 | 87.2% | yes | 12.8% |
| account_id | 48 | 22 | 54.2% | yes | 45.8% |
| free_text | 48 | 48 | 0.0% | no | - |

Overall redactor false-claim rate (claimed formats): 41.5%

## Killing stage attribution

- ingest: 0
- summarise: 9
- chunk: 0
- redact: 79
- translate: 24
- mail: 8
- leaked: 72

Overall leak rate at the mail stage: 37.5%
