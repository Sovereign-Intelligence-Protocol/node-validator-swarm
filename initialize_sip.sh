#!/bin/bash

# This script initializes the Sovereign Intelligence Protocol (S.I.P.) environment.
# It sources the Railway .env file and sets up SIP-specific configurations.

# Function to display usage
usage() {
    echo "Usage: $0 --keys FROM_ENV --pulse RAILWAY_90S"
    echo "  --keys FROM_ENV: Indicates that API keys should be pulled from environment variables."
    echo "  --pulse RAILWAY_90S: Configures the SIP pulse for Railway deployment (90s pulse, 4.5m sleep)."
    exit 1
}

# Parse command-line arguments
KEYS_FROM_ENV=false
PULSE_RAILWAY_90S=false

while [[ "$#" -gt 0 ]]; do
    key="$1"
    case $key in
        --keys)
        if [[ "$2" == "FROM_ENV" ]]; then
            KEYS_FROM_ENV=true
            shift
        else
            usage
        fi
        ;;
        --pulse)
        if [[ "$2" == "RAILWAY_90S" ]]; then
            PULSE_RAILWAY_90S=true
            shift
        else
            usage
        fi
        ;;
        *)
        usage
        ;;
    esac
    shift
done

# Ensure required arguments are provided
if ! $KEYS_FROM_ENV || ! $PULSE_RAILWAY_90S; then
    usage
fi

echo "Initializing Sovereign Intelligence Protocol (S.I.P.) environment..."

# Source Railway .env file if it exists (assuming it's in /app/.env for Railway deployments)
if [ -f "/app/.env" ]; then
    echo "Sourcing /app/.env for Railway environment variables."
    source /app/.env
else
    echo "Warning: /app/.env not found. Ensure environment variables are set."
fi

# Set SIP-specific environment variables based on --pulse RAILWAY_90S
if $PULSE_RAILWAY_90S; then
    echo "Configuring SIP for Railway 90s pulse."
    export SIP_PULSE_90S=90
    export SIP_SLEEP_4_5M=270
    export SIP_WEBSOCKET_URL="wss://api-m2m.gateway.v4/live"
    export SIP_RECOVERY_ID="USER_HARDCODED_ID_001" # This should ideally come from Railway secrets
    export SIP_AUTONOMY_LEVEL=1.0
fi

echo "S.I.P. environment setup complete."

# Example of how to run the main application after setup
# python main.py
