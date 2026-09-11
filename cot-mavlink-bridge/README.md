# CoT–MAVLink Bridge

A two-way bridge that puts live MAVLink drones onto a TAK server as **Cursor-on-Target**
tracks, and relays **ARM / DISARM / RTL** commands from ATAK back to the aircraft.
Developed on invitation in collaboration with the U.S. Army Research Laboratory.

- **Uplink** — reads `GLOBAL_POSITION_INT`, builds a standards-correct CoT `event`
  (type `a-f-G-U-C`, callsign, group), and publishes over UDP. Fix-gated, with a
  `stale` timestamp and a 10-second heartbeat so tracks never flicker or ghost.
- **Downlink** — parses a CoT `<command action="…">` element and maps it to the
  matching MAVLink `command_long` (rate-limited to 10 Hz, guarded against a missing target).

Endpoint addresses in the source are illustrative defaults. Not an official ARL or
U.S. Government publication; implies no endorsement.

`cot_mavlink_bridge.py` — Python · pymavlink · lxml.
