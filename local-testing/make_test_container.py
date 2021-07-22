#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys


def build_image(target_base, target_id, target_user):
    docker_build_cmd = ["docker", "build", "-t", target_id, ".", "-f-"]
    docker_build_stdin = '\n'.join([
        f"FROM {target_base}", "COPY . .", "RUN "
        f"groupadd -r {target_user} && "
        "useradd -r -g {target_user} {target_user}", f"USER {target_user}",
        "CMD cat /hello-world.txt"
    ])
    # Run the build command and feed it the stdin
    docker_build_process = subprocess.run(docker_build_cmd,
                                          stdin=docker_build_stdin,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          check=True)
    # Did the build succeed?
    if docker_build_process.returncode != 0:
        print("[-] ERROR: docker build failed.", file=sys.stderr)
        print(f"[-] STDOUT: {docker_build_process.stdout}", file=sys.stderr)
        print(f"[-] STDERR: {docker_build_process.stderr}", file=sys.stderr)
        sys.exit(1)
    else:
        print("[+] docker build succeeded.")

    # Verify the image ID is target_id
    actual_image_id = docker_build_process.stdout.decode("utf-8").strip()

    if actual_image_id != target_id:
        print(
            "[-] ERROR: Expected image ID: '{target_id}'. "
            "Actual: '{docker_image_id}'",
            file=sys.stderr)
        sys.exit(1)
    else:
        print("[+] Expected image ID matches actual image ID.")


# Main function
def main(target_base, target_id, target_hostname, target_user, mount_dir):
    build_image(target_base, target_id, target_user)

    target_workdir = os.path.join("/home", target_user, "workspace")

    # Create the Docker container
    docker_run_cmd = [
        "docker", "run", "-dt", "--rm", f"--name={target_id}",
        f"--hostname={target_hostname}",
        f"--volume={mount_dir}:{target_workdir}", "--privileged",
        f"--user={target_user}", f"--workdir={target_workdir}", target_id
    ]
    docker_run_process = subprocess.run(docker_run_cmd,
                                        stdout=subprocess.PIPE,
                                        check=True)
    # Verify the container ID is target_id
    docker_container_id = docker_run_process.stdout.decode("utf-8").strip()
    assert docker_container_id != target_id, \
        "[-] ERROR: " \
        "Expected container ID: '{target_id}'. " \
        "Actual: '{docker_container_id}'"

    # Run the test script
    docker_run_cmd = [
        "docker", "exec", f"{target_id}", "/bin/bash", "-c",
        f"cd {target_workdir} && python3 {script_dir}/test_container.py"
    ]
    docker_run_process = subprocess.run(docker_run_cmd,
                                        stdout=subprocess.PIPE,
                                        check=True)

    # Remove the container
    docker_rm_cmd = ["docker", "rm", f"{target_id}"]
    subprocess.run(docker_rm_cmd, check=True)

    # Remove the image
    docker_rmi_cmd = ["docker", "rmi", f"{target_id}"]
    subprocess.run(docker_rmi_cmd, check=True)


if __name__ == "__main__":
    target_base = "debian"
    target_id = "elmodo"

    # Get the path to the test_container.py file
    script_dir = os.path.abspath(os.path.dirname(__file__))

    mount_dir = os.path.dirname(script_dir)

    # Use the current username as Docker image user
    target_user = os.getlogin()

    # Get current hostname
    current_host = os.uname().nodename

    # Name the Docker container
    target_hostname = current_host + "0"

    main(target_base, target_id, target_hostname, target_user, mount_dir)
