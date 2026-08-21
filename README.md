![Animated outer-space Astral Orchestrator banner with Sol at the center, Luna and Terra orbiting, twinkling stars, and a passing comet.](assets/brand/astral-orchestrator-banner.gif)

# Astral Orchestrator

Astral Orchestrator v3.6.0 is an installable, open-source Codex plugin. Its delegated
routes keep Sol responsible for the plan and final decisions, use Luna for focused work
or Terra for context-heavy implementation, then use a fresh Sol reviewer to check the
finished change. Singularity is the deliberate one-Sol exception for eligible work.

Install it now from this public GitHub marketplace source. The official ChatGPT/Codex
directory is a separate publication surface and may lag until the v3.6.0 directory upload
is published. Astral Orchestrator is an independent open-source project, not affiliated
with or endorsed by OpenAI.

## Quick Install

From a terminal where Codex is available, run these two commands:

~~~sh
codex plugin marketplace add Demonbane18/astral-orchestrator --ref main
codex plugin add astral-orchestrator@astral-orchestrator
~~~

This is the complete install. On current Codex MultiAgentsV2 hosts, Orbit, Event Horizon, and
Pulsar use native child agents with `agent_type`, a unique `task_name`, `model`,
`reasoning_effort`, and `fork_turns` stated explicitly for each child. Optional native
profiles are not required. The bundled process launcher is a legacy compatibility fallback
only for hosts that do not expose `agent_type`, `task_name`, `model`, `reasoning_effort`,
and `fork_turns`.
Singularity, Morph, and Constellation are separate explicit opt-ins. Singularity keeps
meaningful low- or medium-risk work in one verified Sol primary session with no subagents
or fresh reviewer; Morph and Constellation do not change the verified Sol primary or
fresh Sol reviewer.

## What Astral Orchestrator does

For Orbit, Event Horizon, Pulsar, Morph, and Constellation work, Astral Orchestrator gives
you a repeatable way to:

1. have Sol turn your request into a clear outcome and work plan;
2. send narrow, repeatable work to Luna and context-heavy implementation to Terra;
3. inspect the actual changes and run relevant checks;
4. request a fresh Sol review before handoff.

Comet and Singularity instead keep their eligible work in the verified Sol primary and
use a plainly labeled self-review; Event Horizon takes over when the risk requires it.

All modes run the bundled primary checker before execution. If local runtime evidence is
unavailable, non-Singularity modes may use one-time user confirmation and label it as
user-confirmed rather than observed. Singularity requires observed/verified Sol model and
effort, must stop on unavailable evidence, and user confirmation cannot satisfy or
override that requirement. A mismatch or invalid result blocks every route.

It works for code, documents, configuration, research artifacts, and other
workspace-based projects. It adds no API key, paid service, background server, analytics,
or third-party Python package. The only local runtime requirement beyond Codex is Python
3.11 or newer.

## Requirements

- Codex with access to gpt-5.6-sol, gpt-5.6-luna, and gpt-5.6-terra.
- Python 3.11 or newer; the included tools use only the Python standard library.
- A new Codex task after installation, so Codex can discover the plugin. It also discovers
  optional native profiles when you choose the setup below.

The optional setup installs profiles; it cannot grant access to models your Codex account
does not have. Astral Orchestrator stops instead of quietly choosing a different model or
effort.

## Installation

### GitHub marketplace install (recommended)

The two Quick Install commands add this GitHub repository at its `main` ref, then install
the `astral-orchestrator` plugin. They are enough for native MultiAgentsV2 routing and
the bundled legacy exact-process fallback.

### Optional fixed-role profile setup

For faster, more ergonomic native named-agent selection, download the public repository
as a ZIP or clone it, open a terminal in its root, and run:

~~~sh
git clone https://github.com/Demonbane18/astral-orchestrator.git
cd astral-orchestrator
sh scripts/setup.sh --dry-run
sh scripts/setup.sh
~~~

The dry run prints the planned local changes. Setup registers the checkout, adds the
plugin, and installs three companion profiles without overwriting a different file. It is
an optional enhancement, not a prerequisite: current MultiAgentsV2 hosts use the built-in
native worker with explicit model and effort for Luna or Terra, or the built-in native
default for a reviewer, when a profile is absent or customized.

## First use

Start a new Codex task with gpt-5.6-sol at your configured orchestrator effort (High by
default), then say:

~~~text
Use Astral Orchestrator to add a search box and verify every lane.
~~~

