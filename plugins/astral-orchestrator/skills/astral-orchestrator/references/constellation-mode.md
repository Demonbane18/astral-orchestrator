# Constellation mode

Constellation is an explicit opt-in: use it only when the user explicitly names it. Constellation has one configured
Sol primary and one fresh Sol reviewer on its exact route. It is a constrained fan-out for independently
owned cards, not a request to fill every available slot or to replace Sol’s integration role.

## Prove that a concurrent first wave is safe

Before launching, Sol must write a complete card for every candidate and prove all of the
following:

- each ready card has an independent outcome and non-overlapping file and system ownership;
- no card needs another card’s output, interface decision, confirmation, or verification;
- every worker has an exact model and requested/configured effort route it can use;
- the host-advertised available slots are known; the primary consumes one slot;
- the configured model roster has enough suitable, cost-aware non-Sol workers.

Launch the first wave concurrently only after those facts are recorded. Its maximum worker
count is the minimum of ready independent cards, suitable configured roster entries, and
the host-advertised available slots minus the primary’s one slot. Do not hard-code four or
five simultaneous children. Do not spawn extra Sol implementers by default; reserve Sol
for the primary and fresh review, and prefer cost-aware non-Sol workers.

If independence, ownership, ready status, model availability, or capacity cannot be
proven, fall back to serial Guided-style routing. The fallback keeps the same work cards,
exact routes, verification, and review; it merely removes unsupported concurrency.

## Routing and integration

Use Luna or Terra for ordinary fixed-route cards. A card that explicitly needs a
user-selected routed model follows Morph mode and includes its exact model id and requested
effort. Start only the first safe wave; inspect completed cards, resolve interfaces in the
Sol primary, and then recalculate readiness and capacity before every later wave.

Tell every worker it is not alone in the codebase, owns only its card, must preserve other
edits, and must not spawn or delegate. Treat every report as a claim: inspect actual files,
run the declared checks, and integrate only after the evidence is sufficient.

## Portable-host route

On a non-Codex host, first read `portable-hosts.md`; do not run Codex preflight scripts or
claim fixed Luna/Terra routes. A concurrent first wave additionally requires observed model
selection, separate worker contexts, reported actual/requested effort, host-advertised
concurrency, and a separate fresh reviewer context. Record the actual provider/model/effort
for every worker and do not rename requested values as observed ones.

When independent cards and all non-concurrency capabilities are proven but the host cannot
provide concurrent capacity, an explicitly selected Constellation may use the documented
serial portable fallback. Keep the same cards, ownership, verification, and fresh reviewer;
label the result serial and never call it concurrent or Guided-style routing. If separate
worker or fresh reviewer context cannot be proven, stop.

## Review and risk

After integration and verification, start one new fresh exact Sol reviewer for the combined
change set. Careful safeguards override Constellation whenever risk requires user
confirmation, observed read-only reviewer isolation, or serial execution. A failed worker,
failed check, or uncertain shared interface stops the affected route rather than expanding
the Constellation.
