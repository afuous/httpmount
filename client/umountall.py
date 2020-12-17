#!/usr/bin/env python3

import json
import os
import subprocess

baseDir = os.path.dirname(os.path.abspath(__file__))
configFile = os.path.join(baseDir, 'config.json')
mntDir = os.path.join(baseDir, 'mnt')

config = None
with open(configFile, 'r') as f:
    config = json.load(f)

for obj in config:
    mountpoint = obj['mountpoint']
    if not ('/' in mountpoint):
        mountpoint = os.path.join(mntDir, mountpoint)
    subprocess.run(['umount', mountpoint])
    try:
        os.rmdir(mountpoint)
    except:
        pass

try:
    os.rmdir(mntDir)
except:
    pass