You can also ask it to fix an error or complete a documentation change. Orbit mode is
the default, so you only need to name a mode when you want a different level of process.

For an evidence-oriented run, say “Use Astral Orchestrator in Pulsar mode.”
For disciplined one-session work larger than Comet, say “Use Astral Orchestrator in
Singularity mode.”
For a bounded card with a user-selected model route, say “Use Astral Orchestrator in Morph
mode.” For independent cards that may safely fan out, say “Use Astral Orchestrator in
Constellation mode.”

Morph’s optional OpenCodex provider route is user-owned: configure it separately if you
choose it. Astral Orchestrator does not install providers, handle credentials, or claim
that a requested effort was accepted natively by an external model.

## Sample prompts for every mode

Copy any of these prompts into a new Codex task and replace the example details with your
own request:

- **Comet:** `Use Astral Orchestrator in Comet mode to rename the typo “recieve” to “receive” in README.md, then run the relevant check.`
- **Orbit:** `Use Astral Orchestrator in Orbit mode to add a search box to the settings page, update its tests, and report the checks you ran.`
- **Event Horizon:** `Use Astral Orchestrator in Event Horizon mode to rotate the staging API credential reference, show me the plan first, and do not apply changes until I confirm.`
- **Singularity:** `Use Astral Orchestrator in Singularity mode to complete this low-risk multi-step documentation cleanup in one verified Sol session, with no subagents or fresh reviewer.`
- **Pulsar:** `Use Astral Orchestrator in Pulsar mode to fix the failing date-format test, freeze one card with its acceptance checks, and record the observed route evidence.`
- **Morph:** `Use Astral Orchestrator in Morph mode for this bounded card: update the CSV export heading and its test using the worker model and effort I specify, then have Sol review it.`
- **Constellation:** `Use Astral Orchestrator in Constellation mode to update the independent README, changelog, and test-fixture cards only when they have non-overlapping ownership and enough available concurrency.`

Orbit remains the recommended default for normal work. The live Astral status panel is a
user-facing progress view: requested routes are shown first, and a route becomes observed
only after runtime evidence confirms what actually ran. Every Astral Status panel is an
actual GitHub-flavored Markdown table with a header separator row—never a code block or
plain pipe text.

For Constellation, **Sol High is sufficient and Sol Ultra is not required.** Sol remains
the configured primary and fresh reviewer; Constellation does not need extra Sol
implementers. A custom worker model and effort are available only through an explicit,
bounded Morph card, and only when that route supports the requested capability and has
runtime evidence. Constellation fans out only when the host advertises enough available
concurrency and each card has non-overlapping ownership; otherwise it uses serial
Orbit-style routing.

## Modes

| Mode | Best for | What happens |
|---|---|---|
| Comet | Tiny, obvious, easy-to-undo work | Sol works directly and self-reviews at the configured orchestrator effort. |
| Orbit (default) | Normal changes and projects | Sol plans, Luna or Terra implements bounded work, and fresh Sol reviews it. |
| Event Horizon | Credentials, payments, private data, production, migrations, or major changes | Visible plan, confirmation gates, pinned workers, strict verification, and read-only reviewer evidence. |
| Singularity (explicit opt-in) | Meaningful low- or medium-risk work larger than Comet | One verified Sol primary completes one compact card at the configured orchestrator effort, with no subagents or fresh reviewer and one proportional verification pass. |
| Pulsar (explicit opt-in) | A deliberately evidence-oriented request | Sol freezes one canonical card, records private local evidence, routes one pinned worker, and requests fresh Sol review. |
| Morph (explicit opt-in) | A bounded worker card that needs a user-selected routed or native model | Sol remains the configured primary, the worker receives an exact model id and requested effort, and fresh Sol reviews the result. |
| Constellation (explicit opt-in) | Several independent, ready cards | Sol proves independent ownership and host capacity, starts a cost-aware non-Sol first wave, integrates it, and requests one fresh Sol review. |

Astral Orchestrator raises safeguards when a request is riskier than the selected mode.
It does not broaden the work you asked for.
Singularity, Pulsar, Morph, and Constellation are never automatic; Orbit remains
recommended for normal work. Event Horizon overrides Singularity and safeguards override either
opt-in worker mode whenever the risk requires confirmation, serial routing, or observed
read-only review isolation.

### Legacy prompt migration

