#!/usr/bin/env python3
"""
ERNA AI Commander — safe high-level MAVLink command interface.

Claude (in the console) is the COMMANDER, not the pilot. This module turns
high-level intent (takeoff/goto/velocity/orbit/rtl/land) into MAVLink, but
EVERY command passes a hard SafetyFilter first. The LLM proposes; the filter
disposes. See project-erna-ai-commander for the full doctrine.

Targets:
  --conn udp:127.0.0.1:14550   SITL (default, safe to fully exercise)
  --conn tcp:127.0.0.1:5760    real drone via GCS mavlink-router
Real-drone movement is BLOCKED unless ERNA_ALLOW_REAL=1 AND --i-understand
is passed (belt + suspenders so a stray call can't fly the real aircraft).
--dry-run prints what would be sent without sending.
"""
from __future__ import annotations
import argparse
import math
import os
import sys
import time
from dataclasses import dataclass


# ---------------- Safety filter (pure logic — unit-testable, no MAVLink) ----
@dataclass
class SafetyLimits:
    geofence_radius_m: float = 150.0   # max horizontal dist from HOME
    alt_floor_m: float = 1.0           # min commanded alt (AGL)
    alt_ceiling_m: float = 60.0        # max commanded alt (AGL)
    max_speed_mps: float = 8.0         # max commanded velocity magnitude
    require_guided: bool = True        # only command in GUIDED (else human has the stick)


