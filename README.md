# Project Pilot

Project Pilot helps Codex take a request from “please do this” to a checked result. It
is a beginner-friendly, model-routed adaptation of
[Sol Advisor](https://github.com/DannyMac180/sol-advisor), designed for people who do
not want to manage agent roles, model tiers, or developer tooling by hand.

Project Pilot needs no additional API key, paid service, or background server beyond
Codex. The setup helper installs the plugin plus three agent profiles. The defaults are
Luna XHigh for focused work, Terra XHigh for context-heavy work, and Sol High for fresh
review. You start a Sol task at the configured orchestrator effort; High is the default.

When Codex exposes native custom-agent selection, Project Pilot uses it. On Codex builds
that expose only generic subagents, the bundled launcher starts separate Codex processes
with the same exact Luna, Terra, or reviewer model, effort, role instructions, and
sandbox. A task name alone is never accepted as proof of a model route.

## What Project Pilot does

Project Pilot gives Codex a repeatable way to:

1. let Sol translate your request into a clear result and work plan at its configured effort;
2. send repeatable, tightly specified work to Luna at its configured effort;
3. send context-heavy implementation, debugging, or integration to Terra at its configured effort;
4. combine the work and run real checks instead of assuming it worked;
5. use a fresh Sol reviewer at its configured effort and explain the evidence plainly.

It works for code, documentation, configuration, research artifacts, and other
workspace-based projects.

## Install

Guided and Careful modes require actual access to Sol, Luna, and Terra. Setup installs
their profiles but cannot grant model access to an account. Quick mode still requires
the task to use Sol at the configured orchestrator effort. Setup also checks for Python
3.11 or newer. Python 3.11 runs locally to validate the profiles, read the temporary
work packet, pass that packet directly to the selected Codex process, and inspect only
the routing fields needed for verification. Project Pilot does not send the packet to
another service or keep a separate copy; the selected Codex process uses your existing
Codex session normally.

### Easiest: ask Codex to install it

Open this repository in Codex and send:

> Install Project Pilot and its three model-routed agents from this repository. Run its
> verification, do not overwrite conflicting agent files, and tell me when to start a
> new Sol task at my configured orchestrator effort.

Codex can follow the repository structure and run the setup helper for you.

### One command from a downloaded copy

Download and unzip the repository, open a terminal in the unzipped folder, then paste:

```sh
sh scripts/setup.sh
```

The setup helper registers this folder as a local marketplace, installs the plugin, and
adds three namespaced profiles to Codex's `agents` folder. It never overwrites a
different profile. If you want to see the commands without changing anything, run
`sh scripts/setup.sh --dry-run` first.

After installation, select **gpt-5.6-sol** with your configured orchestrator effort
(**High** by default) and start a **new Codex task** so the skill and profiles are
discovered.

### Install from GitHub after publishing

Once this repository has a public GitHub address, a friend can paste that link into
Codex with the install request above. Codex should download the complete repository and
run `sh scripts/setup.sh`; installing only the marketplace entry would omit the three
agent profiles.

## Try it

You can speak normally. For example:

```text
Use Project Pilot to orchestrate adding a search box and verify every lane.
```

```text
Use Project Pilot to fix this error. Keep the change focused and explain the checks.
```

```text
Use Project Pilot in Careful mode to plan, delegate, review, and complete this request.
```

The plugin defaults to Guided mode, so naming a mode is optional.

## Choose a mode

| Mode | Use it for | Example |
|---|---|---|
| Quick | Tiny, obvious, easy-to-undo work | Sol works directly and self-reviews at its configured effort |
| Guided | Normal changes and projects | Sol plans; Luna or Terra implements at configured effort; Sol reviews |
| Careful | Login, payments, private data, migrations, production, or major changes | Visible plan, confirmation gates, pinned workers, and read-only Sol review |

Project Pilot automatically raises the safeguards when a request is riskier than the
chosen mode. It does not make the requested scope larger.

## Tune the effort levels

Reasoning effort controls how much work a model spends thinking. Project Pilot keeps
the original defaults—Sol `high` for the orchestrator and reviewer, Luna `xhigh`, and
Terra `xhigh`—but you can change each lane independently without editing a TOML file.

The easiest option is to ask Codex:

> Show my Project Pilot effort levels, then set Luna to medium. Do not change the other
> lanes.

From a downloaded copy, the equivalent command is:

```sh
sh scripts/configure-effort.sh --luna medium
```

You can set several lanes together:

```sh
sh scripts/configure-effort.sh --orchestrator high --luna medium --terra high --reviewer high
```

Use `--show` to see the current settings or `--reset` to restore all defaults. Accepted
values are `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, and `ultra`. Availability
is model-dependent and account-dependent, especially for `max` and `ultra`; Project
Pilot stops if Codex rejects a value instead of quietly using a different one.

Worker and reviewer changes take effect on their next delegated job. An orchestrator
change takes effect when you start a new Sol task at that effort. Custom worker or
reviewer values automatically use the exact-process route, because the installed native
profiles retain the safe defaults. Your settings live outside the plugin cache, so an
update does not erase them.

## Update

For a local downloaded copy, replace the files with the newer version and run:

```sh
sh scripts/setup.sh --refresh
```

The refresh checks or safely installs the three agent profiles again, then reinstalls
the plugin. It preserves your effort settings. Start a new Codex task after updating.

## Share

Share the entire repository, not only the `plugins/project-pilot` folder. The top-level
`.agents/plugins/marketplace.json` file is what lets Codex recognize the repository as
a marketplace.

The easiest sharing flow is:

1. publish this repository to GitHub;
2. send people the GitHub link;
3. tell them to paste this into Codex:

> Install and set up Project Pilot plus its three agent profiles from this GitHub
> repository. Run its tests and verification, preserve conflicting files, and tell me
> to start a new Sol task at my configured orchestrator effort when ready.

Before publishing, personalize the contributor name and repository links if desired.
The current package deliberately contains no fake homepage URL.

## Remove

Remove the installed plugin:

```sh
codex plugin remove project-pilot@project-pilot
```

Remove the three companion profiles only when they still exactly match Project Pilot:

```sh
sh plugins/project-pilot/scripts/install-agents.sh --remove
```

If you no longer want Codex to list this marketplace either, also run:

```sh
codex plugin marketplace remove project-pilot
```

These commands do not delete your downloaded repository or project work. The profile
remover refuses to delete a file you customized.

## Troubleshooting

### Project Pilot does not appear

- Start a new Codex task; skills are discovered when a task starts.
- Run `codex plugin list --marketplace project-pilot` and look for
  `project-pilot@project-pilot`.
- From this repository, run `sh plugins/project-pilot/scripts/verify.sh`.

### Setup says the marketplace name already exists

A different Project Pilot copy may already be registered. Remove that marketplace only
if you no longer need it, then rerun setup:

```sh
codex plugin marketplace remove project-pilot
sh scripts/setup.sh
```

Use `--refresh` after a partially completed first install only when you did not remove
the marketplace; it may already be registered even if a conflicting agent profile
stopped setup later.

### Setup says an agent profile differs

Project Pilot refuses to overwrite a customized file. Ask Codex to compare the named
installed profile with the shipped profile and preserve any customization you need.
After resolving the conflict deliberately, run `sh scripts/setup.sh --refresh`.

### Project Pilot says a model route cannot be proven

- Run `sh scripts/configure-effort.sh --show`, then confirm the current task uses
  `gpt-5.6-sol` with the displayed orchestrator effort.
- Run `sh scripts/setup.sh --refresh` from the complete repository.
- Start a new task; existing tasks do not discover newly installed agent profiles.
- Do not ask Project Pilot to silently fall back. Its strict stop protects the routing
  guarantee.

## For contributors

Run the complete local checks:

```sh
python3 -B -m unittest discover -s tests -v
sh plugins/project-pilot/scripts/verify.sh
```

The design rationale and remaining opportunities are in
[`docs/IMPROVEMENTS.md`](docs/IMPROVEMENTS.md). Attribution is documented in
[`NOTICE.md`](NOTICE.md). This project is licensed under the MIT License.
