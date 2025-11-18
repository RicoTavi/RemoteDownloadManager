#!/bin/bash
# Quick install for Python deps (ADHD-friendly version)

echo "🚀 Installing Python packages..."
echo ""

pip3 install --user --break-system-packages paramiko rich

echo ""
echo "✅ Done! Now run: python3 download-manager.py"
