#!/usr/bin/env bash
# =============================================================================
# CypherPilot — Install / Uninstall Script
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/CypherMorgan/cypherpilot/main/scripts/install.sh | bash
#   curl -fsSL https://raw.githubusercontent.com/CypherMorgan/cypherpilot/main/scripts/install.sh | bash -s uninstall
#
# What it does (install):
#   1. Checks prerequisites (Python 3.11+, Node.js 18+, npm)
#   2. Clones or updates the repository
#   3. Creates a Python virtual environment and installs dependencies
#   4. Installs frontend dependencies and builds the SPA
#   5. Runs database migrations (SQLite by default — zero config)
#   6. Creates a `cypherpilot` CLI alias in the user's shell profile
#   7. Shows a summary with paths and how to start/remove
#
# What it does (uninstall):
#   1. Removes the virtual environment
#   2. Removes the installed application files
#   3. Removes the shell alias
#   4. Confirms nothing was left behind
# =============================================================================

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────────────
REPO_URL="https://github.com/CypherMorgan/cypherpilot.git"
REPO_BRANCH="master"
INSTALL_DIR="${CYPHERPILOT_HOME:-$HOME/.cypherpilot}"
CYPHERPILOT_VERSION="0.4.9"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helpers ──────────────────────────────────────────────────────────────────

log_info()  { printf "${CYAN}==>${NC} %s\n" "$*"; }
log_ok()    { printf "${GREEN}  ✓${NC} %s\n" "$*"; }
log_warn()  { printf "${YELLOW}  ⚠${NC} %s\n" "$*"; }
log_error() { printf "${RED}  ✗${NC} %s\n" "$*" >&2; }
log_step()  { printf "\n${BOLD}── %s ──${NC}\n" "$*"; }

check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    log_error "'$1' is required but not installed."
    case "$1" in
      python3|python) log_info "Install Python 3.11+ from https://www.python.org/downloads/" ;;
      node|npm)       log_info "Install Node.js 18+ from https://nodejs.org/" ;;
      git)            log_info "Install git from https://git-scm.com/downloads" ;;
      uv)             log_info "Install uv from https://docs.astral.sh/uv/#installation" ;;
    esac
    return 1
  fi
  log_ok "$1 found: $(command -v "$1")"
}

cleanup() {
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo ""
    log_error "Installation failed at step above. Leaving logs in $INSTALL_DIR"
    printf "  Remove partial install with:  ${BOLD}%s uninstall${NC}\n" "$0"
  fi
  exit $exit_code
}
trap cleanup EXIT

# ── Install ──────────────────────────────────────────────────────────────────

