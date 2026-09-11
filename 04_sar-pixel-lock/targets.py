"""
targets.py — persistent store of locked SAR targets.

Each target is world-anchored (lat/lon/mgrs) so it survives across frames,
camera motion and restarts. Numbered TGT-01.. with editable name/status/notes.
Exports GeoJSON and ATAK Cursor-on-Target (ties into erna-atak-cot pipeline).
"""
import json
import os
import threading
import time

STATUSES = ("active", "found", "dismissed")


class TargetStore:
    def __init__(self, path="targets.json"):
        self.path = path
        self._lock = threading.Lock()
        self._targets = {}
        self._seq = 0
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                d = json.load(open(self.path))
                self._targets = {t["id"]: t for t in d.get("targets", [])}
                self._seq = d.get("seq", len(self._targets))
            except Exception as e:
                print("[targets] load failed:", e)

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"seq": self._seq,
                       "targets": list(self._targets.values())}, f, indent=2)
        os.replace(tmp, self.path)

    def add(self, lat, lon, mgrs, agl_m=None, conf=None, thumb=None,
            pixel=None, range_m=None, bearing_deg=None, now=None):
        with self._lock:
            self._seq += 1
            tid = "TGT-%02d" % self._seq
            t = {"id": tid, "name": tid, "lat": lat, "lon": lon, "mgrs": mgrs,
                 "agl_m": agl_m, "conf": conf, "thumb": thumb,
                 "range_m": range_m, "bearing_deg": bearing_deg,
                 "status": "active", "notes": "",
                 "created": now or time.time()}
            self._targets[tid] = t
            self._save()
            return t

    def update(self, tid, **fields):
        with self._lock:
            t = self._targets.get(tid)
            if not t:
                return None
            for k, v in fields.items():
                if k in ("name", "notes", "status", "lat", "lon", "mgrs"):
                    t[k] = v
            self._save()
            return t

    def delete(self, tid):
        with self._lock:
            t = self._targets.pop(tid, None)
            self._save()
            return t

    def list(self, include_thumbs=True):
        with self._lock:
            out = []
            for t in self._targets.values():
                d = dict(t)
                if not include_thumbs:
                    d.pop("thumb", None)
                out.append(d)
            return out

    def geojson(self):
        feats = []
        for t in self.list(include_thumbs=False):
            feats.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [t["lon"], t["lat"]]},
                "properties": {k: t[k] for k in
                               ("id", "name", "mgrs", "status", "notes",
                                "conf", "created") if k in t},
            })
        return {"type": "FeatureCollection", "features": feats}

    def cot(self):
        """ATAK Cursor-on-Target XML events (one per active target)."""
        evs = []
        for t in self.list(include_thumbs=False):
            if t["status"] == "dismissed":
                continue
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t["created"]))
            evs.append(
                f'<event version="2.0" uid="SAR.{t["id"]}" '
                f'type="a-u-G" how="m-g" time="{ts}" start="{ts}" stale="{ts}">'
                f'<point lat="{t["lat"]:.7f}" lon="{t["lon"]:.7f}" '
                f'hae="0" ce="15" le="15"/>'
                f'<detail><contact callsign="{t["name"]}"/>'
                f'<remarks>{t["mgrs"]} {t["status"]} {t["notes"]}</remarks>'
                f'</detail></event>')
        return "<?xml version='1.0'?>\n" + "\n".join(evs)
