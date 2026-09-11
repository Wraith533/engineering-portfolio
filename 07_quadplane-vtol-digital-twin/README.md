# QuadPlane VTOL — Flight Data & Digital Twin

Took a full data rip from a **QuadPlane VTOL aircraft** — one that flew real sorties
at up to **135 mph (61 m/s) over 19 km** — and rebuilt the aircraft and its flights in
**ArduPilot SITL** simulation, plus cloned the telemetry radio that controlled it.

## What's here

- **Complete aircraft data package** (`drone-sdcard-backup/`). A read-only rip of the
  flight controller's SD card: full parameter set, dataflash logs, missions, and a
  `HANDOVER.txt` documenting the airframe (QuadPlane VTOL, ArduPlane 4.5.4 with custom
  mods, ARK_FPV controller, u-blox GPS, SBUS-over-radio RC) and nine logged boot
  sessions. Log 8 is the big one: 10.5 min, 19.4 km, 135 mph top speed, ~244 m altitude.
- **Parameter forensics.** Diffs between the card's saved params and the live flight
  controller, plus params reconstructed straight from the logs — the work of proving
  what the aircraft was *actually* running versus what was saved.
- **SITL reconstruction** (`sitl_and_tools/`). Build/run scripts that stand up
  ArduPilot SITL so the aircraft can be re-flown against its real parameters, new
  missions tested, and behavior reproduced on the bench.
- **Ground-station and link tooling.** A ground-station script, a CRSF RC stream
  bridge, a motor-spin bench utility, a GPS test server, and **RFD900x radio tools** —
  including dumping and cloning the telemetry radio's settings so the link hardware can
  be reproduced.
- **Transmitter backup** (`radiomaster-pocket-sd-backup-2026-04-28/`) — a full EdgeTX
  SD backup (models, config, firmware, logs) of the hand controller.
- **Speed-drone simulation notes** and a bench handover.

## Why it matters to an employer

- Real **flight-test data engineering**: pulling ground truth off an aircraft,
  reconciling it, and turning it into a reproducible simulation — the loop every
  serious autonomy/robotics team runs.
- Hands-on with the full **ArduPilot / MAVLink / SITL** toolchain and the RF telemetry
  layer beneath it.

## Stack

ArduPilot (ArduPlane) + SITL, MAVLink/pymavlink, dataflash logs, QGC/Mission Planner
waypoints, RFD900x radios, CRSF, EdgeTX.
