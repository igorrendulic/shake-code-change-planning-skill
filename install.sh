#!/usr/bin/env sh
set -eu

REPOSITORY="igorrendulic/shake-code-change-planning-skill"
REF="main"
DESTINATION="${CODEX_HOME:-$HOME/.codex}/skills/shape-code-change"
FORCE=0
REMOTE=0

usage() {
  cat <<'EOF'
Install the shape-code-change Codex skill.

Usage:
  ./install.sh [--force] [--dest PATH]
  ./install.sh --remote [--ref REF] [--force] [--dest PATH]

Options:
  --dest PATH  Install to PATH instead of $CODEX_HOME/skills/shape-code-change.
  --force      Replace an existing installation.
  --ref REF    Download this GitHub branch, tag, or commit (default: main).
  --remote     Download from GitHub even when running from a local clone.
  -h, --help   Show this help.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dest)
      if [ "$#" -lt 2 ]; then
        echo "error: --dest requires a path" >&2
        exit 2
      fi
      DESTINATION=$2
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --ref)
      if [ "$#" -lt 2 ]; then
        echo "error: --ref requires a value" >&2
        exit 2
      fi
      REF=$2
      shift 2
      ;;
    --remote)
      REMOTE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$REF" in
  ""|*[!A-Za-z0-9._/-]*)
    echo "error: invalid GitHub ref: $REF" >&2
    exit 2
    ;;
esac

if [ -z "$DESTINATION" ] || [ "$DESTINATION" = "/" ]; then
  echo "error: refusing unsafe destination: $DESTINATION" >&2
  exit 2
fi

if [ -e "$DESTINATION" ] || [ -L "$DESTINATION" ]; then
  if [ "$FORCE" -ne 1 ]; then
    echo "error: $DESTINATION already exists; rerun with --force to replace it" >&2
    exit 1
  fi
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd || pwd)
if [ "$REMOTE" -eq 0 ] && [ -f "$SCRIPT_DIR/SKILL.md" ]; then
  SOURCE_ROOT=$SCRIPT_DIR
else
  REMOTE=1
fi

DESTINATION_PARENT=$(dirname -- "$DESTINATION")
mkdir -p "$DESTINATION_PARENT"
WORK_DIR=$(mktemp -d "$DESTINATION_PARENT/.shape-code-change.install.XXXXXX")
trap 'rm -rf "$WORK_DIR"' EXIT HUP INT TERM

if [ "$REMOTE" -eq 1 ]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "error: curl is required for a GitHub installation" >&2
    exit 1
  fi
  if ! command -v tar >/dev/null 2>&1; then
    echo "error: tar is required for a GitHub installation" >&2
    exit 1
  fi

  ARCHIVE="$WORK_DIR/repository.tar.gz"
  EXTRACTED="$WORK_DIR/extracted"
  mkdir -p "$EXTRACTED"
  curl -fsSL "https://codeload.github.com/$REPOSITORY/tar.gz/$REF" -o "$ARCHIVE"
  tar -xzf "$ARCHIVE" -C "$EXTRACTED"
  SOURCE_ROOT=$(find "$EXTRACTED" -mindepth 1 -maxdepth 1 -type d -print | sed -n '1p')
  if [ -z "$SOURCE_ROOT" ]; then
    echo "error: downloaded archive did not contain a repository directory" >&2
    exit 1
  fi
fi

for required in SKILL.md agents/openai.yaml references/plan-format.md scripts/validate-plan.py; do
  if [ ! -f "$SOURCE_ROOT/$required" ]; then
    echo "error: source is missing required skill file: $required" >&2
    exit 1
  fi
done

PAYLOAD="$WORK_DIR/payload"
mkdir -p "$PAYLOAD"
cp "$SOURCE_ROOT/SKILL.md" "$PAYLOAD/SKILL.md"
cp -R "$SOURCE_ROOT/agents" "$PAYLOAD/agents"
cp -R "$SOURCE_ROOT/references" "$PAYLOAD/references"
cp -R "$SOURCE_ROOT/scripts" "$PAYLOAD/scripts"

if [ -e "$DESTINATION" ] || [ -L "$DESTINATION" ]; then
  BACKUP="$WORK_DIR/previous"
  mv "$DESTINATION" "$BACKUP"
  if ! mv "$PAYLOAD" "$DESTINATION"; then
    mv "$BACKUP" "$DESTINATION"
    echo "error: installation failed; restored the previous installation" >&2
    exit 1
  fi
  rm -rf "$BACKUP"
else
  mv "$PAYLOAD" "$DESTINATION"
fi

echo "Installed shape-code-change to $DESTINATION"
echo "Restart Codex to load the skill."
