"""
pipeline.py — the detection + georeferencing engine.

Per frame: SAR YOLO with ByteTrack -> stable track ids -> temporal-persistence
filter (rocks flicker, people persist) + density/clutter flag. Each detection
is geolocked (bbox ground-contact pixel -> lat/lon/MGRS). Locked targets are
reprojected back onto the frame. Overlays are drawn in the browser, not burned
in, so they stay interactive; this module just publishes raw JPEG + state.
"""
import threading
import time
import base64
import cv2
import numpy as np
from ultralytics import YOLO

from geo import Camera, pixel_to_world, world_to_pixel
from vitals import VitalsEngine


class Pipeline:
    def __init__(self, model_path, frames, telemetry, targets, cfg):
        self.frames = frames
        self.telem = telemetry
        self.targets = targets
        self.cfg = cfg
        self.model = YOLO(model_path)
        self.imgsz = cfg.get("imgsz", 960)
        self.conf = cfg.get("conf", 0.25)
        # optional second detector: stock COCO yolo11s (lane-split)
        self.model2 = None
        coco = cfg.get("coco_model")
        if coco:
            self.model2 = YOLO(coco)
            self.imgsz2 = cfg.get("coco_imgsz", 640)
            self.conf2 = cfg.get("coco_conf", 0.35)
            self.coco_classes = cfg.get("coco_classes", [0]) or None
            self.coco_names = self.model2.names
        self.min_hits = cfg.get("min_hits", 3)        # temporal persistence
        self.clutter_max = cfg.get("clutter_max", 40)  # density suppression
        self.ground_anchor = cfg.get("ground_anchor", "bottom")
        cam_cfg = cfg.get("camera", {})
        self._cam_cfg = cam_cfg
        self.cam = None  # built lazily once we know frame size
        self.track_hits = {}
        self.track_seen = {}
        self._n_sar = 0
        self._jpeg = None
        self._state = {"detections": [], "targets": [], "drone": {},
                       "fps": 0.0, "clutter": False, "connected": False}
        self._lock = threading.Lock()
        self.fps = 0.0
        # close-range vitals (rPPG + EVM) — off by default
        self.vitals = VitalsEngine()
        self.vitals_on = False
        self._vit_roi = None
        self._vit_miss = 0
        try:
            self._face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        except Exception:
            self._face_cascade = None

    def _ensure_cam(self, w, h):
        if self.cam is None or self.cam.w != w or self.cam.h != h:
            self.cam = Camera(w, h,
                              hfov_deg=self._cam_cfg.get("hfov_deg", 78.0),
                              mount_tilt_deg=self._cam_cfg.get("mount_tilt_deg", 45.0),
                              mount_yaw_deg=self._cam_cfg.get("mount_yaw_deg", 0.0))

    def set_params(self, **kw):
        for k in ("conf", "min_hits", "clutter_max"):
            if k in kw and kw[k] is not None:
                setattr(self, k, type(getattr(self, k))(kw[k]))
        cam_kw = {}
        for k in ("hfov_deg", "mount_tilt_deg", "mount_yaw_deg"):
            if kw.get(k) is not None:
                self._cam_cfg[k] = float(kw[k])
                cam_kw[k] = float(kw[k])
        if cam_kw and self.cam is not None:
            self.cam.set_mount(self._cam_cfg.get("mount_tilt_deg", 45.0),
                               self._cam_cfg.get("mount_yaw_deg", 0.0))
            self.cam.__init__(self.cam.w, self.cam.h, **{
                "hfov_deg": self._cam_cfg.get("hfov_deg", 78.0),
                "mount_tilt_deg": self._cam_cfg.get("mount_tilt_deg", 45.0),
                "mount_yaw_deg": self._cam_cfg.get("mount_yaw_deg", 0.0)})

    def set_vitals(self, on):
        self.vitals_on = bool(on)
        if not self.vitals_on:
            self.vitals.reset(); self._vit_roi = None; self._vit_miss = 0
        return {"on": self.vitals_on}

    def _detect_face(self, frame):
        try:
            g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            sc = 0.5
            gs = cv2.resize(g, (0, 0), fx=sc, fy=sc)
            faces = self._face_cascade.detectMultiScale(gs, 1.2, 5, minSize=(40, 40))
            if len(faces) == 0:
                return None
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            return (x / sc, y / sc, (x + w) / sc, (y + h) / sc)
        except Exception:
            return None

    def _run_vitals(self, frame):
        """When enabled: track the largest face, estimate BPM, and burn the EVM
        colour-magnified ROI back into the frame. Returns a state dict."""
        if not self.vitals_on:
            return {"on": False}
        face = self._detect_face(frame) if self._face_cascade is not None else None
        if face:
            self._vit_roi = face; self._vit_miss = 0
        elif self._vit_roi is not None:
            self._vit_miss += 1
            if self._vit_miss > 30:
                self._vit_roi = None; self.vitals.reset()
        if self._vit_roi is None:
            return {"on": True, "roi": None, "face": False, "bpm": 0,
                    "quality": 0, "ready": False, "progress": 0, "samples": 0}
        fx1, fy1, fx2, fy2 = self._vit_roi
        iw = (fx2 - fx1) * 0.15; ih = (fy2 - fy1) * 0.15
        st = self.vitals.update(frame, (fx1 + iw, fy1 + ih, fx2 - iw, fy2 - ih))
        try:
            self.vitals.magnify(frame, self._vit_roi)
        except Exception:
            pass
        out = {"on": True, "roi": [fx1, fy1, fx2, fy2], "face": bool(face)}
        out.update(st)
        return out

    def _anchor_pixel(self, x1, y1, x2, y2):
        cx = (x1 + x2) / 2.0
        return (cx, y2) if self.ground_anchor == "bottom" else (cx, (y1 + y2) / 2.0)

    def geolock_pixel(self, u, v):
        d = self.telem.state()
        if self.cam is None or not d.get("fix") or not d.get("agl_m"):
            return None, d
        att = (d["roll"], d["pitch"], d["yaw"])
        return pixel_to_world(self.cam, u, v, att, d["lat"], d["lon"],
                              d["agl_m"]), d

    def thumb_at(self, bbox, frame):
        x1, y1, x2, y2 = [int(c) for c in bbox]
        x1, y1 = max(0, x1), max(0, y1)
        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        crop = cv2.resize(crop, (96, 96))
        ok, buf = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return "data:image/jpeg;base64," + base64.b64encode(buf).decode() if ok else None

    def run(self):
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        last = time.time()
        while True:
            frame, stamp = self.frames.read()
            if frame is None:
                # no feed: still publish live telemetry so the map updates
                drone = self.telem.state()
                with self._lock:
                    self._state = {**self._state, "drone": drone,
                                   "connected": False, "detections": [],
                                   "n_raw": 0,
                                   "targets": self._project_targets(drone)}
                time.sleep(0.1)
                continue
            h, w = frame.shape[:2]
            self._ensure_cam(w, h)
            dets = self._infer(frame, self.model, "sar", self.imgsz,
                               self.conf, [0])
            if self.model2 is not None:
                dets = dets + self._infer(frame, self.model2, "coco",
                                          self.imgsz2, self.conf2,
                                          self.coco_classes)
            self._forget_stale()
            drone = self.telem.state()
            tgts = self._project_targets(drone)
            now = time.time()
            dt = now - last
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt if dt > 0 else 0)
            last = now
            vit = self._run_vitals(frame)        # may burn EVM into the frame
            ok, buf = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, 72])
            with self._lock:
                if ok:
                    self._jpeg = buf.tobytes()
                self._state = {
                    "ts": now, "frame_w": w, "frame_h": h,
                    "detections": dets, "targets": tgts, "drone": drone,
                    "fps": round(self.fps, 1),
                    "clutter": self._n_sar > self.clutter_max,
                    "n_raw": self._n_sar,
                    "n_coco": sum(1 for d in dets if d["src"] == "coco"),
                    "has_coco": self.model2 is not None,
                    "vitals": vit,
                    "connected": self.frames.connected,
                    "params": {"conf": self.conf, "min_hits": self.min_hits,
                               "hfov_deg": self._cam_cfg.get("hfov_deg", 78.0),
                               "mount_tilt_deg": self._cam_cfg.get("mount_tilt_deg", 45.0)},
                }

    def _infer(self, frame, model, src, imgsz, conf, classes):
        names = getattr(model, "names", {}) or {}
        try:
            res = model.track(frame, persist=True, imgsz=imgsz, conf=conf,
                              classes=classes, tracker="bytetrack.yaml",
                              verbose=False)[0]
        except Exception:
            res = model.predict(frame, imgsz=imgsz, conf=conf,
                                classes=classes, verbose=False)[0]
        out = []
        boxes = res.boxes
        n_raw = 0 if boxes is None else len(boxes)
        if src == "sar":
            self._n_sar = n_raw
        if boxes is None:
            return out
        clutter = (src == "sar") and (n_raw > self.clutter_max)
        for b in boxes:
            x1, y1, x2, y2 = [float(v) for v in b.xyxy[0]]
            cval = float(b.conf[0])
            cls = int(b.cls[0]) if b.cls is not None else 0
            tid = int(b.id[0]) if b.id is not None else -1
            key = "%s:%d" % (src, tid)
            if tid >= 0:
                self.track_hits[key] = self.track_hits.get(key, 0) + 1
                self.track_seen[key] = time.time()
            hits = self.track_hits.get(key, 1)
            confirmed = (tid < 0) or (hits >= self.min_hits)
            au, av = self._anchor_pixel(x1, y1, x2, y2)
            geo, _ = self.geolock_pixel(au, av)
            out.append({"src": src, "track_id": tid, "cls": cls,
                        "label": names.get(cls, "obj"),
                        "bbox": [x1, y1, x2, y2], "conf": round(cval, 3),
                        "hits": hits, "confirmed": confirmed,
                        "anchor": [au, av], "geo": geo, "clutter": clutter})
        out.sort(key=lambda d: d["conf"], reverse=True)
        return out

    def _forget_stale(self):
        for k in list(self.track_seen):
            if time.time() - self.track_seen[k] > 3.0:
                self.track_seen.pop(k, None)
                self.track_hits.pop(k, None)

    def _project_targets(self, drone):
        if self.cam is None:
            return []
        att = (drone.get("roll", 0), drone.get("pitch", 0), drone.get("yaw", 0))
        have = drone.get("fix") and drone.get("lat") is not None
        proj = []
        for t in self.targets.list(include_thumbs=False):
            d = {"id": t["id"], "name": t["name"], "status": t["status"],
                 "mgrs": t["mgrs"], "lat": t["lat"], "lon": t["lon"],
                 "u": None, "v": None, "visible": False, "edge_angle": None,
                 "range_m": None}
            if have:
                u, v, vis, ang = world_to_pixel(
                    self.cam, t["lat"], t["lon"], att,
                    drone["lat"], drone["lon"], drone.get("agl_m") or 0)
                d.update({"u": u, "v": v, "visible": vis, "edge_angle": ang})
            proj.append(d)
        return proj

    def jpeg(self):
        with self._lock:
            return self._jpeg

    def state(self):
        with self._lock:
            return dict(self._state)
