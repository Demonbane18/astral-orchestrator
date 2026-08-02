# Project Pilot

Project Pilot helps Codex take a request from “please do this” to a checked result. It
is a beginner-friendly, model-routed adaptation of
[Sol Advisor](https://github.com/DannyMac180/sol-advisor), designed for people who do
not want to manage agent roles, model tiers, or developer tooling by hand.

Project Pilot needs no additional API key, paid service, or background server beyond
Codex. The setup helper installs the plugin plus three agent profiles: Luna XHigh for
focused work, Terra XHigh for context-heavy work, and Sol High for fresh review. You
start the task with Sol High as the main orchestrator.

When Codex exposes native custom-agent selection, Project Pilot uses it. On Codex builds
that expose only generic subagents, the bundled launcher starts separate Codex processes
with the same exact Luna, Terra, or reviewer model, effort, role instructions, and
sandbox. A task name alone is never accepted as proof of a model route.

## What Project Pilot does

Project Pilot gives Codex a repeatable way to:

1. let Sol High translate your request into a clear result and work plan;
2. send repeatable, tightly specified work to Luna XHigh;
3. send context-heavy implementation, debugging, or integration to Terra XHigh;
4. combine the work and run real checks instead of assuming it worked;
5. use a fresh Sol High reviewer and explain the evidence in plain language.

It works for code, documentation, configuration, research artifacts, and other
workspace-based projects.

## Install

Guided and Careful modes require actual access to Sol, Luna, and Terra. Setup installs
their profiles but cannot grant model access to an account. Quick mode still requires
the task to be started with Sol High. Setup also checks for Python 3.11 or newer. Python
runs locally to validate the profiles, read the temporary work packet, pass that packet
directly to the selected Codex process, and inspect only the routing fields needed for
verification. Project Pilot does not send the packet to another service or keep a
separate copy; the selected Codex process uses your existing Codex session normally.

### Easiest: ask Codex to install it

Open this repository in Codex and send:

> Install Project Pilot and its three model-routed agents from this repository. Run its
> verification, do not overwrite conflicting agent files, and tell me when to start a
> new Sol High task.

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

After installation, select **gpt-5.6-sol** with **High** reasoning and start a **new
Codex task** so the skill and agent profiles are discovered.

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
| Quick | Tiny, obvious, easy-to-undo work | Sol High works directly and self-reviews |
| Guided | Normal changes and projects | Sol plans; Luna XHigh or Terra XHigh implements; Sol reviews |
| Careful | Login, payments, private data, migrations, production, or major changes | Visible plan, confirmation gates, pinned workers, and read-only Sol review |

Project Pilot automatically raises the safeguards when a request is riskier than the
chosen mode. It does not make the requested scope larger.

## Update

For a local downloaded copy, replace the files with the newer version and run:

```sh
sh scripts/setup.sh --refresh
```

The refresh checks or safely installs the three agent profiles again, then reinstalls
the plugin. Start a new Codex task after updating.

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
> to start a new Sol High task when ready.

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

- Confirm the current task uses `gpt-5.6-sol` with High reasoning.
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
