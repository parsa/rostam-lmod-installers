#!/usr/bin/env bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

set -euxo pipefail

latest_ninja_version()
{
  local latest_html=$(curl -JL 'https://github.com/ninja-build/ninja/releases/latest')
  grep -Po '(?<=v)([0-9]+\.){1,}[0-9]+(?=/ninja-linux.zip)' <<<"$latest_html"
}

export NINJA_VERSION=1.10.2
export ARCHIVE_NAME=ninja-linux.zip
export DIR_INSTALL=${HOME}/.local/ninja/${NINJA_VERSION}
export FILE_MODULE=${HOME}/.local/modules/ninja/${NINJA_VERSION}

[[ ! -d ${DIR_INSTALL} ]] && mkdir -p ${DIR_INSTALL}

(
    cd ${DIR_INSTALL}
    curl -JLO https://github.com/ninja-build/ninja/releases/download/v${NINJA_VERSION}/${ARCHIVE_NAME}
    unzip ./${ARCHIVE_NAME}
    rm -f ./${ARCHIVE_NAME}
)

mkdir -p $(dirname ${FILE_MODULE})
cat >${FILE_MODULE} <<EOF
#%Module
proc ModulesHelp { } {
  puts stderr {Ninja ${NINJA_VERSION}}
}
module-whatis {Ninja ${NINJA_VERSION}}
set root    ${DIR_INSTALL}
conflict    ninja
prepend-path    PATH            \$root
EOF
