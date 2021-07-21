#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import urllib.parse
import urllib.request


def query_cmake_org_latest_files(cmake_org_files_json):
    release_info = json.load(urllib.request.urlopen(cmake_org_files_json))
    installer_query = list(
        filter(
            lambda i: os.uname().sysname in i['os'] and os.uname(
            ).machine in i['architecture'] and i['class'] == 'installer',
            release_info['files']))
    assert len(installer_query
               ) == 1, "There should be exactly one CMake installer file."
    installer_info = installer_query[0]
    installer_name = installer_info['name']
    cmake_version = release_info['version']['string']
    return installer_name, cmake_version


def download_check_installer(installer_url, installer_name):
    # Download the installer
    http_result = urllib.request.urlretrieve(installer_url, installer_name)
    assert http_result[
        0] == installer_name, f'Failed to download {installer_name} from "{installer_url}".'

    # Assert that the installer file exists
    assert os.path.isfile(
        installer_name
    ), f'CMake installer file {installer_name} does not exist.'
    # Assert that the installer file is larger than 5 MB
    assert os.path.getsize(installer_name) > 5 * \
        2**20, f'CMake installer file {installer_name} is less than 5 MB.'


def install_check_cmake(installer_name, cmake_version, dir_install):
    # Create the directory hierarchy if necessary
    os.makedirs(dir_install, exist_ok=True)

    # Run the installer
    install_proc = subprocess.run(
        ['sh', installer_name, f'--prefix={dir_install}', '--exclude-subdir'],
        capture_output=True,
        text=True)

    assert install_proc.returncode == 0, install_proc.stderr
    assert 'Unpacking finished successfully' in install_proc.stdout, install_proc.stdout
    assert cmake_version in install_proc.stdout, install_proc.stdout
    assert dir_install in install_proc.stdout, install_proc.stdout

    # Assert that the installed CMake file exists.
    cmake_executable = os.path.join(dir_install, 'bin', 'cmake')
    assert os.path.isfile(
        cmake_executable
    ), f'CMake executable {cmake_executable} does not exist.'

    # Assert that the installed CMake works with its absolute path.
    cmake_proc = subprocess.run([cmake_executable, '--version'],
                                capture_output=True,
                                text=True)
    assert cmake_proc.returncode == 0, cmake_proc.stderr
    assert cmake_version in cmake_proc.stdout
    return cmake_executable


# Create an Lmod module file
def create_check_modulefile(module_base, cmake_version, dir_install):
    module_name = os.path.join('cmake', cmake_version)
    # Create an Lmod module file
    module_file = os.path.join(module_base, module_name)
    module_file_content = f'''#%Module
    proc ModulesHelp {{ }} {{
      puts stderr {{CMake {cmake_version}}}
    }}
    module-whatis {{CMake {cmake_version}}}
    set root    {dir_install}
    conflict    cmake
    prepend-path    MANPATH         $root/man
    prepend-path    PATH            $root/bin
    prepend-path    ACLOCAL_PATH    $root/share/aclocal
    setenv          CMAKE_COMMAND   $root/bin/cmake
    setenv          CMAKE_VERSION   {cmake_version}'''

    with open(module_file, 'w') as fh:
        fh.write(module_file_content)

    # Make sure the Lmod can load the module
    lmod_proc = subprocess.run(f'module show cmake/{cmake_version}',
                               shell=True,
                               capture_output=True,
                               text=True,
                               env=dict(os.environ, LMOD_PAGER=''))
    assert lmod_proc.returncode == 0, 'Lmod failed to load the module'
    assert module_file in lmod_proc.stderr, 'Lmod failed to load the module'

    return module_name


def check_module(module_name, cmake_version, cmake_executable):
    # Make sure the correct CMake executable is in the path.
    cmake_proc = subprocess.run(f'module load {module_name} && which cmake',
                                shell=True,
                                capture_output=True,
                                text=True,
                                env=dict(os.environ, LMOD_PAGER=''))
    assert cmake_proc.returncode == 0, 'CMake executable is not in the PATH set by the Lmod modulefile.'
    assert os.path.samefile(
        cmake_proc.stdout.rstrip(), cmake_executable
    ), f'CMake executable loaded by Lmod is not the expected {cmake_version} verison. {cmake_proc.stdout}'

    # Make sure the CMake executable is in the path works and is the version we expected.
    cmake_proc = subprocess.run(
        f'module load {module_name} && cmake --version',
        shell=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, LMOD_PAGER=''))
    assert cmake_proc.returncode == 0, 'Failed to run the CMake executable.\n' + \
        cmake_proc.stderr
    assert cmake_version in cmake_proc.stdout, f'CMake executable loaded in the Lmod file is not the expected {cmake_version} version: {cmake_proc.stdout}'


def main(module_base, module_dir):
    assert os.path.isdir(
        module_base), f'Module base directory {module_base} does not exist.'
    print(f'Using module base directory {module_base}.')

    cmake_org_files_json = 'https://cmake.org/files/LatestRelease/cmake-latest-files-v1.json'

    # Detect latest CMake release page from cmake.org's latest release JSON file
    print('Querying CMake.org latest files...', end='', flush=True)
    installer_name, cmake_version = query_cmake_org_latest_files(
        cmake_org_files_json)
    print(
        f'\x1b[1K\rLatest CMake: {cmake_version}, Installer: {installer_name}')

    # Install directory
    dir_install = os.path.join(module_dir, cmake_version)
    # Concat installer file name to base url
    installer_url = urllib.parse.urljoin(cmake_org_files_json, installer_name)

    print(f'Downloading {installer_url} to {installer_name}...',
          end='',
          flush=True)
    download_check_installer(installer_url, installer_name)
    print(f'\x1b[1K\rDownloaded {installer_name}.')

    print(f'Installing CMake {cmake_version} in {dir_install}...',
          end='',
          flush=True)
    cmake_executable = install_check_cmake(installer_name, cmake_version,
                                           dir_install)
    print(f'\x1b[1K\rInstalled CMake {cmake_version} in {dir_install}.')

    print(f'Removing {installer_name}...', end='', flush=True)
    os.remove(installer_name)
    print(f'\x1b[1K\rRemoved {installer_name}.')

    print(f'Creating module file under {module_base}...', end='', flush=True)
    module_name = create_check_modulefile(module_base, cmake_version,
                                          dir_install)
    print(f'\x1b[1K\rCreated module file {module_name} under {module_base}.')

    print(f'Check created module {module_name}...', end='', flush=True)
    check_module(module_name, cmake_version, cmake_executable)
    print(f'\x1b[1K\rChecked created module {module_name}.')

    print('Done.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download the latest CMake installer from cmake.org and generate a module.'
    )
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--module-base-dir',
                        type=str,
                        default=os.path.expanduser('~/.local/modules/'),
                        help='The base directory for the module files.')
    parser.add_argument('--module-dir',
                        type=str,
                        default=os.path.expanduser('~/.local/'),
                        help='The directory for the module files.')
    args = parser.parse_args()

    main(args.module_base_dir, args.module_dir)
