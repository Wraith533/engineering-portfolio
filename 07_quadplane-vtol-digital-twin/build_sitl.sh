#!/bin/bash
set -x
cd /home/william
echo "=== clone (shallow + submodules) ==="
git clone --recurse-submodules --shallow-submodules --depth 1 \
  https://github.com/ArduPilot/ardupilot.git ardupilot 2>&1
cd /home/william/ardupilot || { echo "CLONE FAILED"; exit 1; }
echo "=== prereqs (passwordless sudo) ==="
SKIP_AP_EXT_ENV=1 SKIP_AP_GIT_CHECK=1 Tools/environment_install/install-prereqs-ubuntu.sh -y 2>&1
echo "=== configure SITL ==="
./waf configure --board sitl 2>&1
echo "=== build copter ==="
./waf copter 2>&1
echo "=== BUILD COMPLETE rc=$? ==="
ls -la build/sitl/bin/arducopter 2>&1
