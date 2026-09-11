"""
telemetry.py — pluggable drone state source for georeferencing.

Every provider exposes .state() -> dict:
  {lat, lon, alt_msl, agl_m, roll, pitch, yaw (rad), heading_deg,
   fix: bool, source: str, age_s: float}
Providers: SimTelemetry (bench), MavlinkTelemetry (real Cube, matches the
Orin pipeline), ManualTelemetry (operator-entered, fixed ground camera).
"""
import math
import threading
import time


class _Base:
    name = "base"

    def state(self):
        raise NotImplementedError

    def set_manual(self, **kw):
        pass

    def start(self):
        pass


class SimTelemetry(_Base):
    """Simulated drone. Honest 'SIM' fix. Optional slow circular drift so the
    reproject-onto-feed behaviour is visibly exercised on the bench."""
    name = "sim"

    def __init__(self, lat=21.3622, lon=-157.9560, agl_m=80.0,
                 mount_tilt_deg=45.0, drift=False, **_):
        self.lat0, self.lon0 = lat, lon
        self.lat, self.lon = lat, lon
        self.agl_m = agl_m
        self.alt_msl = agl_m
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.drift = drift
        self.label = "SIM"
        self.acc = None
        self._fix_t = 0.0
        self._t0 = time.time()

    def state(self):
        if self.drift:
            dt = time.time() - self._t0
            r = 0.0003
            self.lat = self.lat0 + r * math.sin(dt * 0.05)
            self.lon = self.lon0 + r * math.cos(dt * 0.05)
            self.yaw = (dt * 0.05) % (2 * math.pi)
        age = (time.time() - self._fix_t) if self._fix_t else 0.0
        return {"lat": self.lat, "lon": self.lon, "alt_msl": self.alt_msl,
                "agl_m": self.agl_m, "roll": self.roll, "pitch": self.pitch,
                "yaw": self.yaw, "heading_deg": math.degrees(self.yaw) % 360,
                "fix": True, "source": self.label, "accuracy_m": self.acc,
                "age_s": age}

    def set_manual(self, lat=None, lon=None, agl_m=None, yaw_deg=None,
                   pitch_deg=None, roll_deg=None, source=None,
                   accuracy_m=None, **_):
        if lat is not None:
            self.lat = self.lat0 = float(lat)
        if lon is not None:
            self.lon = self.lon0 = float(lon)
        if agl_m is not None:
            self.agl_m = float(agl_m)
        if yaw_deg is not None:
            self.yaw = math.radians(float(yaw_deg))
        if pitch_deg is not None:
            self.pitch = math.radians(float(pitch_deg))
        if roll_deg is not None:
            self.roll = math.radians(float(roll_deg))
        if source is not None:
            self.label = str(source)
        if accuracy_m is not None:
            self.acc = float(accuracy_m)
        if lat is not None or lon is not None:
            self._fix_t = time.time()


class ManualTelemetry(SimTelemetry):
    """Operator-set fixed position (ground camera / known vantage)."""
    name = "manual"

    def __init__(self, **kw):
        kw["drift"] = False
        super().__init__(**kw)
        self.label = "MANUAL"


class MavlinkTelemetry(_Base):
    """Reads GLOBAL_POSITION_INT + ATTITUDE from a MAVLink endpoint, e.g.
    'udpin:0.0.0.0:14550', 'tcp:127.0.0.1:5760', '/dev/ttyACM0'."""
    name = "mavlink"

    def __init__(self, endpoint="udpin:0.0.0.0:14550", **_):
        self.endpoint = endpoint
        self._lock = threading.Lock()
        self._s = {"lat": None, "lon": None, "alt_msl": None, "agl_m": None,
                   "roll": 0.0, "pitch": 0.0, "yaw": 0.0, "heading_deg": 0.0,
                   "fix": False, "source": "MAVLINK", "age_s": 999.0}
        self._last = 0.0

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        from pymavlink import mavutil
        while True:
            try:
                m = mavutil.mavlink_connection(self.endpoint)
                while True:
                    msg = m.recv_match(blocking=True, timeout=5,
                                       type=["GLOBAL_POSITION_INT", "ATTITUDE"])
                    if msg is None:
                        with self._lock:
                            self._s["fix"] = False
                        continue
                    t = msg.get_type()
                    with self._lock:
                        if t == "GLOBAL_POSITION_INT":
                            self._s["lat"] = msg.lat / 1e7
                            self._s["lon"] = msg.lon / 1e7
                            self._s["alt_msl"] = msg.alt / 1000.0
                            self._s["agl_m"] = msg.relative_alt / 1000.0
                            self._s["heading_deg"] = msg.hdg / 100.0
                            self._s["fix"] = self._s["lat"] != 0
                        elif t == "ATTITUDE":
                            self._s["roll"] = msg.roll
                            self._s["pitch"] = msg.pitch
                            self._s["yaw"] = msg.yaw
                        self._last = time.time()
            except Exception as e:
                with self._lock:
                    self._s["fix"] = False
                print("[mavlink] reconnect:", e)
                time.sleep(2)

    def state(self):
        with self._lock:
            s = dict(self._s)
        s["age_s"] = (time.time() - self._last) if self._last else 999.0
        if s["age_s"] > 3:
            s["fix"] = False
        return s


def make_telemetry(cfg):
    kind = (cfg.get("source") or "sim").lower()
    cls = {"sim": SimTelemetry, "manual": ManualTelemetry,
           "mavlink": MavlinkTelemetry}.get(kind, SimTelemetry)
    t = cls(**cfg)
    t.start()
    return t
