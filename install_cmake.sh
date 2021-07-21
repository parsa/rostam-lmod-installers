#!/usr/bin/env bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

set -ex

latest_cmake_version()
{
  local latest_json=$(curl -JL https://cmake.org/files/LatestRelease/cmake-latest-files-v1.json)
  #local jq_query='.files[] | select((.class=="installer") and (.architecture[] | contains("x86_64")) and (.os[] | contains("linux"))).name'
  local jq_query='.version.string'
  jq -r "$jq_query" <<<"$latest_json"
}

export CMAKE_VERSION=$(latest_cmake_version)
#export CMAKE_VERSION=3.20.1
export TARBALL_NAME=cmake-${CMAKE_VERSION}-linux-x86_64.sh
export DIR_INSTALL=${HOME}/.local/cmake/${CMAKE_VERSION}
export FILE_MODULE=${HOME}/.local/modules/cmake/${CMAKE_VERSION}

[[ ! -d ${DIR_INSTALL} ]] && mkdir -p ${DIR_INSTALL}

#curl -JLO https://cmake.org/files/v${CMAKE_VERSION%.*}/${TARBALL_NAME}
curl -JLO https://github.com/Kitware/CMake/releases/download/v${CMAKE_VERSION}/${TARBALL_NAME}
sh ./${TARBALL_NAME} --prefix=${DIR_INSTALL} --exclude-subdir
rm -f ./${TARBALL_NAME}

mkdir -p $(dirname ${FILE_MODULE})
cat >${FILE_MODULE} <<EOF
#%Module
proc ModulesHelp { } {
  puts stderr {CMake ${CMAKE_VERSION}}
}
module-whatis {CMake ${CMAKE_VERSION}}
set root    ${DIR_INSTALL}
conflict    cmake
prepend-path    MANPATH         \$root/man
prepend-path    PATH            \$root/bin
prepend-path    ACLOCAL_PATH    \$root/share/aclocal
setenv          CMAKE_COMMAND   \$root/bin/cmake
setenv          CMAKE_VERSION   ${CMAKE_VERSION}
EOF
