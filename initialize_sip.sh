#!/bin/bash

# ============================================================
# SOVEREIGN INTELLIGENCE PROTOCOL (S.I.P.) - v4.2.1
# Railway Deployment & M2M Extraction Engine
# ============================================================

usage() {
    echo "Usage: $0 --keys FROM_ENV --pulse RAILWAY_90S"
    exit 1
}

# Parse command-line arguments
KEYS_FROM_ENV=false
PULSE_RAILWAY_90S=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --keys) [[ "$2" == "FROM_ENV" ]] && KEYS_FROM_ENV=true && shift ;;
        --pulse) [[ "$2" == "RAILWAY_90S" ]] && PULSE_RAILWAY_90S=true && shift ;;
        *) usage ;;
    esac
    shift
done

if ! $KEYS_FROM_ENV || ! $PULSE_RAILWAY_90S; then usage; fi

echo "--- [S.I.P. INITIALIZATION START] ---"

# Safety Check: Ensure the critical recovery address is set in Railway Variables
if [ -z "$RECOVERY_ID" ]; then
    echo "CRITICAL ERROR: RECOVERY_ID not found in Railway Variables. System aborting to prevent loss."
    exit 1
fi

# Configure S.I.P. Runtime Parameters
export SIP_PULSE_90S=90
export SIP_SLEEP_4_5M=270
export SIP_WEBSOCKET_URL="wss://api-m2m.gateway.v4/live"
export SIP_AUTONOMY_LEVEL=1.0

echo "Environment: RAILWAY_CLOUD"
echo "Pulse Logic: 90s Scrape / 4.5m Stealth"
echo "Recovery ID: ${RECOVERY_ID:0:6}********" # Masked for security logs
echo "--- [S.I.P. INITIALIZATION COMPLETE] ---"

# EXECUTION LAYER: Launching the Autonomous Agent
# In 2026, we use 'unbuffered' python output to ensure logs appear in Railway in real-time.
python3 -u main.py
