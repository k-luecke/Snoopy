# Crawl log

Append-only log of every network fetch attempt (success or failure) made by
`scripts/xcoinslib.py`, plus manual probes noted below. Successful fetches
record HTTP status and SHA-256 of the cached body; failures record the error.

Manual probes on 2026-08-27 (curl via session proxy, one attempt per host,
plus WebFetch): 17 blockchain-explorer hosts and the archival/forum hosts
listed in `evidence/sources.md` all denied with 403 at the egress proxy
CONNECT stage / `EGRESS_BLOCKED`. `info.xcoins.io` fails DNS resolution
(`ENOTFOUND`). Policy denials were reported, not retried or circumvented.

## Automated fetch attempts

- 2026-08-27T21:14:32Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://mempool.space/api/tx/008d70dbf29d1f009fee24d075b181ac34232c11e4834cae00c2d862f15ba2e1`
- 2026-08-27T21:14:33Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://blockstream.info/api/tx/008d70dbf29d1f009fee24d075b181ac34232c11e4834cae00c2d862f15ba2e1`
- 2026-08-27T21:14:34Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://mempool.space/api/tx/3f96f393166086a8f098226778e8bbd67ada8c022c08e7708c64fd07f62b663d`
- 2026-08-27T21:14:35Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://blockstream.info/api/tx/3f96f393166086a8f098226778e8bbd67ada8c022c08e7708c64fd07f62b663d`
- 2026-08-27T21:14:36Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://mempool.space/api/tx/dcb28ba5b2f5f657414a5e0c1ea1219711b038f8dab90de5c70d06bcf3fa00da`
- 2026-08-27T21:14:37Z FAIL URLError(OSError('Tunnel connection failed: 403 Forbidden')) `https://blockstream.info/api/tx/dcb28ba5b2f5f657414a5e0c1ea1219711b038f8dab90de5c70d06bcf3fa00da`
