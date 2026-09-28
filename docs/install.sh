#!/bin/sh
set -e

echo "🦆 Installing Astral uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Inject the default uv install paths into the current script session
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "🦆 Installing Posthorn..."
uv tool install --force posthorn

echo "🦆 Validating installation..."
if command -v posthorn >/dev/null 2>&1; then
    echo "✨ All done! Run 'posthorn' to launch the daemon."
else
    echo "⚠️ Installation finished, but you may need to restart your terminal before running 'posthorn'."
fi
