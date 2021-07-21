#!/usr/bin/env bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

set -euxo pipefail

latest_gnu_parallel_version()
{
  local latest_html=$(curl -JL https://ftp.gnu.org/gnu/parallel/)
  local all_versions=$(grep -Po '(?<=parallel-).[0-9.]+(?=.tar.bz2)' <<<"$latest_html")
  echo "$all_versions" | sort -rV | head -1
}

#export PARALLEL_VERSION=20201222
export PARALLEL_VERSION=$(latest_gnu_parallel_version)
export TARBALL_NAME=parallel-${PARALLEL_VERSION}.tar.bz2
export DIR_INSTALL=${HOME}/.local/parallel/${PARALLEL_VERSION}
export FILE_MODULE=${HOME}/.local/modules/parallel/${PARALLEL_VERSION}

[[ ! -d ${DIR_INSTALL} ]] && mkdir -p ${DIR_INSTALL}

curl -JLO https://ftp.gnu.org/gnu/parallel/${TARBALL_NAME}
tar xf ${TARBALL_NAME}
(
  cd parallel-${PARALLEL_VERSION}
  ./configure --prefix=${DIR_INSTALL}
  make install
)
rm -f ./${TARBALL_NAME}
rm -rf parallel-${PARALLEL_VERSION}

mkdir -p $(dirname ${FILE_MODULE})
cat >${FILE_MODULE} <<EOF
#%Module
proc ModulesHelp { } {
  puts stderr {GNU Parallel ${PARALLEL_VERSION}}
}
module-whatis {GNU Parallel ${PARALLEL_VERSION}}
set root    ${DIR_INSTALL}
conflict    parallel
prepend-path    MANPATH         \$root/share/man
prepend-path    PATH            \$root/bin

EOF
