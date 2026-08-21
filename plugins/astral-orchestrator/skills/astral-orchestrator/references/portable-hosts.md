# Portable-host routes

Use this reference only after the core skill has established that the host is not Codex
and the user explicitly selected Morph or Constellation. The package format can make the
skill discoverable; it does not provide an orchestration runtime.

## Capability record

Before starting a portable worker, record the host name/version when exposed and observable evidence
for each required capability. Do not infer a capability from the host’s name or from a
plugin-install success.

| Capability | Required for |
| --- | --- |
| Select and report an actual provider/model | Morph and Constellation |
| Separate worker context | Morph and Constellation |
| Requested and actual effort reporting, when effort is offered | Morph and Constellation |
| New reviewer context distinct from primary and workers | Morph and Constellation |
| Available worker concurrency | Concurrent Constellation only |

For every route record: host, requested provider/model/effort, actual provider/model/effort,
whether each value is observed or merely requested, worker-context identity, reviewer-context
identity, and the checks run. Never relabel an unknown actual value as a configured value.

## Portable Morph

Require a bounded, non-overlapping worker card and an observed separate worker context.
Pass only that card through the host’s documented worker mechanism. A user-configured
external provider can receive that packet; say so plainly, never handle credentials, and
use no recursive delegation. After the worker returns, remove only that exact private
packet through the host’s safe narrow operation. If actual provider/model, requested
effort handling, or fresh reviewer context cannot be observed, stop and report the
missing capability.

## Portable Constellation

Start concurrent workers only when independent ownership, all worker contexts, host
capacity, and a fresh reviewer context are observed. Reserve and count the primary as one
occupied slot before calculating worker capacity, regardless of whether the host advertises
it. If concurrency is unavailable but the worker and reviewer requirements are proven, an
explicitly selected Constellation may run the same cards serially, clearly labeled **serial
portable fallback**. Do not call it Orbit, do not claim it was concurrent, and do not run
more workers merely to fill capacity.

## Fresh review

Integrate and verify actual changes before review. A reviewer is fresh only when the host
provides a context separate from the primary and every worker. If that cannot be observed,
do not substitute a primary self-review and do not claim independent review.
