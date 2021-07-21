#!/usr/bin/env python3

# Get the lastest version of Ninja from GitHub

import argparse
import json
import os
import subprocess
import urllib.request
import zipfile


def query_latest_release(release_info_url):
    # Get Ninja release info from GitHub as a JSON object
    release_info = json.load(urllib.request.urlopen(release_info_url))

    # Get the latest version of Ninja
    ninja_version = release_info["tag_name"]

    # Get the download URL for the latest Linux version of Ninja
    linux_assets = [asset for asset in release_info['assets']
                    if asset['name'].endswith('.zip') and 'linux' in asset['name']]
    assert len(linux_assets) == 1, "There should be only one Linux asset"
    linux_asset = linux_assets[0]

    download_url = linux_asset['browser_download_url']
    return ninja_version, download_url


def download_check_archive(download_url, dest_file):
    # Download the latest version of Ninja
    http_result = urllib.request.urlretrieve(download_url, dest_file)
    assert http_result[1].getcode(
    ) == 200, f"Download from {download_url} failed."

    # Assert that the downloaded file at dest_file is a zip file
    assert zipfile.is_zipfile(
        dest_file), f"Downloaded file {dest_file} is not a zip file."


def install_check_ninja(ninja_version, install_dir):
    # Check that the Ninja executable exists in the current directory
    ninja_exe_cur = os.path.abspath(os.getcwd(), 'ninja')
    # Assert the ninja executable path is correct
    assert os.path.isfile(
        ninja_exe_cur), f"The ninja executable {ninja_exe_cur} does not exist."
    # Assert ninja is executable
    assert os.access(
        ninja_exe_cur, os.X_OK), f"The ninja executable {ninja_exe_cur} is not executable."

    # Create the directory hierarchy if necessary
    os.makedirs(install_dir, exist_ok=True)

    # Move the executable to the install directory
    ninja_executable = os.path.join(install_dir, 'ninja')
    os.rename(ninja_exe_cur, ninja_executable)

    # Assert that the installed Ninja file exists.
    assert os.path.isfile(os.path.join(install_dir, 'ninja')), \
        f'{os.path.join(install_dir, "ninja")} does not exist.'

    # Assert that the installed Ninja file is executable
    assert os.access(ninja_executable, os.X_OK), \
        f'{ninja_executable} is not executable.'
    # Assert that the installed Ninja is the correct version
    ninja_proc = subprocess.run(
        [ninja_executable, '-v'],
        capture_output=True, text=True)
    assert ninja_proc.returncode == 0, ninja_proc.stderr
    assert ninja_version in ninja_proc.stdout, ninja_proc.stdout

    return ninja_executable


# Create an Lmod module file
def create_check_modulefile(module_base, ninja_version, install_dir):
    module_name = os.path.join('ninja', ninja_version)
    module_file = os.path.join(module_base, module_name)
    module_file_content = f"""#%Module
    proc ModulesHelp {{ }} {{
    puts stderr {{Ninja {ninja_version}}}
    }}
    module-whatis {{Ninja {ninja_version}}}
    set root    {install_dir}
    conflict    ninja
    prepend-path    PATH            $root"""

    with open(module_file, 'w') as fh:
        fh.write(module_file_content)

    # Make sure the Lmod can load the module
    lmod_proc = subprocess.run(f'module show ninja/{ninja_version}',
                               shell=True,
                               capture_output=True,
                               text=True,
                               env=dict(os.environ, LMOD_PAGER=''))
    assert lmod_proc.returncode == 0, 'Lmod failed to load the module'
    assert module_file in lmod_proc.stderr, 'Lmod failed to load the module'

    return module_name


def check_module(module_name, ninja_version, ninja_executable):
    # Make sure the correct ninja executable is in the path.
    ninja_proc = subprocess.run(f'module load {module_name} && which ninja',
                                shell=True,
                                capture_output=True,
                                text=True,
                                env=dict(os.environ, LMOD_PAGER=''))
    assert ninja_proc.returncode == 0, 'ninja executable is not in the PATH set by the Lmod modulefile.'
    assert os.path.samefile(
        ninja_proc.stdout.rstrip(), ninja_executable
    ), f'ninja executable loaded by Lmod is not the expected {ninja_version} verison. {ninja_proc.stdout}'

    # Make sure the ninja executable is in the path works and is the version
    # we expected.
    ninja_proc = subprocess.run(
        f'module load {module_name} && ninja -v',
        shell=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, LMOD_PAGER=''))
    assert ninja_proc.returncode == 0, 'Failed to run the ninja executable.\n' + \
        ninja_proc.stderr
    assert ninja_version in ninja_proc.stdout, f'ninja executable loaded in the Lmod file is not the expected {ninja_version} version: {ninja_proc.stdout}'


def main(module_base, module_dir):
    # Assert that the base module directory exists
    assert os.path.isdir(
        module_base), f'Module base directory {module_base} does not exist.'
    print(f'Using module base directory {module_base}.')

    # Get the latest Ninja release info from GitHub
    release_info_url = "https://api.github.com/repos/ninja-build/ninja/releases/latest"
    ninja_version, download_url = query_latest_release(release_info_url)

    # Target download file name
    archive_name = "ninja.zip"

    # Download the latest version of Ninja
    print(f'Downloading {installer_url} to {installer_name}...',
          end='',
          flush=True)
    download_check_archive(download_url, archive_name)
    print(f'\x1b[1K\rDownloaded {installer_name}.')

    # Unzip the archive
    print(f"Extracting {archive_name}...", end="", flush=True)
    with zipfile.ZipFile(archive_name, 'r') as zip_ref:
        for file in zip_ref.namelist():
            zip_ref.extract(file, ".")
    print(f"\x1b[1K\rExtracted {archive_name}.")

    install_dir = os.path.join(module_dir, ninja_version)

    print(f"Moving Ninja {ninja_version} binary to {install_dir}...",
          end="",
          flush=True)
    # Install Ninja to install_dir
    ninja_executable = install_check_ninja(ninja_version, install_dir)
    print(f"\x1b[1K\rMoved Ninja {ninja_version} binary to {install_dir}.")

    # Remove the archive
    print(f'Removing {archive_name}...', end='', flush=True)
    os.remove(archive_name)
    print(f'\x1b[1K\rRemoved {archive_name}.')

    # Create a modulefile for Git
    print(f'Creating module file under {module_base}...', end='', flush=True)
    module_name = create_check_modulefile(module_base, ninja_version,
                                          install_dir)
    print(f'\x1b[1K\rCreated module file {module_name} under {module_base}.')

    # Check if the modulefile works
    print(f'Check created module {module_base}...', end='', flush=True)
    check_module(module_name, ninja_version, ninja_executable)
    print(f'\x1b[1K\rChecked created module {module_name}.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download the latest Ninja binary from Github and generate a module.'
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
