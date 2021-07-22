#!/usr/bin/env bash

set -euxo pipefail

pip3 list --outdated --format=freeze | cut -d= -f1 | xargs -n1 pip3 install --upgrade
