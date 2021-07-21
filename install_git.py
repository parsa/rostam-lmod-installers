#!/usr/bin/env python

import argparse
import os
import re
import shutil
import subprocess
import tarfile
import urllib.parse
import urllib.request


# Detect latest Git release from its kernel.org webpage
def query_latest_git_release(latest_url):
    latest_html = urllib.request.urlopen(latest_url).read().decode("utf-8")
    # releases = re.findall(r'(?<=git-).[0-9.]*(?=.tar.gz)', latest_html)
    # return max(releases, key=lambda k: [int(x) for x in k.split('.')])
    releases = re.findall(r"[a-z-\.0-9]+\.tar\.xz", latest_html)
    return max(
        releases,
        key=lambda k: [int(x) for x in re.split(r"-|\.", k) if x.isdigit()])


def download_check_archive(archive_name, archive_url):
    http_result = urllib.request.urlretrieve(archive_url, archive_name)

    assert (http_result[0] == archive_name
            ), f'Failed to download {archive_name} from "{archive_url}".'
    assert os.path.isfile(
        archive_name), f"Git tarball file {archive_name} does not exist."


def install_check_git(dir_build, dir_install, git_version):
    # Configure Git
    subprocess.run(
        [
            "./configure", f"--prefix={dir_install}", "--with-editor=vim",
            "--quiet"
        ],
        cwd=dir_build,
        check=True,
    )

    # Install Git
    subprocess.run(["make", "install", f"-j{os.cpu_count()}", "-s"],
                   cwd=dir_build,
                   check=True)

    # Assert that the installed Git file exists.
    git_executable = os.path.join(dir_install, "bin", "git")
    assert os.path.isfile(
        git_executable), f"Git executable {git_executable} does not exist."

    # Assert that the installed Git works with its absolute path.
    git_proc = subprocess.run([git_executable, "--version"],
                              capture_output=True,
                              text=True)
    assert git_proc.returncode == 0, f"Git executable {git_executable} does not work."
    # Check that the Git executable is the expected version.
    assert (
        git_version in git_proc.stdout
    ), f"Git executable {git_executable} is not the expected version: {git_proc.stdout}"
    return git_executable


def create_check_modulefile(git_version, module_base, dir_install):
    module_name = os.path.join("git", git_version)
    # Create an Lmod module file
    module_file = os.path.join(module_base, module_name)

    module_file_content = f"""#%Module
    proc ModulesHelp {{ }} {{
    puts stderr {{Git {git_version}}}
    }}
    module-whatis {{Git {git_version}}}
    set root    {dir_install}
    conflict    git
    prepend-path    LD_LIBRARY_PATH $root/lib64
    prepend-path    LIBRARY_PATH    $root/lib64
    prepend-path    MANPATH         $root/share/man
    prepend-path    PATH            $root/bin
    """

    with open(module_file, "w") as fh:
        fh.write(module_file_content)

    # Make sure the Lmod can load the module
    lmod_proc = subprocess.run(
        f"module show git/{git_version}",
        shell=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, LMOD_PAGER=""),
    )
    assert lmod_proc.returncode == 0, ("Lmod failed to load the module.\n" +
                                       lmod_proc.stderr)
    assert module_file in lmod_proc.stderr, "Lmod failed to load the module."
    return module_name


def check_module(module_name, git_version, git_executable):
    # Make sure the correct Git executable is in the path.
    git_proc = subprocess.run(
        f"module load {module_name} && which git",
        shell=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, LMOD_PAGER=""),
    )
    assert git_proc.returncode == 0, "Git executable is not in the PATH set by the Lmod modulefile."
    assert os.path.samefile(
        git_proc.stdout.rstrip(), git_executable
    ), f"Git executable loaded by Lmod is not the expected {git_version} version. {git_proc.stdout}"

    # Make sure the Git executable is in the path works and is the version we
    # expected.
    git_proc = subprocess.run(
        f"module load {module_name} && git --version",
        shell=True,
        capture_output=True,
        text=True,
        env=dict(os.environ, LMOD_PAGER=""),
    )
    assert git_proc.returncode == 0, ("Failed to run the Git executable.\n" +
                                      git_proc.stderr)
    assert git_version in git_proc.stdout, f"Git executable loaded in the Lmod file is not the expected {git_version} version: {git_proc.stdout}"


def main(module_base, module_dir):
    assert os.path.isdir(
        module_base), f"Module base directory {module_base} does not exist."
    print(f"Using module base directory {module_base}.")

    latest_url = "https://mirrors.edge.kernel.org/pub/software/scm/git/"

    print("Query latest Git release...", end="", flush=True)
    archive_name = query_latest_git_release(latest_url)

    # Extract Git version number from the tarball name
    git_version = ".".join(
        [x for x in re.split(r"-|\.", archive_name) if x.isdigit()])
    print("\x1b[1K\rLatest Git version: " + git_version)

    print(
        f"Downloading {archive_name} from {latest_url}...",
        end="",
        flush=True)
    archive_url = urllib.parse.urljoin(latest_url, archive_name)
    download_check_archive(archive_name, archive_url)
    print(f"\x1b[1K\rDownloaded {archive_name}.")

    # Extract Git tarball
    print(f"Extracting {archive_name}...", end="", flush=True)
    with tarfile.open(archive_name, "r") as archive:
        archive.extractall()
    print(f"\x1b[1K\rExtracted {archive_name}.")

    dir_build = ".".join(archive_name.split(".")[:-2])
    dir_install = os.path.join(module_dir, git_version)

    print(f"Installing Git {git_version} in {dir_install}...",
          end="",
          flush=True)
    # Install Git
    git_executable = install_check_git(dir_build, dir_install, git_version)
    print(f"\x1b[1K\rInstalled Git {git_version} in {dir_install}.")

    print(f"Removing up {archive_name} and {dir_build}...", end="", flush=True)
    # Remove downloaded tarball and build directory
    os.remove(archive_name)
    shutil.rmtree(dir_build, ignore_errors=True)
    print(f"\x1b[1K\rRemoved {archive_name} and {dir_build}.")

    print(f"Creating module file under {module_base}...", end="", flush=True)
    module_name = create_check_modulefile(git_version, module_base, dir_install)
    print(f"\x1b[1K\rCreated module file under {module_base}.")

    print(f"Checking module file under {module_base}...", end="", flush=True)
    check_module(module_name, git_version, git_executable)
    print(f"\x1b[1K\rChecked module file under {module_base}.")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the latest Git tarball from kernel.org and generate a module."
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    parser.add_argument(
        "--module-base-dir",
        type=str,
        default=os.path.expanduser("~/.local/modules/"),
        help="The base directory for the module files.",
    )
    parser.add_argument(
        "--module-dir",
        type=str,
        default=os.path.expanduser("~/.local/"),
        help="The directory for the module files.",
    )
    args = parser.parse_args()

    main(args.module_base_dir, args.module_dir)
