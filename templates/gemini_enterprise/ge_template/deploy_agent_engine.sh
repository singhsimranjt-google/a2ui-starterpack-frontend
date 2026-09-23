#!/usr/bin/env bash
#
# Deploy this A2UI agent to Vertex AI Agent Engine.
#
#   ./deploy_agent_engine.sh              # deploy (or update if AGENT_ENGINE_ID is set)
#   ./deploy_agent_engine.sh --new        # force-create a brand new instance
#
# Configuration is read from .env. Nothing secret is hardcoded here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'; BOLD=$'\033[1m';    NC=$'\033[0m'

info()  { echo "${BLUE}==>${NC} $*"; }
ok()    { echo "${GREEN}  ✓${NC} $*"; }
warn()  { echo "${YELLOW}  !${NC} $*"; }
die()   { echo "${RED}  ✗ $*${NC}" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1. Load .env
# ---------------------------------------------------------------------------
if [[ -f .env ]]; then
  set -a; source .env; set +a
  ok "Loaded .env"
else
  warn "No .env found - relying on the current shell environment"
fi

FORCE_NEW=false
[[ "${1:-}" == "--new" ]] && FORCE_NEW=true

# ---------------------------------------------------------------------------
# 2. Locate the agent directory (must contain agent.py defining root_agent/app)
# ---------------------------------------------------------------------------
AGENT_DIR="${AGENT_DIR:-}"
if [[ -z "$AGENT_DIR" ]]; then
  for candidate in src app agent .; do
    if [[ -f "$candidate/agent.py" ]]; then AGENT_DIR="$candidate"; break; fi
  done
fi
[[ -n "$AGENT_DIR" && -f "$AGENT_DIR/agent.py" ]] \
  || die "Could not find an agent directory containing agent.py. Set AGENT_DIR in .env."
ok "Agent directory: ${BOLD}${AGENT_DIR}${NC}"

# ADK stages only the agent directory. requirements.txt must live inside it.
if [[ ! -f "$AGENT_DIR/requirements.txt" && -f requirements.txt ]]; then
  cp requirements.txt "$AGENT_DIR/requirements.txt"
  ok "Copied requirements.txt into ${AGENT_DIR}/ for staging"
fi

# ---------------------------------------------------------------------------
# 3. Tooling
# ---------------------------------------------------------------------------
command -v uv >/dev/null 2>&1 || die "uv not found. https://astral.sh/uv"
ADK=(uv run adk)
"${ADK[@]}" --version >/dev/null 2>&1 || die "adk CLI unavailable. Run: uv sync"
ok "adk CLI ready"

# ---------------------------------------------------------------------------
# 4. Resolve auth mode
# ---------------------------------------------------------------------------
USE_VERTEX="$(echo "${GOOGLE_GENAI_USE_VERTEXAI:-false}" | tr '[:upper:]' '[:lower:]')"
DEPLOY_ARGS=()

if [[ "$USE_VERTEX" == "true" || "$USE_VERTEX" == "1" || "$USE_VERTEX" == "yes" ]]; then
  # --- Vertex AI / Argolis (ADC) --------------------------------------------
  [[ -n "${GOOGLE_CLOUD_PROJECT:-}" ]]  || die "GOOGLE_CLOUD_PROJECT is not set in .env"
  GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

  command -v gcloud >/dev/null 2>&1 || die "gcloud not found. https://cloud.google.com/sdk"

  if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
    warn "No Application Default Credentials found."
    read -r -p "    Run 'gcloud auth application-default login' now? [Y/n] " reply
    if [[ ! "$reply" =~ ^[Nn]$ ]]; then
      gcloud auth application-default login
      gcloud auth application-default set-quota-project "$GOOGLE_CLOUD_PROJECT"
    else
      die "ADC is required for Vertex deployment."
    fi
  fi
  ok "ADC active"

  info "Enabling required APIs (idempotent)..."
  gcloud services enable aiplatform.googleapis.com cloudbuild.googleapis.com \
      storage.googleapis.com --project "$GOOGLE_CLOUD_PROJECT" --quiet \
    || warn "Could not enable APIs - continuing (they may already be on)"

  DEPLOY_ARGS+=(--project "$GOOGLE_CLOUD_PROJECT" --region "$GOOGLE_CLOUD_LOCATION")
  echo "    Project : ${BOLD}${GOOGLE_CLOUD_PROJECT}${NC}"
  echo "    Region  : ${BOLD}${GOOGLE_CLOUD_LOCATION}${NC}"

else
  # --- Express mode (API key) -----------------------------------------------
  API_KEY="${GOOGLE_API_KEY:-${GEMINI_API_KEY:-}}"
  [[ -n "$API_KEY" ]] || die "Set GEMINI_API_KEY, or set GOOGLE_GENAI_USE_VERTEXAI=true for Vertex."
  DEPLOY_ARGS+=(--api_key "$API_KEY")
  warn "Express mode (API key). Vertex/Argolis is recommended for production."
fi

# ---------------------------------------------------------------------------
# 5. Naming + update-vs-create
# ---------------------------------------------------------------------------
DISPLAY_NAME="${AGENT_DISPLAY_NAME:-$(basename "$(pwd)")}"
DESCRIPTION="${AGENT_DESCRIPTION:-A2UI agent deployed from the adk-a2ui starter pack}"
DEPLOY_ARGS+=(--display_name "$DISPLAY_NAME" --description "$DESCRIPTION")

if [[ -n "${AGENT_ENGINE_ID:-}" && "$FORCE_NEW" == "false" ]]; then
  DEPLOY_ARGS+=(--agent_engine_id "$AGENT_ENGINE_ID")
  info "Updating existing Agent Engine instance: ${BOLD}${AGENT_ENGINE_ID}${NC}"
else
  info "Creating a new Agent Engine instance"
fi

# ---------------------------------------------------------------------------
# 6. Deploy
# ---------------------------------------------------------------------------
echo
info "Deploying ${BOLD}${DISPLAY_NAME}${NC} to Agent Engine (this can take 5-10 minutes)..."
echo

LOG="$(mktemp)"
trap 'rm -f "$LOG"' EXIT

set +e
"${ADK[@]}" deploy agent_engine "${DEPLOY_ARGS[@]}" "$AGENT_DIR" 2>&1 | tee "$LOG"
STATUS=${PIPESTATUS[0]}
set -e

[[ $STATUS -eq 0 ]] || die "Deployment failed (exit $STATUS). See the output above."

# ---------------------------------------------------------------------------
# 7. Capture the resource name so the next run updates instead of duplicating
# ---------------------------------------------------------------------------
RESOURCE="$(grep -oE 'projects/[^/]+/locations/[^/]+/reasoningEngines/[0-9]+' "$LOG" | tail -1 || true)"

echo
if [[ -n "$RESOURCE" ]]; then
  NEW_ID="${RESOURCE##*/}"
  ok "Deployed: ${BOLD}${RESOURCE}${NC}"

  if [[ -f .env ]] && ! grep -q '^AGENT_ENGINE_ID=' .env; then
    printf '\n# Written by deploy_agent_engine.sh - reuse this instance on redeploy\nAGENT_ENGINE_ID=%s\n' "$NEW_ID" >> .env
    ok "Saved AGENT_ENGINE_ID=${NEW_ID} to .env"
  fi

  echo
  echo "${BOLD}Next: register in Gemini Enterprise${NC}"
  echo "  1. Open  https://console.cloud.google.com/gen-app-builder"
  echo "  2. Your app  ->  Agents  ->  Add agent  ->  Agent Engine"
  echo "  3. Paste:  ${RESOURCE}"
else
  warn "Deployment reported success but no resource name was parsed."
  warn "Find it with: gcloud ai reasoning-engines list --region=\${GOOGLE_CLOUD_LOCATION}"
fi
