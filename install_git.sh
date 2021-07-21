#!/usr/bin/env bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

set -euxo pipefail

latest_git_version()
{
  local latest_html=$(curl -JL https://mirrors.edge.kernel.org/pub/software/scm/git/)
  local all_versions=$(grep -Po '(?<=git-).[0-9.]*(?=.tar.gz)' <<<"$latest_html")
  echo "$all_versions" | sort -rV | head -1
}

#export GIT_VERSION=2.30.0
export GIT_VERSION=$(latest_git_version)
export ARCHIVE_NAME=git-${GIT_VERSION}.tar.xz
export DIR_INSTALL=${HOME}/.local/git/${GIT_VERSION}
export FILE_MODULE=${HOME}/.local/modules/git/${GIT_VERSION}

[[ ! -d ${DIR_INSTALL} ]] && mkdir -p ${DIR_INSTALL}

curl -JLO https://mirrors.edge.kernel.org/pub/software/scm/git/${ARCHIVE_NAME}
tar xf ${ARCHIVE_NAME}
(
  cd git-${GIT_VERSION}
  ./configure --prefix=${DIR_INSTALL} --with-editor=vim
  make install -j10
)
rm -f ./${ARCHIVE_NAME}
rm -rf git-${GIT_VERSION}

mkdir -p $(dirname ${FILE_MODULE})
cat >${FILE_MODULE} <<EOF
#%Module
proc ModulesHelp { } {
  puts stderr {Git ${GIT_VERSION}}
}
module-whatis {Git ${GIT_VERSION}}
set root    ${DIR_INSTALL}
conflict    git
prepend-path    LD_LIBRARY_PATH \$root/lib64
prepend-path    LIBRARY_PATH    \$root/lib64
prepend-path    MANPATH         \$root/share/man
prepend-path    PATH            \$root/bin
EOF
