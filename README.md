# Project Pilot

Project Pilot helps Codex take a request from “please do this” to a checked result. It
is a simpler, model-independent adaptation of
[Sol Advisor](https://github.com/DannyMac180/sol-advisor), designed for people who do
not want to learn agent roles, model tiers, or developer tooling.

There is no API key, paid service, separate agent pack, or extra runtime package to
configure. Native agents are used only when they are available and genuinely useful.

## What Project Pilot does

Project Pilot gives Codex a repeatable way to:

1. translate your request into a clear result;
2. choose a sensible amount of planning and review;
3. do the work without expanding the scope;
4. run real checks instead of assuming it worked;
5. explain the outcome, evidence, and remaining risk in plain language.

It works for code, documentation, configuration, research artifacts, and other
workspace-based projects.

## Install

### Easiest: ask Codex to install it

Open this repository in Codex and send:

> Install Project Pilot from this repository, run its verification, and tell me when I
> should start a new task to use it.

Codex can follow the repository structure and perform the two plugin commands for you.

### One command from a downloaded copy

Download and unzip the repository, open a terminal in the unzipped folder, then paste:

```sh
sh scripts/setup.sh
```

The setup helper registers this folder as a local marketplace and installs the plugin.
It does not overwrite project files. If you want to see the commands without changing
anything, run `sh scripts/setup.sh --dry-run` first.

After installation, start a **new Codex task** so the new skill is discovered.

### Install from GitHub after publishing

Once this repository has a public GitHub address, people can use the repository address
directly:

```sh
codex plugin marketplace add owner/repository --ref main
codex plugin add project-pilot@project-pilot
```

Replace `owner/repository` with the two parts shown in the GitHub page address. A friend
who does not use the terminal can paste the repository link into Codex with the install
request above.

## Try it

You can speak normally. For example:

```text
Use Project Pilot to add a search box and verify that it works.
```

```text
Use Project Pilot to fix this error. Keep the change focused and explain the checks.
```

```text
Use Project Pilot to plan and complete this request from start to finish.
```

The plugin defaults to Guided mode, so naming a mode is optional.

## Choose a mode

| Mode | Use it for | Example |
|---|---|---|
| Quick | Tiny, obvious, easy-to-undo work | “Use Project Pilot in Quick mode to fix these typos.” |
| Guided | Normal changes and projects | “Use Project Pilot to add a contact form.” |
| Careful | Login, payments, private data, migrations, production, or major changes | “Use Project Pilot in Careful mode to change our sign-in flow.” |

Project Pilot automatically raises the safeguards when a request is riskier than the
chosen mode. It does not make the requested scope larger.

## Update

For a local downloaded copy, replace the files with the newer version and run:

```sh
sh scripts/setup.sh --refresh
```

For a marketplace installed directly from GitHub, run:

```sh
codex plugin marketplace upgrade project-pilot
codex plugin add project-pilot@project-pilot
```

Start a new Codex task after updating.

## Share

Share the entire repository, not only the `plugins/project-pilot` folder. The top-level
`.agents/plugins/marketplace.json` file is what lets Codex recognize the repository as
a marketplace.

The easiest sharing flow is:

1. publish this repository to GitHub;
2. send people the GitHub link;
3. tell them to paste this into Codex:

> Install and set up the Project Pilot plugin from this GitHub repository. Run its
> verification before installing it, and tell me to start a new task when ready.

Before publishing, personalize the contributor name and repository links if desired.
The current package deliberately contains no fake homepage URL.

## Remove

Remove the installed plugin:

```sh
codex plugin remove project-pilot@project-pilot
```

If you no longer want Codex to list this marketplace either, also run:

```sh
codex plugin marketplace remove project-pilot
```

These commands remove Codex's installed entry. They do not delete your downloaded
repository or project work.

## Troubleshooting

### Project Pilot does not appear

- Start a new Codex task; skills are discovered when a task starts.
- Run `codex plugin list --available` and look for `project-pilot@project-pilot`.
- From this repository, run `sh plugins/project-pilot/scripts/verify.sh`.

### Setup says the marketplace name already exists

A different Project Pilot copy may already be registered. Remove that marketplace only
if you no longer need it, then rerun setup:

```sh
codex plugin marketplace remove project-pilot
sh scripts/setup.sh
```

### Project Pilot says independent review is unavailable

Your current Codex session may not expose a suitable fresh-agent tool. Ordinary Guided
work can still receive a labeled self-review. Careful work reports the independent
review as incomplete instead of pretending it happened.

## For contributors

Run the complete local checks:

```sh
python3 -B -m unittest discover -s tests -v
sh plugins/project-pilot/scripts/verify.sh
```

The design rationale and remaining opportunities are in
[`docs/IMPROVEMENTS.md`](docs/IMPROVEMENTS.md). Attribution is documented in
[`NOTICE.md`](NOTICE.md). This project is licensed under the MIT License.
