"""
camera.py — pluggable frame source feeding a single latest-frame buffer.

Sources (config 'source' string):
  device:0            local /dev/video0 (USB cam, e.g. on the Orin)
  url:http://host/x   pull an MJPEG/RTSP/HTTP stream (laptop relay, IP cam)
  rtsp://...          shorthand for url:
  file:/path.mp4      loop a video file (test on real drone footage)
  push                frames are POSTed in by a client (laptop webcam -> A6000)
"""
import os
import threading
import time
import numpy as np
import cv2

_IS_WIN = os.name == "nt"


class FrameSource:
    def __init__(self, source="push", width=1280, height=720, fps=30):
        self.source = source
        self.req_w, self.req_h = width, height
        self.fps = fps
        self._frame = None
        self._lock = threading.Lock()
        self._stamp = 0.0
        self._connected = False
        self.kind = source.split(":", 1)[0] if ":" in source else source
        if source.startswith(("rtsp://", "http://", "https://")):
            self.kind, self._arg = "url", source
        elif ":" in source:
            self.kind, self._arg = source.split(":", 1)
        else:
            self.kind, self._arg = source, ""
        # --- alternate feed sources: "folder" (pictures) / "video" (clips) ---
        self.mode = "live"          # "live" = source above, "folder", or "video"
        self.folder = None
        self._images = []
        self._idx = 0
        self.video_folder = None
        self._videos = []
        self._vidx = 0

    def start(self):
        if self.kind != "push":
            threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._video_loop, daemon=True).start()
        return self

    def submit(self, jpeg_bytes):
        """Ingest endpoint for push source. Ignored unless we're in Live mode,
        so a pushing client (e.g. OAK) doesn't fight Pictures/Video playback."""
        if self.mode != "live":
            return
        arr = np.frombuffer(jpeg_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            self._set(img)

    def _capture_loop(self):
        while True:
            cap = self._open()
            if not cap or not cap.isOpened():
                self._connected = False
                time.sleep(1.0)
                continue
            self._connected = True
            while True:
                ok, frame = cap.read()
                if not ok:
                    if self.kind == "file":
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # loop
                        continue
                    break
                if self.mode == "live":      # in folder mode we hold the picture
                    self._set(frame)
                if self.kind == "file" or self.mode != "live":
                    time.sleep(1.0 / max(self.fps, 1))
            cap.release()
            self._connected = False
            time.sleep(0.5)

    def _open(self):
        if self.kind == "device":
            idx = int(self._arg or 0)
            # DirectShow backend opens USB/integrated cams reliably on Windows
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if _IS_WIN else cv2.VideoCapture(idx)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.req_w)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.req_h)
            return cap
        if self.kind in ("url", "file"):
            return cv2.VideoCapture(self._arg)
        return None

    def _set(self, img):
        with self._lock:
            self._frame = img
            self._stamp = time.time()
            self._connected = True

    def read(self):
        with self._lock:
            if self._frame is None:
                return None, 0.0
            return self._frame.copy(), self._stamp

    @property
    def connected(self):
        if self.mode == "folder":
            return bool(self._images)
        return self._connected and (time.time() - self._stamp) < 3.0

    # ---------- still-image folder + video-clip playback ----------
    _IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff")
    _VID_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm")

    @staticmethod
    def _scan(folder, exts):
        out = []
        if folder and os.path.isdir(folder):
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(exts):
                    out.append(os.path.join(folder, f))
        return out

    def set_folder(self, path):
        self.folder = path
        self.rescan()

    def set_video_folder(self, path):
        self.video_folder = path
        self.rescan_videos()

    def rescan(self):
        self._images = self._scan(self.folder, self._IMG_EXTS)
        if self._idx >= len(self._images):
            self._idx = 0
        if self.mode == "folder":
            self._load_current()
        return len(self._images)

    def rescan_videos(self):
        self._videos = self._scan(self.video_folder, self._VID_EXTS)
        if self._vidx >= len(self._videos):
            self._vidx = 0
        return len(self._videos)

    def set_mode(self, mode):
        if mode in ("live", "folder", "video"):
            self.mode = mode
            if mode == "folder":
                self.rescan()
                self._load_current()
            elif mode == "video":
                self.rescan_videos()
        return self.source_status()

    def _load_current(self):
        if not self._images:
            return
        self._idx %= len(self._images)
        img = cv2.imread(self._images[self._idx])
        if img is not None:
            self._set(img)

    def step(self, d):
        if self.mode == "video":
            if self._videos:
                self._vidx = (self._vidx + int(d)) % len(self._videos)
        elif self._images:
            self._idx = (self._idx + int(d)) % len(self._images)
            self._load_current()
        return self.source_status()

    def goto(self, i):
        if self.mode == "video":
            if self._videos:
                self._vidx = int(i) % len(self._videos)
        elif self._images:
            self._idx = int(i) % len(self._images)
            self._load_current()
        return self.source_status()

    def _video_loop(self):
        """Play the selected clip (looping) while in video mode; downscale 4K
        to 1080p so display/encode stays smooth (inference uses imgsz anyway)."""
        while True:
            if self.mode != "video" or not self._videos:
                time.sleep(0.15)
                continue
            cur = self._vidx
            cap = cv2.VideoCapture(self._videos[cur])
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            delay = 1.0 / max(fps, 1)
            while self.mode == "video" and self._vidx == cur:
                ok, frame = cap.read()
                if not ok:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                if frame.shape[1] > 1920:
                    sc = 1920.0 / frame.shape[1]
                    frame = cv2.resize(frame, (1920, int(frame.shape[0] * sc)))
                self._set(frame)
                time.sleep(delay)
            cap.release()

    def source_status(self):
        if self.mode == "video":
            name = os.path.basename(self._videos[self._vidx]) if self._videos else None
            return {"mode": self.mode, "index": self._vidx,
                    "count": len(self._videos), "file": name,
                    "folder": self.video_folder}
        name = os.path.basename(self._images[self._idx]) if (self.mode == "folder" and self._images) else None
        return {"mode": self.mode, "index": self._idx,
                "count": len(self._images), "file": name, "folder": self.folder}
