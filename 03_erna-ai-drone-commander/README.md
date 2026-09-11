# ERNA — AI Drone Commander

An **LLM commands a real drone through a hard safety filter**. The model is the
commander, not the pilot: it turns high-level intent (takeoff, go-to, velocity,
orbit, return-to-launch, land) into MAVLink, and **every command must pass a pure,
unit-tested SafetyFilter before it can be sent**. The LLM proposes; the filter
disposes.

This is the pattern I care about most: using a powerful, fallible model for
flexibility while a small, auditable, deterministic layer guarantees the aircraft
stays safe.

## The safety architecture

- **Pure-logic filter, independently testable.** Geofence radius, altitude floor and
  ceiling, max speed, and a "must be in GUIDED mode" rule are enforced in plain code
  with no MAVLink dependency, so the safety envelope is covered by a fast unit-test
  suite (`test_safety.py`) rather than trusted to a prompt.
- **Belt-and-suspenders on real hardware.** Movement on the real aircraft is blocked
  unless an environment flag *and* an explicit `--i-understand` are both set; a
  `--dry-run` prints exactly what would be sent. SITL is the default target so the
  full behavior can be exercised safely.
- **Same interface, sim or real.** The commander speaks to ArduPilot SITL over UDP or
  a real Cube autopilot over a GCS MAVLink router with no code change.

## Around the commander

- **SAR search planner** (`erna_search/`) — pick a datum and an IAMSAR pattern
  (expanding square, sector, parallel track, creeping line); it computes track spacing
  from altitude and camera field-of-view, lays out every waypoint with bearing/ETA and
  an endurance budget, and exports a `.waypoints` file that loads straight into Mission
  Planner.
- **Preflight gate** (`erna_preflight/`) and a **map watcher** service
  (`erna-map-watcher/`) that keep the ground picture and go/no-go checks current.
- **Field bridges** (`erna/`) — a gimbal probe and a LiDAR bridge for the payload.
- **Flight-tested backups** (`erna_pi_backups/`) from the companion computer.

## Why it matters to an employer

- Directly relevant to **autonomy and robotics**: MAVLink/ArduPilot integration,
  ground-station tooling, and mission planning that a real operator can use.
- More importantly, it shows I build **AI safety in the right place** — a verifiable
  guard around a capable model — which is exactly the discipline autonomy products need.

## Stack

Python, pymavlink, ArduPilot SITL, MAVLink, Mission Planner / QGroundControl waypoint
format, systemd services.
