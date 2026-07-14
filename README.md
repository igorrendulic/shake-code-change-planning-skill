# Shape Code Change

`shape-code-change` is a planning-only Codex skill for investigating requested software changes and producing decision-complete, code-routed implementation plans. It supports micro, standard, and full planning depth, validates handoff-ready plans, and prepares macro-level delivery slices for later task-graph decomposition.

## Install from GitHub

Install the latest `main` revision without cloning the repository:

```sh
curl -fsSL https://raw.githubusercontent.com/igorrendulic/shake-code-change-planning-skill/main/install.sh | bash
```

Restart Codex after installation.

To replace an existing installation:

```sh
curl -fsSL https://raw.githubusercontent.com/igorrendulic/shake-code-change-planning-skill/main/install.sh | bash -s -- --force
```

Install a branch, tag, or commit with `--ref`:

```sh
curl -fsSL https://raw.githubusercontent.com/igorrendulic/shake-code-change-planning-skill/main/install.sh | bash -s -- --ref v1.0.0
```

## Install from a local clone

```sh
git clone https://github.com/igorrendulic/shake-code-change-planning-skill.git
cd shake-code-change-planning-skill
./install.sh
```

The default destination is `${CODEX_HOME:-$HOME/.codex}/skills/shape-code-change`. Use `--dest PATH` for another location and `--force` to replace an existing installation.

## Use

Ask Codex:

```text
Use $shape-code-change to investigate this requested change and produce an implementation-ready plan.
```

The skill creates planning artifacts only. Its delivery slices preserve architectural boundaries and sequencing; task-graph owns smaller task files, task dependencies, and safe scheduling within each slice.

## Validate a plan

From the installed skill directory:

```sh
python3 scripts/validate-plan.py path/to/plan.md
python3 scripts/validate-plan.py path/to/plan.md --handoff
python3 scripts/validate-plan.py path/to/plan.md --handoff --json
```

## Uninstall

Remove the installed skill directory, then restart Codex:

```sh
rm -rf "${CODEX_HOME:-$HOME/.codex}/skills/shape-code-change"
```
