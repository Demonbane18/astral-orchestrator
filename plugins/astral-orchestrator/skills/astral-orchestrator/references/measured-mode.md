# Measured mode

Measured is an explicit opt-in route for a user who wants a deliberately slower,
evidence-oriented execution record. Never auto-select Measured: recommend Guided for
normal work. It adds no Ori, OpenRouter, API, network service, secret, analytics, or
dynamic model selection. It uses the existing pinned `gpt-5.6-sol`, `gpt-5.6-luna`, and
`gpt-5.6-terra` lanes at their configured efforts.

Sol retains requirements, architecture, safety decisions, decomposition, integration,
and final routing. Measured does not make a worker an independent owner of those choices.

## One executable state sequence

Measured has one unpersisted **Prepare** step followed by this persisted grammar:
`freeze`, `preflight`, `route`, then one or more numbered execution attempts, each in
the order `implementation`, `verification`, `review`, followed by `complete`. The route
phase includes any permitted planning probes. Freeze, preflight, and route occur once;
an execution attempt repeats only after a `fix-first` verdict.

1. **Prepare (unpersisted).** Sol constructs and canonicalizes the one work card in
   memory, derives its repository/card run path, validates every existing state path, and
   asks the single resume/archive question before any writes. A matching run asks exactly:
   “Resume this Measured run or archive it and start a new one?” End the turn for that
   answer. Resume continues from the first unfinished base phase or the current
   attempt's first unfinished phase.
   Before recording `freeze started`, Prepare creates or validates the private state.
2. **Freeze.** Only after Prepare creates or validates private state, record `freeze
   started`, write the canonical card, then record `freeze finished`.
3. **Preflight.** Run the normal Guided/Careful route preflight and record observed route
   evidence.
4. **Route.** Sol applies the deterministic rules below; a planning probe is allowed only
   for genuine Luna/Terra ambiguity.
5. **Attempt N — Implementation.** Start with attempt `1`. Only the one selected
   implementation lane edits the frozen card's bounded items.
6. **Attempt N — Verification.** Run the frozen checks and record their observed results.
7. **Attempt N — Review.** Obtain a fresh normal Sol reviewer. On `ship`, continue to
   Complete. On `fix-first`, finish the current Review occurrence, increment the attempt
   number, and start the new attempt at Implementation; it requires fresh verification
   and a new reviewer. `rethink` does not mutate the frozen card: finish the Review
   occurrence, stop, and ask to archive this run and start a new frozen card.
8. **Complete.** Complete is allowed only after a `ship` verdict. Record that verdict and
   its observed evidence. Never reconstruct an event from memory.

Before and after every persisted phase occurrence, atomically update `phase-state.txt`
with an ordered event number, the attempt number (`0` for Freeze, Preflight, and Route),
the phase, and `started` or `finished`; append the matching numbered non-secret event to
`ledger.txt`. Complete uses the final successful attempt number. The state sequence never
has a separately persisted “open” or “probe” phase. Ask at most one blocking question in
a turn.

## Private, reproducible local state

Measured state is private, local, non-secret, and resumable. Do not record credentials,
tokens, raw prompts, diffs, private raw tool output, or personal or regulated data.

Derive the run key in this order:

1. Resolve the workspace root with `realpath`. Encode that absolute path as UTF-8 without
   a BOM, calculate SHA-256, and take the first 16 lowercase hexadecimal characters. This
   is the **repository-root SHA-256 prefix**.
2. Serialize the frozen card using the canonical UTF-8 LF serialization below. Calculate
   SHA-256 of the exact bytes and take the first 16 lowercase hexadecimal characters.
   This is the independent **frozen-card SHA-256 prefix**.
3. Obtain the numeric effective local UID by running `id -u`. Reject an empty or
   non-decimal result; use its decimal digits without a username fallback.
4. Resolve the fixed `/tmp` alias once with `realpath`; require its **canonical temp root**
   to be an existing directory. Use the logical path
   `/tmp/astral-orchestrator-measured-<effective-uid>/<repository-prefix>-<card-prefix>`
   and perform the operations below relative to the canonical temp root.

The independent prefixes prevent identical cards in different repositories from
colliding. Below the canonical temp root, first create or validate the owner-only parent
directory `astral-orchestrator-measured-<effective-uid>` with `0700` permissions. Every
path component below the canonical temp root must be checked with `lstat`-style or
no-follow operations: reject symlink parents, a symlink run directory, and any symlink
tracker file. Reject an existing path not owned by the effective UID or with group or
other access bits. Do not repair insecure state by following or replacing it.

