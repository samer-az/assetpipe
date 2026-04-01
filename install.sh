#!/usr/bin/env bash
#
# AssetPipe Installer
# Registers the MCP server + skill with Claude Code in one step.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_PATH="$SCRIPT_DIR/mcp-server/server.py"
SKILL_SRC="$SCRIPT_DIR/skill/SKILL.md"
SKILL_DST="$HOME/.claude/skills/assetpipe/SKILL.md"

# ── Colors ──────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# ── Preflight checks ───────────────────────────────────────────────
echo ""
echo "  AssetPipe Installer"
echo "  ==================="
echo ""

# Python 3.10+
if ! command -v python3 &>/dev/null; then
  err "python3 not found. Install Python 3.10+ first."
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  err "Python 3.10+ required (found $PY_VER)"
fi
info "Python $PY_VER"

# Claude Code CLI
if ! command -v claude &>/dev/null; then
  err "Claude Code CLI not found. Install from https://docs.anthropic.com/en/docs/claude-code"
fi
info "Claude Code CLI found"

# ── Gemini API key ──────────────────────────────────────────────────
if [ -z "${GEMINI_API_KEY:-}" ]; then
  # Check .env file
  if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env" 2>/dev/null || true
  fi
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo ""
  echo "  A Gemini API key is required (free at https://aistudio.google.com/)."
  echo ""
  read -rp "  Enter your GEMINI_API_KEY: " GEMINI_API_KEY
  if [ -z "$GEMINI_API_KEY" ]; then
    err "No API key provided."
  fi
fi
info "Gemini API key set"

# ── Install Python dependencies ─────────────────────────────────────
echo ""
echo "  Installing Python dependencies..."
pip install -q -r "$SCRIPT_DIR/mcp-server/requirements.txt"
info "Dependencies installed"

# ── Register MCP server ─────────────────────────────────────────────
echo ""
echo "  Registering MCP server with Claude Code..."

# Remove existing registration if present (idempotent reinstall)
claude mcp remove assetpipe --scope user 2>/dev/null || true

claude mcp add assetpipe \
  --scope user \
  --env GEMINI_API_KEY="$GEMINI_API_KEY" \
  -- python3 "$SERVER_PATH"

info "MCP server registered (scope: user)"

# ── Install skill ───────────────────────────────────────────────────
echo ""
echo "  Installing skill..."
mkdir -p "$(dirname "$SKILL_DST")"
cp "$SKILL_SRC" "$SKILL_DST"
info "Skill installed to $SKILL_DST"

# ── Done ────────────────────────────────────────────────────────────
echo ""
echo -e "  ${GREEN}Installation complete!${NC}"
echo ""
echo "  Restart Claude Code, then try:"
echo "    \"Generate a hero image for a tech startup landing page\""
echo ""
echo "  Images are saved to ./generated-images/ by default."
echo "  Set IMAGE_OUTPUT_DIR in 'claude mcp edit' to change this."
echo ""