do_install() {
  echo ""
  echo "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
  echo "${BOLD}║        CypherPilot v${CYPHERPILOT_VERSION} — Installer           ║${NC}"
  echo "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
  echo ""

  # ── Step 1: Check prerequisites ──────────────────────────────────────────
  log_step "Checking prerequisites"

  # Try python3, then python
  PYTHON=""
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      PYTHON="$cmd"
      break
    fi
  done

  if [ -z "$PYTHON" ]; then
    log_error "Python 3.11+ is required but not found."
    log_info "Install from https://www.python.org/downloads/"
    exit 1
  fi

  pyver=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
  pyver_major=$(echo "$pyver" | cut -d. -f1)
  pyver_minor=$(echo "$pyver" | cut -d. -f2)

  if [ "$pyver_major" -lt 3 ] || { [ "$pyver_major" -eq 3 ] && [ "$pyver_minor" -lt 11 ]; }; then
    log_error "Python 3.11+ required (found $pyver)"
    exit 1
  fi
  log_ok "Python $pyver found: $(command -v "$PYTHON")"

  check_cmd git
  check_cmd node
  check_cmd npm

  # ── Step 2: Clone / update repository ────────────────────────────────────
  log_step "Getting CypherPilot source"

  if [ -d "$INSTALL_DIR" ]; then
    log_info "Updating existing installation in $INSTALL_DIR"
    cd "$INSTALL_DIR"
    git fetch origin "$REPO_BRANCH"
    git reset --hard "origin/$REPO_BRANCH"
    log_ok "Repository updated"
  else
    log_info "Cloning into $INSTALL_DIR"
    git clone --depth 1 --branch "$REPO_BRANCH" "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    log_ok "Repository cloned"
  fi

  # ── Step 3: Python virtual environment ────────────────────────────────────
  log_step "Setting up Python environment"

  # Remove old venv if it exists
  if [ -d "$INSTALL_DIR/.venv" ]; then
    log_info "Removing existing virtual environment..."
    rm -rf "$INSTALL_DIR/.venv"
  fi

  log_info "Creating virtual environment..."
  "$PYTHON" -m venv "$INSTALL_DIR/.venv"
  log_ok "Virtual environment created"

  # Activate
  source "$INSTALL_DIR/.venv/bin/activate"

  # Upgrade pip
  log_info "Upgrading pip..."
  pip install --upgrade pip --quiet 2>&1 | tail -1
  log_ok "pip upgraded"

  # Install dependencies — tries uv first for speed, falls back to pip
  log_info "Installing Python dependencies..."
  if command -v uv &>/dev/null; then
    log_info "Using uv (fast)"
    uv pip install --no-cache -e "$INSTALL_DIR" 2>&1
  else
    log_info "Using pip"
    pip install --no-cache -e "$INSTALL_DIR" 2>&1
  fi
  log_ok "Python dependencies installed"

  # ── Step 4: Frontend ──────────────────────────────────────────────────────
  log_step "Building frontend"

  cd "$INSTALL_DIR/frontend"
  log_info "Installing frontend dependencies..."
  npm install --silent 2>&1 | tail -1
  log_ok "Frontend dependencies installed"

  log_info "Building production bundle..."
  npm run build 2>&1 | tail -1
  log_ok "Frontend built"

  # ── Step 5: Database ──────────────────────────────────────────────────────
  log_step "Setting up database"

  cd "$INSTALL_DIR"
  if [ ! -f "$INSTALL_DIR/.env" ]; then
    log_info "Creating .env from .env.example (SQLite by default)"
    cp .env.example .env
    # Switch to SQLite for zero-config local setup
    sed -i 's|postgresql+asyncpg://.*|sqlite+aiosqlite:///./cypherpilot.db|' .env
    sed -i 's|postgresql://.*|sqlite:///./cypherpilot.db|' .env
    log_ok ".env created with SQLite"
  else
    log_info ".env already exists, keeping it"
  fi

  log_info "Running database migrations..."
  # Activate venv and run migrations
  source "$INSTALL_DIR/.venv/bin/activate"
  cd "$INSTALL_DIR"
  alembic upgrade head 2>&1
  log_ok "Database ready"

  # ── Step 6: Create shell alias ────────────────────────────────────────────
  log_step "Creating 'cypherpilot' command"

  ALIAS_LINE="alias cypherpilot='cd $INSTALL_DIR && source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'"
  UNINSTALL_LINE="alias cypherpilot-uninstall='cd $INSTALL_DIR && bash scripts/install.sh uninstall'"

  # Detect shell profile
  SHELL_PROFILE=""
  if [ -n "${ZSH_VERSION-}" ]; then
    SHELL_PROFILE="${HOME}/.zshrc"
  elif [ -n "${BASH_VERSION-}" ]; then
    if [ -f "${HOME}/.bashrc" ]; then
      SHELL_PROFILE="${HOME}/.bashrc"
    elif [ -f "${HOME}/.bash_profile" ]; then
      SHELL_PROFILE="${HOME}/.bash_profile"
    fi
  fi

  if [ -n "$SHELL_PROFILE" ] && [ -f "$SHELL_PROFILE" ]; then
    # Remove old cypherpilot aliases if present
    sed -i '/^alias cypherpilot=/d' "$SHELL_PROFILE" 2>/dev/null || true
    sed -i '/^alias cypherpilot-uninstall=/d' "$SHELL_PROFILE" 2>/dev/null || true

    echo "$ALIAS_LINE" >> "$SHELL_PROFILE"
    echo "$UNINSTALL_LINE" >> "$SHELL_PROFILE"
    log_ok "Aliases added to $SHELL_PROFILE"
  else
    log_warn "Could not detect shell profile. Add this alias manually:"
    echo ""
    echo "  $ALIAS_LINE"
    echo ""
  fi

  # Also create a convenience script in PATH-friendly location
  cat > "$INSTALL_DIR/cypherpilot.sh" << 'SCRIPT'
#!/usr/bin/env bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
SCRIPT
  chmod +x "$INSTALL_DIR/cypherpilot.sh"
  log_ok "Start script created at $INSTALL_DIR/cypherpilot.sh"

  # ── Summary ──────────────────────────────────────────────────────────────
  echo ""
  echo "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
  echo "${BOLD}║          CypherPilot v${CYPHERPILOT_VERSION} installed!           ║${NC}"
  echo "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
  echo ""
  echo "  ${BOLD}Install path:${NC}     $INSTALL_DIR"
  echo "  ${BOLD}Python venv:${NC}      $INSTALL_DIR/.venv"
  echo "  ${BOLD}Config:${NC}           $INSTALL_DIR/.env"
  echo ""
  echo "  ${BOLD}Quick start:${NC}"
  echo "    cd $INSTALL_DIR && source .venv/bin/activate"
  echo "    uvicorn app.main:app --host 0.0.0.0 --port 8000"
  echo ""
  echo "    Or use the alias:  ${BOLD}cypherpilot${NC}"
  echo ""
  echo "  ${BOLD}Open in browser:${NC}  http://localhost:8000"
  echo "  ${BOLD}API docs:${NC}         http://localhost:8000/docs"
  echo ""
  echo "  ${BOLD}To uninstall:${NC}     bash $INSTALL_DIR/scripts/install.sh uninstall"
  echo "                    or  ${BOLD}cypherpilot-uninstall${NC}"
  echo ""
}

