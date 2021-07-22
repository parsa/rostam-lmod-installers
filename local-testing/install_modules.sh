#!/usr/bin/env bash

set -euxo pipefail

################################################################################
# Install Prerequisites - Debian (docker run -it --rm debian)
################################################################################
apt-get update && apt-get install -y g++ make wget tcl-dev procps less gettext

################################################################################
# Install Modules - https://modules.readthedocs.io/en/stable/INSTALL.html
################################################################################
export MODULES_VERSION=4.8.0
wget https://sourceforge.net/projects/modules/files/Modules/modules-${MODULES_VERSION}/modules-${MODULES_VERSION}.tar.gz
tar xf modules-${MODULES_VERSION}.tar.gz
(
  cd modules-${MODULES_VERSION}/
  ./configure
  make -j install
)
rm -rf modules-${MODULES_VERSION} modules-${MODULES_VERSION}.tar.gz
echo source /usr/local/Modules/init/bash >>~/.bashrc
echo source /usr/local/Modules/init/bash_completion >>~/.bashrc

mkdir -p $HOME/.local/modules
echo module use $HOME/.local/modules >>~/.bashrc