Create the run directory with `0700` permissions. Create `card.txt`, `phase-state.txt`,
and `ledger.txt` with `0600` permissions using owner-only atomic creation that does not
follow links (for example, no-follow exclusive create). For an update, write a new
owner-only temporary sibling, fsync when available, revalidate the destination with
`lstat`, and atomically replace it without following a link. If the platform cannot make
those no-follow checks, stop and report the state path as unsafe.

`card.txt` is the source of truth. It contains exactly one compact JSON object followed by
one LF. Its schema version is `1` and keys appear in this fixed order:

```text
schema_version, outcome, done_when, boundaries, checks
```

Use only those keys. `done_when`, `boundaries`, and `checks` are arrays in Sol-frozen
order. Strings are Unicode NFC; convert CRLF and CR to LF; do not trim or add whitespace.
Encode as UTF-8 without a BOM, set `ensure_ascii` to false, use `,` and `:` separators
with no spaces, and append one LF. This canonical UTF-8 LF serialization is the only
input to the frozen-card hash.

`phase-state.txt` is the current ordered tracker; `ledger.txt` is append-only evidence.
They are concrete tracker files, not recollection. Archiving moves a matching run to a
dated sibling directory only after the user chooses archive; it never deletes the
repository or records.

## Candidate planning probes

When only Luna/Terra selection is ambiguous, Sol requests exactly one Luna probe and one
Terra probe. Both probes receive the identical frozen card and acceptance checks. A probe
is behaviorally read-only: it must not edit, format, create, delete, or run a
state-changing command. That instruction is not hard sandbox isolation. Probes cannot
change the card, requirements, architecture, safety boundaries, acceptance checks, files,
or systems. They do not implement, and Sol still chooses the route.

### Measured planning probe

```text
ROLE
<astral_orchestrator_luna_implementer or astral_orchestrator_terra_implementer>
Provide a planning probe for Measured routing only. Remain behaviorally read-only: do not
edit, format, create, delete, or run a state-changing command. This instruction is not
hard sandbox isolation. Do not spawn or delegate.

FROZEN WORK CARD
<The identical non-secret frozen work card and named acceptance checks for both probes.>

REPORT ONLY
- Fully specified: yes/no, with decisive fact
- Narrow and repeatable/mechanical: yes/no, with decisive fact
- Exact checks: yes/no, with decisive fact
- Flags: debugging, integration, cross-component, context-heavy, moderate ambiguity
- Recommended lane: Luna or Terra, with decisive facts

BOUNDARIES
- Do not change the work card, requirements, architecture, safety boundaries, acceptance
  checks, files, or systems.
- Sol retains the final route decision.
```

## Deterministic lane selection

Keep the work with Sol while requirements, architecture, safety boundaries, public
interfaces, decomposition, or acceptance conditions are unsettled. After Sol settles
them, choose Luna only when every condition is true:

- the card is fully specified;
- the change is narrow, repeatable or mechanical, and has exact checks; and
- no debugging, integration, cross-component, context-heavy, or moderate-ambiguity flag
  is present.

Choose Terra when any listed flag is present. If probes materially disagree, Sol records
the decisive facts and defaults to Terra. Never route by prestige, popularity, or a
silent fallback. Requested and observed role, model, effort, and task or session identity
must be recorded as facts; unknown values remain unknown.

## Measured ledger entry

```text
PHASE
<freeze | preflight | route | implementation | verification | review | complete>

ATTEMPT
<0 for freeze/preflight/route | positive execution attempt number>

ROUTE EVIDENCE
- Requested role/model/effort: <observed or unknown>
- Observed role/model/effort/task-or-session-id: <facts only>

OUTCOME EVIDENCE
- Chosen lane and reasons: <facts only>
- Checks and observed results: <facts only>
- Model-call count: <observed count or unknown>
- Wall time: <observed duration or unknown>
- First-pass acceptance or rework: <observed state>
- Final reviewer verdict: <ship | fix-first | rethink | unknown>

Never invent a missing measurement. Store only non-secret values in the Measured private
run directory; later transcribe compatible observed values into the existing benchmark
scorecard JSONL schema.
```

## Implementation and review

Only the selected implementation lane edits. The other candidate lane does not receive
implementation ownership. The normal fresh Sol reviewer reviews every worker-produced
Measured change. High-risk Measured work inherits Careful confirmation gates and observed
read-only isolation requirements.
