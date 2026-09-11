"""
vitals.py — close-range remote pulse (rPPG) + Eulerian-style color magnification.

Each tick it is fed the current frame and a face ROI. It buffers the ROI's mean
colour over time and estimates heart rate (BPM) with the POS algorithm (Wang et
al. 2017) + an FFT peak in the pulse band, and can blend an EVM-magnified version
of the ROI back onto the feed to *show* the pulsation.

CLOSE RANGE ONLY: needs a resolvable, fairly stable face (laptop camera / close
video). It is useless at aerial SAR altitude — faces are too small and platform/
subject motion and compression destroy the sub-percent colour signal.

numpy-only (no scipy) so it adds no new dependencies.
"""
import time
import numpy as np
import cv2

_POS = np.array([[0.0, 1.0, -1.0], [-2.0, 1.0, 1.0]])


class VitalsEngine:
    def __init__(self, window_s=10.0, fmin=0.7, fmax=4.0, patch=64):
        self.window_s = window_s
        self.fmin, self.fmax = fmin, fmax
        self.patch = patch
        self._t = []          # sample timestamps
        self._rgb = []        # mean [r,g,b] per sample
        self._pt = []         # patch timestamps
        self._patches = []    # small ROI patches (float32) for EVM
        self.bpm = 0.0
        self.quality = 0.0
        self._last_calc = 0.0

    def reset(self):
        self._t.clear(); self._rgb.clear()
        self._pt.clear(); self._patches.clear()
        self.bpm = 0.0; self.quality = 0.0; self._last_calc = 0.0

    # ---- ingest ----
    def update(self, frame, roi, now=None):
        now = time.time() if now is None else now
        x1, y1, x2, y2 = self._clip(frame, roi)
        if x2 <= x1 or y2 <= y1:
            return self.status()
        crop = frame[y1:y2, x1:x2]
        m = crop.reshape(-1, 3).mean(axis=0)           # BGR
        self._t.append(now); self._rgb.append([m[2], m[1], m[0]])
        self._pt.append(now)
        self._patches.append(cv2.resize(crop, (self.patch, self.patch)).astype(np.float32))
        tmin = now - self.window_s
        while self._t and self._t[0] < tmin:
            self._t.pop(0); self._rgb.pop(0)
        while self._pt and self._pt[0] < tmin:
            self._pt.pop(0); self._patches.pop(0)
        if now - self._last_calc > 0.5 and self._span() >= 5.0:
            self._compute()
            self._last_calc = now
        return self.status()

    # ---- heart-rate (POS + FFT) ----
    def _compute(self):
        t = np.asarray(self._t); rgb = np.asarray(self._rgb)
        if len(t) < 32:
            return
        fs = 30.0
        ti = np.arange(t[0], t[-1], 1.0 / fs)
        if len(ti) < 64:
            return
        C = np.stack([np.interp(ti, t, rgb[:, i]) for i in range(3)], axis=0)  # 3 x M
        M = C.shape[1]
        win = int(1.6 * fs)
        if M <= win:
            return
        H = np.zeros(M)
        for n in range(0, M - win):
            seg = C[:, n:n + win]
            mu = seg.mean(axis=1, keepdims=True) + 1e-8
            S = _POS @ (seg / mu)
            h = S[0] + (S[0].std() / (S[1].std() + 1e-8)) * S[1]
            H[n:n + win] += (h - h.mean())
        sig = (H - H.mean()) * np.hanning(M)
        ps = np.abs(np.fft.rfft(sig)) ** 2
        freqs = np.fft.rfftfreq(M, d=1.0 / fs)
        band = (freqs >= self.fmin) & (freqs <= self.fmax)
        if not band.any():
            return
        bp = np.where(band, ps, 0.0)
        peak = int(np.argmax(bp))
        self.bpm = float(freqs[peak] * 60.0)
        self.quality = float(bp[peak] / (ps[band].sum() + 1e-8))

    # ---- EVM colour magnification of the ROI (burned into the frame) ----
    def magnify(self, frame, roi, alpha=6.0):
        if len(self._patches) < 40:
            return
        x1, y1, x2, y2 = self._clip(frame, roi)
        if x2 <= x1 or y2 <= y1:
            return
        stack = np.asarray(self._patches)              # T x p x p x 3
        ts = np.asarray(self._pt)
        dur = ts[-1] - ts[0]
        if dur < 3.0:
            return
        fs = len(ts) / dur
        T = stack.shape[0]
        detr = stack - stack.mean(axis=0, keepdims=True)
        F = np.fft.rfft(detr, axis=0)
        freqs = np.fft.rfftfreq(T, d=1.0 / fs)
        mask = ((freqs >= self.fmin) & (freqs <= self.fmax)).astype(np.float32)
        F *= mask[:, None, None, None]
        pulse = np.fft.irfft(F, n=T, axis=0)[-1]       # bandpassed deviation, last frame
        boosted = np.clip(stack[-1] + alpha * pulse, 0, 255).astype(np.uint8)
        frame[y1:y2, x1:x2] = cv2.resize(boosted, (x2 - x1, y2 - y1))

    # ---- helpers ----
    def _span(self):
        return (self._t[-1] - self._t[0]) if len(self._t) > 1 else 0.0

    @staticmethod
    def _clip(frame, roi):
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = [int(v) for v in roi]
        return max(0, x1), max(0, y1), min(w, x2), min(h, y2)

    def status(self):
        return {"bpm": round(self.bpm, 1), "quality": round(self.quality, 2),
                "ready": self.bpm > 0 and self.quality >= 0.25,
                "progress": round(min(1.0, self._span() / 6.0), 2),
                "samples": len(self._t)}
