#!/usr/bin/env python3

# Python version must be at least 3.6
import sys
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    print("Python version must be at least 3.6")
    sys.exit(1)

import urllib.request
import os
import shutil
import stat
import sys
import subprocess
import zipfile

ninja_zipball_url = 'https://github.com/ninja-build/ninja/archive/refs/tags/v1.10.2.zip'
with urllib.request.urlopen(ninja_zipball_url) as http_request:
    with open('ninja-v1.10.2.zip', 'wb') as file:
        file.write(http_request.read())
assert zipfile.is_zipfile('ninja-v1.10.2.zip')
with zipfile.ZipFile('ninja-v1.10.2.zip', 'r') as z:
    z.extractall()

os.chmod('ninja-1.10.2/src/browse.py', os.stat('ninja-1.10.2/src/browse.py').st_mode | stat.S_IEXEC)
os.chmod('ninja-1.10.2/src/inline.sh', os.stat('ninja-1.10.2/src/inline.sh').st_mode | stat.S_IEXEC)

subprocess.run(["python3", "configure.py", "--bootstrap"],
               cwd="ninja-1.10.2/",
               check=True)
subprocess.run(["ninja-1.10.2/ninja", "--version"], check=True)
shutil.copy2("ninja-1.10.2/ninja",
             os.path.expanduser("~/.local/ninja/1.10.2/ninja"))