def _haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (math.sin(dp/2)**2 +
         math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def check_command(cmd: dict, state: dict, lim: SafetyLimits) -> tuple[bool, str]:
    """Return (allowed, reason). `cmd` = high-level intent, `state` = current
    vehicle telemetry. This is the ONLY gate between the LLM and the aircraft."""
    kind = cmd.get("kind")

    # Movement commands require a healthy, GUIDED, armed vehicle.
    MOVE = {"takeoff", "goto", "velocity", "orbit"}
    if kind in MOVE:
        if lim.require_guided and state.get("mode") != "GUIDED":
            return False, f"vehicle not in GUIDED (mode={state.get('mode')}) — human override active"
        if not state.get("armed") and kind != "takeoff":
            return False, "vehicle not armed"
        if state.get("home_lat") is None:
            return False, "no HOME set — cannot enforce geofence"

    if kind == "goto":
        lat, lon, alt = cmd["lat"], cmd["lon"], cmd["alt"]
        if not (abs(lat) > 0.0001 and abs(lon) > 0.0001):
            return False, "invalid/zero target coordinates"
        if any(map(lambda v: v != v, (lat, lon, alt))):  # NaN
            return False, "NaN in command"
        d = _haversine_m(state["home_lat"], state["home_lon"], lat, lon)
        if d > lim.geofence_radius_m:
            return False, f"target {d:.0f}m from home exceeds geofence {lim.geofence_radius_m:.0f}m"
        if not (lim.alt_floor_m <= alt <= lim.alt_ceiling_m):
            return False, f"alt {alt:.0f}m outside [{lim.alt_floor_m},{lim.alt_ceiling_m}]"
        return True, "ok"

    if kind == "takeoff":
        alt = cmd["alt"]
        if not (lim.alt_floor_m <= alt <= lim.alt_ceiling_m):
            return False, f"takeoff alt {alt:.0f}m outside [{lim.alt_floor_m},{lim.alt_ceiling_m}]"
        return True, "ok"

    if kind == "velocity":
        vx, vy, vz = cmd["vx"], cmd["vy"], cmd["vz"]
        mag = math.sqrt(vx*vx + vy*vy + vz*vz)
        if mag > lim.max_speed_mps:
            return False, f"speed {mag:.1f} exceeds cap {lim.max_speed_mps}"
        # don't let the AI drive into the ground or past the ceiling
        alt = state.get("alt_rel")
        if alt is not None and alt < lim.alt_floor_m and vz > 0:  # vz>0 = down (NED)
            return False, f"descending below alt floor ({alt:.1f}m)"
        return True, "ok"

    if kind in ("rtl", "land", "loiter", "set_mode"):
        return True, "ok"   # safe/recovery actions always allowed

    return False, f"unknown command kind {kind!r}"


# ---------------- Commander (MAVLink side) ----------------------------------
class Commander:
    def __init__(self, conn, limits: SafetyLimits, dry_run=True,
                 allow_real=False):
        self.conn_str = conn
        self.lim = limits
        self.dry_run = dry_run
        # is_real = anything that isn't the local SITL UDP. READ-ONLY
        # (connect + telemetry) is ALWAYS allowed — reading the drone through
        # mavlink-router is safe and non-invasive. Only state-CHANGING
        # commands to a real drone require the explicit unlock.
        self.is_real = not (("127.0.0.1:14550" in conn) or ("sitl" in conn.lower()))
        self.allow_real = allow_real
        self.m = None

    def connect(self):
        from pymavlink import mavutil
        self.mav = mavutil
        self.m = mavutil.mavlink_connection(self.conn_str)
        # Lock onto the AUTOPILOT's heartbeat, not the first one on the link.
        # On the RFD900 there are multiple talkers (GCS components, router)
        # and the first HEARTBEAT is often sys=0 with a garbage mode — which
        # would make the GUIDED gate misread and refuse everything. Find the
        # real ArduPilot (autopilot != INVALID, not a GCS/component type).
        import time as _t
        self.ap_sys = None
        t0 = _t.time()
        while _t.time() - t0 < 15:
            hb = self.m.recv_match(type="HEARTBEAT", blocking=True, timeout=3)
            if hb is None:
                continue
            ap = hb.autopilot
            typ = hb.type
            if (ap != self.mav.mavlink.MAV_AUTOPILOT_INVALID
                    and typ != self.mav.mavlink.MAV_TYPE_GCS):
                self.ap_sys = hb.get_srcSystem()
                self.ap_comp = hb.get_srcComponent()
                self.m.target_system = self.ap_sys
                self.m.target_component = self.ap_comp
                break
        if self.ap_sys is None:
            raise SystemExit("no autopilot heartbeat found on the link")
        print(f"[cmd] connected {self.conn_str} autopilot sys={self.ap_sys} "
              f"comp={self.ap_comp}", flush=True)

    def telemetry(self) -> dict:
        s = {"mode": None, "armed": None, "home_lat": None, "home_lon": None,
             "lat": None, "lon": None, "alt_rel": None}
        # mode + armed — ONLY from the autopilot's heartbeat (ignore sys=0 etc).
        import time as _t
        t0 = _t.time()
        hb = None
        while _t.time() - t0 < 4:
            h = self.m.recv_match(type="HEARTBEAT", blocking=True, timeout=2)
            # Must match the autopilot's sys AND comp — there are other
            # components on the same sysid (e.g. sys1/comp0) that report a
            # different mode and would be misread (the GUIDED-vs-STABILIZE bug).
            if (h and h.get_srcSystem() == self.ap_sys
                    and h.get_srcComponent() == self.ap_comp):
                hb = h; break
        if hb:
            # Map custom_mode via the ArduCopter table directly — more robust
            # than mode_string_v10, which returns hex when the heartbeat's
            # type field doesn't map (seen on the real Cube over RFD).
            COPTER = {0:"STABILIZE",1:"ACRO",2:"ALT_HOLD",3:"AUTO",4:"GUIDED",
                      5:"LOITER",6:"RTL",7:"CIRCLE",9:"LAND",16:"POSHOLD",
                      17:"BRAKE",20:"GUIDED_NOGPS"}
            s["mode"] = COPTER.get(hb.custom_mode, self.mav.mode_string_v10(hb))
            s["armed"] = bool(hb.base_mode & self.mav.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        gp = self.m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=3)
        if gp:
            s["lat"] = gp.lat/1e7; s["lon"] = gp.lon/1e7; s["alt_rel"] = gp.relative_alt/1000.0
        # home
        try:
            self.m.mav.command_long_send(self.m.target_system, self.m.target_component,
                self.mav.mavlink.MAV_CMD_GET_HOME_POSITION, 0,0,0,0,0,0,0,0)
            hm = self.m.recv_match(type="HOME_POSITION", blocking=True, timeout=3)
            if hm:
                s["home_lat"] = hm.latitude/1e7; s["home_lon"] = hm.longitude/1e7
        except Exception:
            pass
        if s["home_lat"] is None:        # fall back to current pos as home ref
            s["home_lat"], s["home_lon"] = s["lat"], s["lon"]
        return s

    def issue(self, cmd: dict) -> bool:
        state = self.telemetry()
        ok, reason = check_command(cmd, state, self.lim)
        tag = "DRY-RUN " if self.dry_run else ""
        if not ok:
            print(f"[cmd] REFUSED {cmd.get('kind')}: {reason}", flush=True)
            return False
        # Real-drone lock: a passing filter is not enough to actually move the
        # real aircraft — need ERNA_ALLOW_REAL=1 + --i-understand. Dry-run and
        # SITL are exempt (no real aircraft moves).
        if self.is_real and not self.allow_real and not self.dry_run:
            print(f"[cmd] LOCKED (real drone): {cmd.get('kind')} passed the "
                  f"filter but real commanding is locked. Set ERNA_ALLOW_REAL=1 "
                  f"and pass --i-understand to fly the actual aircraft.",
                  flush=True)
            return False
        print(f"[cmd] {tag}ALLOW {cmd} (state mode={state['mode']} "
              f"armed={state['armed']})", flush=True)
        if self.dry_run:
            return True
        return self._send(cmd, state)

    def _send(self, cmd, state):
        mv = self.mav.mavlink
        k = cmd["kind"]
        try:
            if k == "set_mode":
                self.m.set_mode(cmd["mode"]); return True
            if k == "rtl":
                self.m.set_mode("RTL"); return True
            if k == "land":
                self.m.set_mode("LAND"); return True
            if k == "loiter":
                self.m.set_mode("LOITER"); return True
            if k == "takeoff":
                self.m.mav.command_long_send(self.m.target_system, self.m.target_component,
                    mv.MAV_CMD_NAV_TAKEOFF, 0,0,0,0,0,0,0, cmd["alt"]); return True
            if k == "goto":
                self.m.mav.set_position_target_global_int_send(
                    0, self.m.target_system, self.m.target_component,
                    mv.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
                    0b0000111111111000,
                    int(cmd["lat"]*1e7), int(cmd["lon"]*1e7), cmd["alt"],
                    0,0,0, 0,0,0, 0,0); return True
            if k == "velocity":
                self.m.mav.set_position_target_local_ned_send(
                    0, self.m.target_system, self.m.target_component,
                    mv.MAV_FRAME_LOCAL_NED, 0b0000111111000111,
                    0,0,0, cmd["vx"],cmd["vy"],cmd["vz"], 0,0,0, 0,0); return True
        except Exception as e:
            print(f"[cmd] send error: {e}", flush=True)
            return False
        return False


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--conn", default="udp:127.0.0.1:14550")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--i-understand", action="store_true",
                    help="required (with ERNA_ALLOW_REAL=1) to command a REAL drone")
    sub = ap.add_subparsers(dest="kind", required=True)
    sub.add_parser("status")
    p = sub.add_parser("takeoff"); p.add_argument("alt", type=float)
    p = sub.add_parser("goto"); p.add_argument("lat", type=float); p.add_argument("lon", type=float); p.add_argument("alt", type=float)
    p = sub.add_parser("velocity"); [p.add_argument(a, type=float) for a in ("vx","vy","vz")]
    for s in ("rtl","land","loiter"):
        sub.add_parser(s)
    a = ap.parse_args()
    allow_real = os.environ.get("ERNA_ALLOW_REAL") == "1" and a.i_understand
    c = Commander(a.conn, SafetyLimits(), dry_run=a.dry_run, allow_real=allow_real)
    c.connect()
    if a.kind == "status":
        print(c.telemetry()); sys.exit(0)
    cmd = {"kind": a.kind}
    for f in ("alt","lat","lon","vx","vy","vz"):
        if hasattr(a, f): cmd[f] = getattr(a, f)
    sys.exit(0 if c.issue(cmd) else 1)
