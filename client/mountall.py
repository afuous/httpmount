#!/usr/bin/env python3

import json
import os
import subprocess

baseDir = os.path.dirname(os.path.abspath(__file__))
configFile = os.path.join(baseDir, 'config.json')
mntDir = os.path.join(baseDir, 'mnt')
scriptFile = os.path.join(baseDir, 'httpmount.py')

config = None
with open(configFile, 'r') as f:
    config = json.load(f)

for obj in config:
    mountpoint = obj['mountpoint']
    if not ('/' in mountpoint):
        mountpoint = os.path.join(mntDir, mountpoint)
        os.makedirs(mountpoint, exist_ok=True)
    subprocess.Popen([scriptFile, '-u', obj['url'], '-p', obj['password'], '-f', mountpoint])