The former names remain advisory prompt aliases: Quick maps to Comet; Guided maps to
Orbit; Careful maps to Event Horizon; and Measured maps to Pulsar. New prompts and
documentation use the cosmic names, while an old prompt keeps the same behavior.

## How Astral chooses models and effort

Three separate decisions keep the workflow predictable:

1. **Mode determines whether to delegate.** Comet keeps a tiny change in the Sol primary;
   Singularity keeps larger low- or medium-risk work in one verified Sol primary session;
   Orbit, Event Horizon, and Pulsar delegate bounded implementation when there is work that can safely
   be handed off. Morph and Constellation work only when the user explicitly names them.
2. **Work characteristics choose Sol, Luna, or Terra.** Sol retains requirements,
   architecture, safety boundaries, and acceptance decisions. Luna receives narrow,
   repeatable, fully specified work. Terra receives context-heavy implementation,
   debugging, integrations, or moderate refactoring after Sol has settled the plan.
3. **Each lane reads its effort from the per-lane settings file.** Effort is not
   dynamically chosen from each prompt. On current MultiAgentsV2 hosts, Astral passes
   the configured model and effort explicitly to a native child. A matching optional
   profile can be used only when its fixed values agree, because profile values take
   precedence. The process launcher remains a legacy fallback only for hosts that lack
   one or more of the native `agent_type`, `task_name`, `model`, `reasoning_effort`, and
   `fork_turns` controls. Astral stops if it
   cannot prove the requested model and effort; it does not substitute another route.
4. **Morph labels a worker request, not provider capability.** The selected model gets the
   requested effort label, but the route records upstream-native effort as unverified until
   independent provider evidence exists.

### Singularity: disciplined one-session work

Singularity is explicit opt-in, never a default or automatic route. It uses exactly one
verified Sol primary at the configured orchestrator effort—never forced Max—and no
subagents, planning probes, worker lanes, or fresh reviewer. If you want Sol Max, set
the orchestrator effort and start a new task. Sol uses one work card, keeps no more than
five active steps with one in progress, loads targeted context, uses the smallest
sufficient intervention, and performs one proportional verification pass before its one
self-review. High-risk work switches to Event Horizon, including its confirmation gates and
independent reviewer requirements. All modes run the primary checker; Singularity requires
observed/verified Sol model and effort, must stop on unavailable evidence, and user
confirmation cannot satisfy or override that requirement.

