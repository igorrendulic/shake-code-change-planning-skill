#!/usr/bin/env sh
set -eu

REPO_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TMP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/shape-code-change-install-test.XXXXXX")
trap 'rm -rf "$TMP_ROOT"' EXIT HUP INT TERM

assert_file() {
  if [ ! -f "$1" ]; then
    echo "expected file: $1" >&2
    exit 1
  fi
}

assert_absent() {
  if [ -e "$1" ]; then
    echo "expected path to be absent: $1" >&2
    exit 1
  fi
}

LOCAL_DEST="$TMP_ROOT/local/shape-code-change"
sh "$REPO_ROOT/install.sh" --dest "$LOCAL_DEST"
assert_file "$LOCAL_DEST/SKILL.md"
assert_file "$LOCAL_DEST/agents/openai.yaml"
assert_file "$LOCAL_DEST/references/plan-format.md"
assert_file "$LOCAL_DEST/scripts/validate-plan.py"
assert_absent "$LOCAL_DEST/.git"
assert_absent "$LOCAL_DEST/README.md"

if sh "$REPO_ROOT/install.sh" --dest "$LOCAL_DEST" >"$TMP_ROOT/existing.out" 2>"$TMP_ROOT/existing.err"; then
  echo "installer overwrote an existing installation without --force" >&2
  exit 1
fi
grep -q -- '--force' "$TMP_ROOT/existing.err"
sh "$REPO_ROOT/install.sh" --force --dest "$LOCAL_DEST"

ARCHIVE_ROOT="$TMP_ROOT/archive/shake-code-change-planning-skill-test"
mkdir -p "$ARCHIVE_ROOT/agents" "$ARCHIVE_ROOT/references" "$ARCHIVE_ROOT/scripts"
cp "$REPO_ROOT/SKILL.md" "$ARCHIVE_ROOT/SKILL.md"
cp "$REPO_ROOT/agents/openai.yaml" "$ARCHIVE_ROOT/agents/openai.yaml"
cp "$REPO_ROOT/references/plan-format.md" "$ARCHIVE_ROOT/references/plan-format.md"
cp "$REPO_ROOT/scripts/validate-plan.py" "$ARCHIVE_ROOT/scripts/validate-plan.py"
tar -czf "$TMP_ROOT/repository.tar.gz" -C "$TMP_ROOT/archive" shake-code-change-planning-skill-test

mkdir -p "$TMP_ROOT/bin" "$TMP_ROOT/remote-cwd"
cat >"$TMP_ROOT/bin/curl" <<'EOF'
#!/usr/bin/env sh
set -eu
output=
url=
while [ "$#" -gt 0 ]; do
  case "$1" in
    -o)
      output=$2
      shift 2
      ;;
    -* ) shift ;;
    *)
      url=$1
      shift
      ;;
  esac
done
printf '%s\n' "$url" >"$FAKE_CURL_URL"
cp "$FAKE_CURL_ARCHIVE" "$output"
EOF
chmod +x "$TMP_ROOT/bin/curl"

REMOTE_DEST="$TMP_ROOT/remote/shape-code-change"
(
  cd "$TMP_ROOT/remote-cwd"
  PATH="$TMP_ROOT/bin:$PATH" \
    FAKE_CURL_ARCHIVE="$TMP_ROOT/repository.tar.gz" \
    FAKE_CURL_URL="$TMP_ROOT/requested-url" \
    sh "$REPO_ROOT/install.sh" --remote --ref test --dest "$REMOTE_DEST"
)
assert_file "$REMOTE_DEST/SKILL.md"
assert_file "$REMOTE_DEST/agents/openai.yaml"
assert_file "$REMOTE_DEST/references/plan-format.md"
assert_file "$REMOTE_DEST/scripts/validate-plan.py"
grep -q 'https://codeload.github.com/igorrendulic/shake-code-change-planning-skill/tar.gz/test' "$TMP_ROOT/requested-url"

echo "install tests passed"
