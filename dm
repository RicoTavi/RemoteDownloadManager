#!/bin/bash
# Quick launcher for download-manager.py
cd "$(dirname "$0")"
python3 download-manager.py "$@"
