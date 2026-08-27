# Hypotheses

Maintained side by side; none is privileged. Status reflects all evidence
gathered so far (2026-08-27). On-chain evidence is still entirely absent
(environment egress policy — see methodology), so no hypothesis has been
tested against the blockchain yet.

## H0 — Ordinary custodial wallet operation
Observed behavior is ordinary custodial wallet operation.
- **Status**: untested on-chain. Grade-C retrospectives describing a
  custodial lender wallet ("deposit BTC into your xCoins wallet") make a
  custodial architecture plausible in general.

## H1 — Coincidence
Candidate transactions are unrelated and merely resemble $50 xCoins deposits.
- **Status**: untested. Nothing yet rules it in or out. The two high-priority
  claims are ~$49.8 sends five weeks apart to different addresses; that alone
  is consistent with H1. Verbatim searches surfaced no external link between
  the addresses/txids and anything.

## H2 — xCoins deposits swept into shared custody
Candidate deposits belong to xCoins and were swept into shared custody.
- **Status**: untested. The key discriminator — whether the two exact UTXOs
  are swept into a common downstream wallet — requires the blocked on-chain
  trace. The custodial-model reviews support plausibility only; they
  attribute no address.

## H3 — Custody structure accumulated customer residual balances
- **Status**: untested and hard to test: internal ledger liabilities are not
  on-chain observables. At most, a persistent unspent custody-cluster balance
  after 2022-04-23 (shutdown) would be *consistent* with H3 without proving it.

## H4 — Apparent residuals are dust/fees/reserves/accounting artifacts
- **Status**: untested; the default explanation against which any residual
  finding must be weighed.

## H5 — Behavioral changes driven by external pressures
Changes over time result from PayPal fraud/chargebacks, regulatory changes,
BTC market conditions, or corporate restructuring.
- **Status**: partially supported externally. Contemporaneous 2017-era lender
  complaints document real chargeback pressure (grade D, multiple
  independent complainants plus first-party forum threads dedicated to
  chargeback support). The 2022-04-23 shutdown citing "developments beyond
  our control" (grade A via snippet) is consistent with external pressure.
  No on-chain regime change has been measured yet.

## Discriminating tests (pending network access)

1. Fetch three seed txs; confirm claimed outputs exist (falsifies/validates
   the wallet-record claims).
2. Spend of each exact seed outpoint: one-time address swept quickly into a
   many-input consolidation → supports H0/H2 over H1; direct spend by an
   obviously personal wallet pattern → supports H1.
3. Convergence of Jan and Feb paths within ≤6 hops on a common
   wallet/transaction → strong H2 signal (still unattributed).
4. April control converging on the same infrastructure → either broadens H2
   or reveals the "check" note meant something else; divergence keeps it a
   useful control.
5. Custody-cluster monthly activity 2016–2022: regime breaks at 2017
   (chargebacks), 2018 (corporate), 2021 (redesign), 2022-04 (shutdown) → H5
   support; none → H0.
