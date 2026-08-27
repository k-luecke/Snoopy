# Source log

All retrieval attempts and searches, with quality grades:

- **A** = first-party contemporaneous
- **B** = independent contemporaneous
- **C** = later reputable retrospective
- **D** = forum/user claim
- **E** = unknown/unverified

## Blockchain API attempts (all denied by environment egress policy, 2026-08-27)

Full per-URL log with timestamps: `reports/crawl-log.md` and
`raw/transactions/*.provenance.jsonl`. Hosts attempted (HTTP 403 at the
egress proxy CONNECT stage; also `EGRESS_BLOCKED` via the sanctioned
WebFetch tool): mempool.space, blockstream.info, esplora.blockstream.com,
blockchain.info, www.blockchain.com, api.blockchain.info, blockchair.com,
api.blockchair.com, btc.com, api.blockcypher.com, sochain.com, chain.so,
bitaps.com, blockonomics.co, blockexplorer.one, btcscan.org,
mempool.emzy.de. Also blocked: web.archive.org, archive.org,
bitcointalk.org, reddit.com, trustpilot.com, en.wikipedia.org.
Reachable but not useful for chain data: github.com,
raw.githubusercontent.com, googleapis.com (BigQuery public bitcoin dataset
requires GCP credentials not present here).

No CAPTCHA bypassing, authentication bypassing, or anti-bot evasion was
attempted; each blocked host was tried at most twice and the policy denial
was accepted.

## Web searches (WebSearch tool, server-side, 2026-08-27)

| # | Query | Outcome |
|---|-------|---------|
| Q1 | `"1ATE8wW11ULvcksZYDnWf74SH5SKdXbAwo"` | No page mentions the address (index noise only). Negative. |
| Q2 | `"1LC7zdvLpQD3DZdE2eZdRnj7nMgiYActTk"` | No page mentions the address. Negative. |
| Q3 | `"13kUu7RU9WF9UGQQoRM7QRbzTJaCFLfv6K"` | No page mentions the address. Negative. |
| Q4 | `mempool.space transaction 008d70db...a2e1` | No page references the txid. Negative. |
| Q5 | `"3f96f393...b663d" OR "dcb28ba5...00da"` | No page references either txid. Negative. |
| Q6 | `xcoins.io bitcoin deposit address wallet how it worked lender` | Grade-C retrospectives describing custodial lender-wallet flow: masterthecrypto.com/xcoins/, coincentral.com/xcoins-review/, btxchange.io/xcoins-review/, bitrates.com/exchange/xcoins/, yunorr1992.medium.com |
| Q7 | `xcoins.io P2P marketplace shutdown April 2022 residual balance withdraw` | Grade-A (snippet only): info.xcoins.io forum thread 9569 "Why xcoins shut down"; Grade-D: trustpilot.com/review/xcoins.io ("xCoins.io - closed") |
| Q8 | `"xcoins" shut down 2022 announcement "withdraw" funds statement` | Confirms 2022-04-23 discontinuation date, withdraw-first instruction; also info.xcoins.io thread 6616 "How do i withdraw" |
| Q9 | `xcoins.io complaints 2017 PayPal chargeback lender lost bitcoin` | Grade-D: steemit.com/fraudalert/@naltedtirt/xcoins-paypal-chargeback; info.xcoins.io lender-support threads 4019 ("Chargeback dispute not successful"), 7553 ("Two paypal disputes in the past two days"); bittrust.org/xcoinsio (206 reviews) |

## Direct fetch attempts of attribution sources

- `https://info.xcoins.io/forum/forum/borrower-questions/9569-why-xcoins-shut-down`
  — DNS `ENOTFOUND` (domain dead as of 2026-08-27). Content known only from
  search snippets; needs Wayback capture when reachable.
- `https://www.trustpilot.com/review/xcoins.io` — EGRESS_BLOCKED.

## Caveats

Search-snippet content is the search provider's summary of a page, not the
page itself; grade accordingly and re-capture verbatim text once archival
hosts are reachable.