# ── Uninstall ────────────────────────────────────────────────────────────────

do_uninstall() {
  echo ""
  echo "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
  echo "${BOLD}║         CypherPilot — Uninstall                       ║${NC}"
  echo "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
  echo ""

  if [ ! -d "$INSTALL_DIR" ]; then
    log_warn "No installation found at $INSTALL_DIR"
    exit 0
  fi

  # ── Remove shell aliases ─────────────────────────────────────────────────
  log_step "Removing shell aliases"

  for profile in "${HOME}/.zshrc" "${HOME}/.bashrc" "${HOME}/.bash_profile"; do
    if [ -f "$profile" ]; then
      sed -i '/^alias cypherpilot=/d' "$profile" 2>/dev/null || true
      sed -i '/^alias cypherpilot-uninstall=/d' "$profile" 2>/dev/null || true
      log_ok "Cleaned aliases from $profile"
    fi
  done

  # ── Remove installed files ───────────────────────────────────────────────
  log_step "Removing installed files"
  log_info "Removing $INSTALL_DIR ..."

  # Confirm
  printf "  Remove everything under ${BOLD}%s${NC}? [y/N] " "$INSTALL_DIR"
  read -r confirm
  if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log_warn "Uninstall cancelled."
    exit 0
  fi

  rm -rf "$INSTALL_DIR"
  log_ok "Removed $INSTALL_DIR"

  # ── Verify nothing left ──────────────────────────────────────────────────
  log_step "Verifying clean removal"
  local leftovers=false

  if [ -d "$INSTALL_DIR" ]; then
    log_error "Directory still exists: $INSTALL_DIR"
    leftovers=true
  fi

  # Check for stray processes
  if pgrep -f "uvicorn.*app.main" &>/dev/null 2>&1; then
    log_warn "A CypherPilot process may still be running."
    log_info "Stop it with: pkill -f 'uvicorn.*app.main'"
    leftovers=true
  fi

  if [ "$leftovers" = false ]; then
    echo ""
    echo "${GREEN}  ✓ CypherPilot has been completely removed.${NC}"
    echo ""
  else
    echo ""
    log_warn "Some items may need manual cleanup."
    echo ""
  fi
}

# ── Main ─────────────────────────────────────────────────────────────────────

case "${1:-install}" in
  install|--install)
    do_install
    ;;
  uninstall|--uninstall|remove|--remove)
    do_uninstall
    ;;
  *)
    echo "Usage: bash install.sh [install|uninstall]"
    echo ""
    echo "  install   (default) Install CypherPilot"
    echo "  uninstall           Remove CypherPilot completely"
    exit 1
    ;;
esac