These scope-control and verification patterns are adapted from
[single-agent-skills](https://github.com/blavkgokuvnn/single-agent-skills) at commit
`7fc169557e84e0d27fe22e7d4fc2a6bffeefe4b2`. The external plugin and runtime are not
bundled or required, and Astral has no StateM dependency. A social-media claim of 4% of a
five-times plan over six hours and doubled speed is anecdotal and unverified. Astral does
not promise or claim to have measured it.

The route below is a documented **heuristic**, based on the type of work and the route
contract. The separate local outcome scorecard described below is how to collect
effectiveness and efficiency evidence without pretending that a single anecdote proves a
model choice.

## Pulsar instruction-context footprint

Using `tiktoken` 0.13.0 with the `o200k_base` encoding, the current v3.6.0 core
`SKILL.md` measures **3,403 tokens**; Comet measures **4,722 tokens**; Orbit/full
measures **10,223 tokens**; and Pulsar measures **12,401 tokens**. Comet therefore
avoids **5,501 tokens (53.8%)** compared with eager full-bundle loading.
Comet loads the core skill and mode/risk reference only; it does not load work templates
or routing/preflight instructions.

These are static instruction-context measurements. This instruction-context footprint covers instruction-context loading only and does not prove every multi-agent run uses fewer total tokens than a single Sol run, and does not measure quality, latency, or price, or total tokens for a complete run. The committed
[context-footprint evidence](benchmarks/context-footprint-2026-08-21.json)
includes file hashes, byte/word/token counts, and a reproducible contributor command to
regenerate the published v3.6.0 measurement.

The 2026-08-21 v3.6.0 measurement uses stable historical bundle keys: `quick` means
Comet, `guided` means Orbit, and `measured` means Pulsar. The older v3.2.0 snapshot is
preserved as historical evidence. These measurements support the architecture's
progressive context loading, not task quality, latency, price, or total-run tokens.
Alongside exact pinned routes, objective checks plus fresh review, and the local
privacy/no-analytics runtime posture, they are tested workflow contracts rather than
proof of outcome superiority. See the
[benchmark guide](benchmarks/README.md) for the method and scope.

## Public evidence status

The current repository verification passed **100+ automated tests** and **package verification**.
This validates behavior and contracts; it does not prove Astral beats single-Sol or
establish a valid outcome comparison.

The first end-to-end pilot is retained as invalid exploratory evidence after fresh
review found protocol defects. [Its disclosure](benchmarks/results/2026-08-04-invalid-pilot/INVALID.md)
explains why the raw artifacts remain auditable but unsuitable for comparison. No valid
outcome comparison exists. This README does not publish outcome, token, time, or quality
numbers from that pilot.

The reproducible pinned/state/evidence method was inspired by OpenRouter's Ori Eval;
see the [Ori Eval page](https://openrouter.ai/ori/eval) and
[spawn-ori-eval skill](https://openrouter.ai/skills/spawn-ori-eval). Astral Orchestrator
uses only pinned Codex GPT-5.6 Sol/Terra/Luna lanes; it does not run or depend on
Ori or OpenRouter.

## Configurable effort levels

Reasoning effort is the requested reasoning level/budget for a lane. Higher values can
increase latency and usage, and do not guarantee a better answer. Defaults are Sol High
for the orchestrator and reviewer, Luna Max, and Terra High.

Show the effective settings:

~~~sh
sh scripts/configure-effort.sh --show
~~~

Change one lane without changing the others:

~~~sh
sh scripts/configure-effort.sh --luna medium
~~~

Set multiple lanes or reset all defaults:

~~~sh
sh scripts/configure-effort.sh --orchestrator high --luna medium --terra high --reviewer high
sh scripts/configure-effort.sh --reset
~~~

Allowed values are minimal, low, medium, high, xhigh, max, and ultra. Max and ultra are
model-dependent and account-dependent. A rejected value is an error, never a silent
fallback. Settings persist at ~/.codex/astral-orchestrator/effort-levels.toml (or inside
CODEX_HOME when set), outside the plugin cache.

## How routing and verification work

![Hand-drawn workflow showing a request choosing Comet or Orbit/Event Horizon work; Orbit/Event Horizon flows through planning, Luna or Terra, checks, and a fresh Sol review before handoff.](assets/diagrams/routing-and-verification.svg)

[Open the editable Excalidraw source for the routing and verification diagram.](assets/diagrams/routing-and-verification.excalidraw)

In delegated routes, Sol uses `gpt-5.6-sol`; Luna uses `gpt-5.6-luna`; Terra uses
`gpt-5.6-terra`; and the fresh reviewer uses `gpt-5.6-sol`. Singularity uses only the
verified Sol primary and its self-review. The configurable effort settings described above
supply each lane's effort (Sol High, Luna Max, Terra High, reviewer Sol High by default),
rather than the prompt choosing a new effort at runtime.

For every mode, Astral first runs its local primary checker. When `CODEX_THREAD_ID` and
local rollout evidence are available, it automatically verifies that the primary is
`gpt-5.6-sol` at the configured orchestrator effort. The checker emits only allowlisted
route fields and never prints prompt or session contents. Only when that evidence is
unavailable, only non-Singularity modes may ask once for the user's confirmation.
Singularity requires observed/verified Sol model and effort, must stop on unavailable,
and user confirmation cannot satisfy or override that requirement. A mismatch or invalid
result blocks every route.

For Orbit, Event Horizon, and Pulsar work, Astral Orchestrator first checks whether
`collaboration.spawn_agent` exposes all five required MultiAgentsV2 controls:
`agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`. A current
MultiAgentsV2 host uses the native standard route with a complete standalone packet,
`fork_turns: "none"`, and the exact model and configured effort for each child. A matching
optional custom profile is used only when its fixed values match the effective settings;
its TOML values take precedence over explicit spawn values.
Missing or different profiles do not weaken the route or demand setup: Astral uses the
built-in native worker with explicit values for Luna or Terra, and the built-in native
default for a reviewer. Only a host that lacks one or more of `agent_type`, `task_name`,
`model`, `reasoning_effort`, and `fork_turns` may use the bundled legacy exact-process
launcher, which emits an
ASTRAL_ORCHESTRATOR_ROUTE header with allowlisted route facts and never the task packet,
instructions, secrets, or file contents.

A task name is not proof of the route. Missing or mismatched `agent_type`, `task_name`,
`model`, `reasoning_effort`, or `fork_turns`, or missing review isolation, blocks the lane
and tells you the smallest corrective action.

### Morph and Constellation

Morph is optional. It can use an OpenCodex-routed `provider/model` or another user-selected
native model only for a bounded worker card. OpenCodex is independently installed and
configured by the user: Astral never changes `~/.opencodex`, starts a service, installs a
package, handles credentials, or assumes provider terms-of-service compatibility. It adds
no network client; its launcher only invokes the existing `codex` command. Provider/model
support and effort semantics are capability-dependent, and a worker failure blocks that
worker rather than falling back silently. A configured external or non-OpenAI provider may
receive the worker packet during model inference. “No network client” means Astral adds no
network client, service, or credential handling; it does not mean provider traffic is local.

Constellation is also optional. It starts a concurrent first wave only after Sol proves
that cards are independent and have non-overlapping ownership, the host advertises enough
available slots after the primary consumes one, and the configured roster has suitable
cost-aware non-Sol workers. It never hard-codes a child count or creates extra Sol
implementers by default. If capacity or independence is uncertain, it uses serial
Orbit-style routing instead.

Pulsar freezes exactly one canonical card and its checks before routing. If Luna versus
Terra is ambiguous, Sol sends exactly one behaviorally read-only probe to each lane with
the identical card; this is not hard sandbox isolation. The non-secret tracker files are
owner-only and resumable under a private `/tmp` path derived from effective UID plus
repository-root and frozen-card SHA-256 prefixes. Only the selected lane edits; fixes
need fresh verification and a new Sol reviewer.

## Benchmarking Astral against a single-Sol control

The repository includes a separate local, standard-library outcome scorecard. It does
not call Codex, send data anywhere, or manufacture a result: you run the same frozen task
cases, record the trial facts in JSONL, then ask the scorecard to validate and summarize
them. It is distinct from the instruction-context footprint above.

![Hand-drawn comparison showing the same frozen cases run through a single-Sol control and an Astral route, then joined by identical checks, route evidence, and a local scorecard.](assets/diagrams/outcome-scorecard.svg)

[Open the editable Excalidraw source for the outcome-scorecard diagram.](assets/diagrams/outcome-scorecard.excalidraw)

Quick start: create at least two JSONL records for every task case under each strategy
(the guide shows the exact schema), then run:

~~~sh
python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py benchmarks/trials.jsonl
python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py --format json benchmarks/trials.jsonl
~~~

The scorecard requires the same case fingerprint, matching repeated trials, and identical
acceptance checks for `single-sol` and `astral`. Within either strategy, its observed
route role/model/effort settings must remain fixed across repetitions; the two strategies
may intentionally differ. It reports success, first-pass acceptance, rework, route
correctness, wall time, and model calls; input/output token counts and a 0–100 quality
score are optional. Record quality scoring blind to strategy when practical. Read the
[benchmark guide and JSONL schema](benchmarks/README.md) before collecting trials.

The output can show what happened for the recorded cases and settings. It cannot prove
that Astral is generally faster, better, or cheaper, establish causation from a small
sample, or rescue a comparison with a wrong route or unequal acceptance checks. Treat a
route-correctness warning, a non-blind quality score, or a small/unrepresentative case
set as a reason to investigate before making a product claim.

## Safety and privacy

- Existing different optional native profiles are never overwritten.
- Profile removal deletes only shipped files that still match exactly.
- Destructive, credential, publishing, production, and irreversible actions require
  an explicit confirmation gate in Event Horizon mode.
- Native MultiAgentsV2 routes pass a complete standalone packet only to the selected
  native child. The legacy local process route keeps its private packet in a local
  temporary file, passes it only to the selected Codex process, then removes it after
  that process exits. An external Morph provider can receive its bounded worker packet
  during inference when the user explicitly configures that route; local packet handling
  does not make external processing local. There is no analytics collection, extra network
  client, API key, or background service.
- A fresh reviewer is required after worker-produced Orbit, Pulsar, Morph, or
  Constellation work. Event Horizon mode—and high-risk Pulsar, Morph, or Constellation work—
  also requires observed read-only review isolation.

## Updating and the 3.0 migration

To refresh the optional native profiles in a downloaded checkout, replace it with the
newer complete repository and run:

~~~sh
sh scripts/setup.sh --refresh
~~~

The refresh migrates only byte-exact shipped v3.4.0 Luna XHigh and Terra XHigh profiles
to Luna Max and Terra High. A customized or conflicting profile remains untouched; on a
current MultiAgentsV2 host it is not needed for native delegation.

Version 3.0.0 was a breaking identity migration from the former name, Project Pilot.
The plugin and marketplace IDs are now `astral-orchestrator`, profile filenames begin
with `astral-orchestrator-`, TOML agent names begin with `astral_orchestrator_`, route
evidence begins with `ASTRAL_ORCHESTRATOR_ROUTE`, and persistent settings live under
`~/.codex/astral-orchestrator/`. Install the new package; remove the former package
separately only when you no longer use it. Old effort settings are intentionally not
copied, so set desired values again with `configure-effort.sh`.

## Uninstalling

Remove the installed plugin:

~~~sh
codex plugin remove astral-orchestrator@astral-orchestrator
~~~

Remove the companion profiles only if they still exactly match the shipped versions:

~~~sh
sh plugins/astral-orchestrator/scripts/install-agents.sh --remove
~~~

Optionally remove this local marketplace entry:

~~~sh
codex plugin marketplace remove astral-orchestrator
~~~

These commands do not delete your downloaded repository or project files.

## Troubleshooting

| Problem | What to do |
|---|---|
| The plugin does not appear | Start a new Codex task, then run codex plugin list --marketplace astral-orchestrator. |
| Setup reports a profile conflict | Astral Orchestrator will not overwrite a customized native profile. Keep it: current MultiAgentsV2 hosts use the built-in native worker for Luna or Terra, or built-in native default for a reviewer, with explicit values. Run `sh scripts/setup.sh --refresh` only if you deliberately want the fixed role profile restored. |
| A route cannot be proven | Confirm that the current host exposes all five v2 controls: `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`. Only a host that lacks one or more of `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` should use the bundled launcher dry run to prove the exact legacy role, model, and effort; never accept another route as a fallback. |
| A Morph worker fails | Check the separately configured provider/model and requested effort with its owner. Astral does not configure OpenCodex, credentials, services, or provider compatibility. |
| Constellation will not fan out | Make each card independent with non-overlapping ownership, or continue with the serial Orbit-style fallback. The primary consumes one advertised slot. |
| An effort value is rejected | Pick a supported value available to your account; max and ultra are not available everywhere. |
| Setup cannot find Codex or Python | Install or update Codex and use Python 3.11 or newer, then rerun the dry run. |

## Frequently asked questions

### Does this make Codex faster?

Not automatically. It makes non-trivial work more deliberate by selecting the right
pinned lane and demanding evidence before handoff.

### Can I use only one model?

Comet and explicit Singularity use the verified Sol primary alone; Singularity can cover
larger eligible low- or medium-risk work with its one self-review. Orbit, Event Horizon, and
Pulsar require the three specified models when bounded execution or independent review
is needed; there is no silent model substitution. Morph can use a user-selected worker
model only after an explicit opt-in, while Constellation defaults to non-Sol workers and
retains one Sol primary and one fresh Sol reviewer.

### Are my effort settings lost during an update?

No. They live outside the plugin cache at the Astral Orchestrator settings path. The
former Project Pilot settings path is deliberately separate because this release changes
the product identifier.

### Can I share this with a team?

Yes. Share the GitHub link, then have each person run the two Quick Install commands in
their own Codex environment. They need their own access to the three models.

## Sharing

The repository is public at https://github.com/Demonbane18/astral-orchestrator. Share
the link or a complete archive. Ask recipients to use the two GitHub marketplace commands;
use the optional setup only when native profiles are wanted. Do not share an installed
profile directory on its own.

## Contributor commands

Run these from the repository root after a behavior or packaging change:

~~~sh
python3 -B -m unittest discover -s tests -v
sh plugins/astral-orchestrator/scripts/verify.sh
sh scripts/setup.sh --dry-run
git diff --check
~~~

The project does not add secrets, analytics, network runtime, or destructive setup.
Ask before publishing, pushing, or changing a user's global Codex configuration.

## License

Astral Orchestrator is distributed under the MIT License. See LICENSE.

## Sol Advisor attribution

Astral Orchestrator is an independent adaptation inspired by
[DannyMac180/sol-advisor](https://github.com/DannyMac180/sol-advisor), revision
92f0fb105854e0fa606bdc98bfe688411e1db989. The original Sol Advisor MIT notice and
copyright are preserved in NOTICE.md and LICENSE. Astral Orchestrator is not endorsed by
or affiliated with Daniel McAteer.
