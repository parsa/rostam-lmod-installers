#!/usr/bin/env python3

from genericpath import isdir
import os
import subprocess
import shutil
import sys
import textwrap

# Parameters {{{ #
script_name = os.path.basename(__file__)

repo_url="https://github.com/STEllAR-GROUP/hpx.git"
boost_install_dir="/opt/boost/1.60.0-debug"

CONFIG="Debug" # Debug Release MinSizeRel RelWithDebInfo

hpx_run_options="--hpx:threads 4"
performance_counter_flags =  ' '.join([
    '--hpx:print-counter=/agas{locality#0/total}/count/resolve_locality',
    '--hpx:print-counter=/agas{locality#*/total}/count/bind_gid',
    '--hpx:print-counter=/agas{locality#*/total}/count/bind',
    '--hpx:print-counter=/agas{locality#0/total}/time/resolved_localities',
    ])
# }}} Parameters #

# Internals {{{ #
script_dir=os.path.dirname(__file__)

## Set fonts for Help.
#__NORM=$(tput sgr0)
#__BOLD=$(tput bold)
#__REV=$(tput smso)

function print_usage {
    cat <<EOT

Synopsis
    $script_name [OPTION]... [ARGUMENTS]
    Perform the operation selected via options (see below) on HPX

    -p       Perform a "git pull" on "repo"
    -c       Clean. Perform "rm -rf build/*".
    -i       Create the directory structure in the specified directory and
             clone HPX.
    -q       Build Quick Start examples.
    -g       Run CMake if CMake Cache doesn't exist and build HPX.
    -m       Build HPX.
    -r       Run the HPX application.
    \?       Prints this message.
EOT
}

def get_paths():
    base = f"{argv[1]:-"{script_dir}"}"
    repo_path=f"{base}/repo"
    build_path=f"{base}/build"
    bin_path="f{base}/build/bin"

def git_pull():
    assert os.path.isdir(repo_path), f"Pull: Cannot find the repository at "{repo_path}."
    print(f"{repo_path}"
    subprocess.run(["git", "pull"], check=True)
    #popd
    

def clean():
    if os.path.isdir(build_path):
        shutil.rmtree(build_path, ignore_errors=True)

def run_make(arg1, *args):
    # pushd "${__BUILD_PATH}"
    subprocess.run(["make", arg1, "-k", "-j", os.cpu_count(), *args], check=True)
    # popd

def check_run_cinit():
    if not os.isdir(repo_path):
        print(f"CMake: Cannot find the repository at \"{repo_path}\".", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(build_path):
        os.makedirs(build_path, exist_ok=True)

        # pushd "${__BUILD_PATH}"

        # Boost
        #   BOOST_SUFFIX="-il-mt-1_51"
        #   BOOST_ROOT=$WORK/boost/install

        # jemalloc
        #   HPX_MALLOC=“jemalloc”
        #   JEMALLOC_ROOT=/some/path
        #   Cmalloc
        #   HPX_MALLOC=“tcmalloc”
        #   TCMALLOC_ROOT=/some/path

        # Clang
        #   CMAKE_CXX_COMPILER=clang++

        # Misc
        #-DHPX_HAVE_VERIFY_LOCKS=True
        #-Wdev

        local cmake_args=$(cat <<-EOT
            -DHPX_NO_INSTALL=On
            -DBOOST_ROOT=${BOOST_INST}
            -DCMAKE_BUILD_TYPE=${CONFIG}
            -DHPX_HAVE_PARCELPORT_MPI=True
            -DHPX_MALLOC=custom
            ${__REPO_PATH}
        EOT
        )
        echo "cmake" ${cmake_args}
        cmake ${cmake_args}

        spopd
    fi

    run_make()

function run_app {
    local cmd="${__BIN_PATH}/${1}" ${HPX_OPTS} ${PFX_COUNTERS}
    echo $cmd
    $cmd
}

#BOOST: build_boost.sh –v 1.52.0 –d boost_1.52.0

get_paths

#CC=clang
#CXX=clang++
#CC=$ICC_BIN/icc
#CXX=$ICC_BIN/icpc

function init_repo {
    if [[ -d "${__REPO_PATH}/.git" ]]; then
        echorr "Repository already exists"
        return
    fi

    # Repository folder path
    __BASE_PATH="${1}"
    if [[ X"${__BASE_PATH}" == "X" ]]; then
        read -p 'Enter the path to the desired working directory: ' -r __BASE_PATH
        echo
    fi

    get_paths "${__BASE_PATH}"
    echo "mkdir -p ${__REPO_PATH}"
    mkdir -p "${__REPO_PATH}"
    echo "cp ${__SCRIPT_PATH} ${__BASE_PATH}"
    cp "${__SCRIPT_PATH}" "${__BASE_PATH}"
    echo "git clone ${REPO_URL} ${__REPO_PATH}"
    git clone "${REPO_URL}" "${__REPO_PATH}"

    if [[ "${__MAKE:-x}" == "x" ]]; then
        read -p "Do you wish to compile HPX as well? [y] " -n 1 -s -r
        echo

        spushd "${__BASE_PATH}"

        if [[ "${REPLY:-y}" =~ ^[Yy]$ ]]; then
            __MAKE=
        fi
    fi
}
# }}} Internals #

# Handle options {{{ #
while getopts "pcqimrg" opt; do
    case "${opt}" in
        # pull
        p  ) __PULL=$OPTARG ;;

        # clean
        c  ) __CLEAN=$OPTARG ;;

        # init
        i  ) __INIT=$OPTARG ;;

        # quickstart
        q  ) __QUICKSTART=$OPTARG ;;

        # configure
        g  ) __CONFIGURE=$OPTARG ;;

        # make
        m  ) __MAKE=$OPTARG ;;

        # run
        r  ) __RUN=$OPTARG ;;

        # help
        h  )
            print_usage
            exit 1;;

        # pull
        \? )
            echorr -e "\n  Option does not exist : -$OPTARG\n"
            print_usage
            exit 1
            ;;
    esac
done
shift $(( $OPTIND-1 ))
# }}} Handle options #

# Git Pull
[[ -n "${__PULL+x}" ]] && git_pull
# Clean
[[ -n "${__CLEAN+x}" ]] && clean
# Git Clone
if [[ -n "${__INIT+x}" ]]; then
    init_repo "${1}"
    shift
fi
[[ -n "${__QUICKSTART+x}" ]] && TARGET="examples.quickstart"
# CMake
[[ -n "${__CONFIGURE+x}" ]] && check_run_cinit
# Build
if [[ -n "${__MAKE+x}" ]]; then
    run_make "${TARGET:-"${1}"}"
    shift
fi
# Run
[[ -n "${__RUN+x}" ]] && run_app "${1}" "${@:2}"
{"mode":"full","isActive":false}
