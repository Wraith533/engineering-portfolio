#!/usr/bin/env python3
"""Fly the simulated ERNA through the full commander loop, gating every
command with the REAL safety filter. Proves the MAVLink encoding + filter
against actual ArduPilot before any live flight."""
import sys, time, math
sys.path.insert(0, "/home/william/erna_ai_commander")
from erna_cmd import check_command, SafetyLimits
from pymavlink import mavutil

lim = SafetyLimits()
m = mavutil.mavlink_connection("udpin:127.0.0.1:14550")
m.wait_heartbeat(timeout=20)
print(f"[sitl] heartbeat sys={m.target_system}", flush=True)

def state():
    s = {"mode":None,"armed":None,"home_lat":21.4845,"home_lon":-158.0597,
         "lat":None,"lon":None,"alt_rel":None}
    hb = m.recv_match(type="HEARTBEAT", blocking=True, timeout=3)
    if hb:
        s["mode"] = mavutil.mode_string_v10(hb)
        s["armed"] = bool(hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    gp = m.recv_match(type="GLOBAL_POSITION_INT", blocking=True, timeout=3)
    if gp:
        s["lat"]=gp.lat/1e7; s["lon"]=gp.lon/1e7; s["alt_rel"]=gp.relative_alt/1000.0
    return s

def gated_send(cmd, sender):
    st = state()
    ok, why = check_command(cmd, st, lim)
    if not ok:
        print(f"[sitl] FILTER REFUSED {cmd.get('kind')}: {why}", flush=True)
        return False
    print(f"[sitl] FILTER OK {cmd}  (mode={st['mode']} armed={st['armed']} alt={st['alt_rel']})", flush=True)
    sender()
    return True

# 1) wait EKF/GPS ready
print("[sitl] waiting for GPS/EKF ready...", flush=True)
t0=time.time()
while time.time()-t0 < 60:
    g = m.recv_match(type="GPS_RAW_INT", blocking=True, timeout=2)
    if g and g.fix_type >= 3:
        print(f"[sitl] GPS fix_type={g.fix_type}", flush=True); break
time.sleep(3)

# 2) GUIDED
m.set_mode(m.mode_mapping()["GUIDED"]); time.sleep(2)
print(f"[sitl] mode now {state()['mode']}", flush=True)

# 3) arm (retry)
armed=False
for _ in range(30):
    m.mav.command_long_send(m.target_system,m.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,0,1,0,0,0,0,0,0)
    time.sleep(1)
    if state()["armed"]: armed=True; print("[sitl] ARMED", flush=True); break
if not armed: print("[sitl] FAIL: could not arm"); sys.exit(1)

# 4) takeoff to 12m (gated)
gated_send({"kind":"takeoff","alt":12},
    lambda: m.mav.command_long_send(m.target_system,m.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,0,0,0,0,0,0,0,12))
for _ in range(40):
    a=state()["alt_rel"]
    if a and a>=11: print(f"[sitl] reached takeoff alt {a:.1f}m", flush=True); break
    time.sleep(1)

# 5) goto ~60m north (within 150m fence), gated
tgt=(21.4845+0.00054, -158.0597, 12)
def goto_send():
    m.mav.set_position_target_global_int_send(0,m.target_system,m.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,0b0000111111111000,
        int(tgt[0]*1e7),int(tgt[1]*1e7),tgt[2],0,0,0,0,0,0,0,0)
gated_send({"kind":"goto","lat":tgt[0],"lon":tgt[1],"alt":tgt[2]}, goto_send)
R=6371000
for _ in range(40):
    s=state()
    if s["lat"]:
        d=R*math.radians(math.hypot(s["lat"]-tgt[0],(s["lon"]-tgt[1])*math.cos(math.radians(tgt[0]))))
        if d<3: print(f"[sitl] arrived at target (<3m)", flush=True); break
    time.sleep(1)
print(f"[sitl] dist to target now: {d:.1f}m", flush=True)

# 6) prove the filter BLOCKS an out-of-fence goto (live, against real vehicle)
blocked = not gated_send({"kind":"goto","lat":21.50,"lon":-158.04,"alt":12}, goto_send)
print(f"[sitl] out-of-fence goto correctly blocked: {blocked}", flush=True)

# 7) RTL home
m.set_mode(m.mode_mapping()["RTL"]); print("[sitl] RTL commanded", flush=True)
for _ in range(60):
    s=state()
    if s["alt_rel"] is not None and s["alt_rel"]<0.5: print("[sitl] landed (RTL complete)", flush=True); break
    time.sleep(1)
print(f"[sitl] final: mode={state()['mode']} alt={state()['alt_rel']}", flush=True)
print("[sitl] === FLIGHT TEST COMPLETE ===", flush=True)
