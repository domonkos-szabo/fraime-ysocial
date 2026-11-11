#!/bin/sh
set -eu
PLUGIN_DIR=/data/external/YPhotoSharing
# User-installed plugins are already under the persistent /data volume.
# Seed only on a clean volume, never overwrite an existing installation.
if [ ! -f "$PLUGIN_DIR/run_client.py" ]; then
  mkdir -p /data/external
  cp -a /opt/fraime-plugins/YPhotoSharing "$PLUGIN_DIR"
fi
exec /usr/local/bin/ysocial-entrypoint "$@"
