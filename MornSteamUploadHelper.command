#!/bin/bash
cd "$(dirname "$0")"
# Set environment variable before Python starts
export SYSTEM_VERSION_COMPAT=0
exec python3 src/main.py