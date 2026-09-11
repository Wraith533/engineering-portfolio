#!/bin/bash
cd /home/william/ardupilot
source /home/william/venv-ardupilot/bin/activate
exec Tools/autotest/sim_vehicle.py -v ArduCopter --no-rebuild --no-mavproxy \
  --custom-location=21.4845,-158.0597,2,0 \
  --out=udp:127.0.0.1:14550
