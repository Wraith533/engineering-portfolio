import sys
sys.path.insert(0, "/home/william/erna_ai_commander")
from erna_cmd import check_command, SafetyLimits

lim = SafetyLimits()  # fence 150m, alt 1-60m, speed 8, GUIDED required
# realistic state: GUIDED, armed, home at Pearl Harbor
HOME = dict(mode="GUIDED", armed=True, home_lat=21.4845, home_lon=-158.0597,
            lat=21.4845, lon=-158.0597, alt_rel=20.0)

def near(lat=21.4845, lon=-158.0597): return (lat, lon)

cases = []
def case(desc, cmd, state, want_ok):
    ok, reason = check_command(cmd, state, lim)
    status = "PASS" if ok == want_ok else "FAIL"
    cases.append((status, desc, ok, reason))

# --- should ALLOW ---
case("goto within fence/alt", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":25}, HOME, True)
case("takeoff sane alt", {"kind":"takeoff","alt":15}, HOME, True)
case("velocity under cap", {"kind":"velocity","vx":3,"vy":2,"vz":0}, HOME, True)
case("rtl always allowed", {"kind":"rtl"}, HOME, True)
case("land always allowed", {"kind":"land"}, dict(HOME, mode="LOITER"), True)

# --- should REFUSE ---
case("goto OUTSIDE geofence (2km away)", {"kind":"goto","lat":21.50,"lon":-158.04,"alt":25}, HOME, False)
case("goto ABOVE ceiling", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":120}, HOME, False)
case("goto BELOW floor", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":0.2}, HOME, False)
case("goto zero coords", {"kind":"goto","lat":0,"lon":0,"alt":25}, HOME, False)
case("velocity OVER speed cap", {"kind":"velocity","vx":20,"vy":0,"vz":0}, HOME, False)
case("move while NOT guided (human override)", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":25}, dict(HOME, mode="STABILIZE"), False)
case("move while disarmed", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":25}, dict(HOME, armed=False), False)
case("goto with no HOME (cant enforce fence)", {"kind":"goto","lat":21.4850,"lon":-158.0600,"alt":25}, dict(HOME, home_lat=None), False)
case("velocity descending below floor", {"kind":"velocity","vx":0,"vy":0,"vz":2}, dict(HOME, alt_rel=0.5), False)

fails = [c for c in cases if c[0]=="FAIL"]
for st, desc, ok, reason in cases:
    print(f"  {st}  {desc:42s} -> allowed={ok} ({reason})")
print(f"\n{'ALL SAFETY TESTS PASSED' if not fails else str(len(fails))+' FAILED'}  ({len(cases)-len(fails)}/{len(cases)})")
sys.exit(1 if fails else 0)
