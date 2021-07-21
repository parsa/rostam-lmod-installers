#!/usr/bin/env bash
cd "$( dirname "${BASH_SOURCE[0]}" )"

set -ex

export RUBY_VERSION=2.7.1
export ARCHIVE_NAME=ruby-${RUBY_VERSION}.tar.gz
export DIR_INSTALL=${HOME}/.local/ruby/${RUBY_VERSION}
export FILE_MODULE=${HOME}/.local/modules/ruby/${RUBY_VERSION}

[[ ! -d ${DIR_INSTALL} ]] && mkdir -p ${DIR_INSTALL}

curl -JLO https://cache.ruby-lang.org/pub/ruby/${RUBY_VERSION%.*}/${ARCHIVE_NAME}
tar xf ${ARCHIVE_NAME}
(
  cd ruby-${RUBY_VERSION}
  ./configure --prefix=${DIR_INSTALL}
  make install -j10
)
rm -f ./${ARCHIVE_NAME}
rm -rf ruby-${RUBY_VERSION}

mkdir -p $(dirname ${FILE_MODULE})
cat >${FILE_MODULE} <<EOF
#%Module
proc ModulesHelp { } {
  puts stderr {Ruby ${RUBY_VERSION}}
}
module-whatis {Ruby ${RUBY_VERSION}}
set root    ${DIR_INSTALL}
conflict    ruby
prepend-path    LD_LIBRARY_PATH \$root/lib
prepend-path    LIBRARY_PATH    \$root/lib
prepend-path    MANPATH         \$root/share/man
prepend-path    CPATH           \$root/include
prepend-path    PATH            \$root/bin
EOF
