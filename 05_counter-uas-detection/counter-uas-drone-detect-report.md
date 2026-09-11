# Counter-UAS Drone Detection — Project Report

**Dates:** 2026-08-07 → 08-09 (build sprint) · **Author:** William + Claude
**Goal:** a drone/UAS detector trained on public data, running in real time on a Pi 5 (16 GB) with a Hailo AI HAT, feeding the existing SAR Pixel-Lock GUI and (next) the GCS/ATAK/drone ecosystem.

---

## Why

- Counter-UAS detection is an open, active problem (lab partnership context: the institutional version of this is stalled — a working commodity-hardware chain is genuinely valuable).
- Every usable drone detector is a fine-tune: stock COCO YOLO has no drone class (calls quadcopters birds/kites/airplanes).
- No single public dataset covers the hard cases (tiny long-range targets, drone-vs-bird false positives, cluttered backgrounds) — the value is in the **multi-dataset merge**, not the architecture.
- End-to-end story (data engineering → GPU training → INT8 quantization → edge silicon → operational GUI) is also a portfolio piece for the civilian transition.

## What we built

1. **Dataset merge** (a6000, `/mnt/ssd/yolo/drone-detect/`): 6 public datasets → one single-class (drone) YOLO set, **117,471 train / 20,321 val images, ~158k boxes**. All drone-type labels remapped to class 0; bird/airplane/helicopter boxes dropped so their images act as hard negatives; DUT's VOC XML converted; output names split-prefixed to prevent label collisions; images symlinked (near-zero extra disk).
2. **Training** (A6000 GPU, ultralytics YOLO11):
   - **YOLO11s** — 100 epochs, ~36 h: **mAP50 0.802 · mAP50-95 0.559 · P 0.91 · R 0.77** → `runs/yolo11s-drone-v1/weights/best.pt`
   - **YOLO11n** — stopped at epoch 78 (deck-clearing): mAP50 0.759, usable checkpoint at `runs/yolo11n-drone-v1/weights/best.pt`
3. **Hailo compile chain** (a6000 `hailo-venv`): DFC 3.34.0 + Model Zoo 5.4 (patched — see gotchas) → ONNX → INT8 quantize (512-image calib set) → HEF.
   - `yolo11s-drone-v1.hef` (full Hailo-8, single-context)
   - `yolo11s-drone-v1-8l.hef` (Hailo-**8L**, 5-context — what the Pi actually has)
4. **Pi 5 deployment** (`pi5@<lan-ip>`, `~/drone-detect/`): HailoRT 4.23 verified; **20.9 FPS on-chip benchmark**; `drone_watch.py` live pipeline (USB cam 1080p MJPEG → letterbox → HEF w/ on-chip NMS → IOU persistence tracker → annotated display/save/stdout), ~14 FPS end-to-end, runs fullscreen on the attached screen (`--show`), tunable `--conf/--min-hits` (sensitivity raised to 0.2/2 for swarm demos). SAR kiosk autostart disabled (`sar-kiosk.desktop.disabled_drone`); relay services untouched.
5. **SAR GUI integration** (a6000 `:8080`): drone model added as a third detector lane — DETECTOR dropdown (SAR / UAS / Both) switches server-side live via `POST /detector`; UAS boxes red, own layer toggle, counted in the top bar; airborne targets deliberately get **no ground-plane geolock** (would be wrong); originals backed up `*.bak_drone`.
6. **Demo media**: model-verified stock set in the GUI — 5 images (0.54–0.83 conf) + 3 videos (2 Anti-UAV benchmark clips 8/8 frames, 1 BLM training clip 8/9). Non-detecting pulls culled.

## Datasets

| Dataset | Size | Role in v1 | Status |
|---|---|---|---|
| seraphim (HF, lgrzybowski) | 8.6 GB, 83k imgs | bulk of training set (curated from 23 sources) | **merged** |
| DUT Anti-UAV (Dalian Univ.) | 2.7 GB, ~10k | ground-to-air benchmark; val credibility | **merged** (VOC→YOLO) |
| multiclass-drone (Kaggle, troykueh) | 2.5 GB | military types (shahed, MQ-9, mavic, mohajer) | **merged** |
| bird-vs-drone (Kaggle, stealthknight) | 1.2 GB, 12.5k | drones labeled, birds unlabeled = hard negatives | **merged** |
| cybersimar08 drone-detection (Kaggle) | 692 MB | drone class kept; airplane/heli imgs as negatives | **merged** |
| muki2003 yolo-drone (Kaggle) | 373 MB | general drone images | **merged** |
| Anti-UAV300 (CVPR benchmark) | 12 GB | RGB + **thermal** video — v2 thermal lever | downloaded, needs frame extraction |
| Cranfield synthetic (HF, mazqtpopx) | 51 GB | synthetic pretrain + 20–320 m range series | downloaded; Images+Masks only → needs mask→bbox converter |
| Det-Fly (Westlake Univ.) | ~? | **air-to-air** (drone filming drone) — key for drone-mounted camera | NOT downloaded (OneDrive folder defeats scripting — manual click) |
| UETT4K | 33k 4K imgs | long-range tiny targets | not downloaded (SharePoint, manual; storage-heavy) |
| DroneSOD-30K / SynDroneVision | — | — | not publicly released |

## Key gotchas (also in project memory)

- Hailo DFC 3.34 **does** support hailo8 — Model Zoo 5.4 de-lists it in 3 places (CLI choices, per-network yaml `supported_hw_arch`, nuscenes import); patched copies live in `/tmp/hailo_model_zoo` on the a6000.
- `lspci` says "Hailo-8" but the Pi's chip is **Hailo-8L** (fw identify tells the truth); hailo8 HEFs don't run on 8L — compile with `--hw-arch hailo8l`.
- hailo-venv: numpy must stay 1.26.4 / scipy 1.12.0 (DFC pins).
- Pi 5 has **no hardware H.264 encoder** — plan 720p software encode for RTSP.
- On-chip NMS floors score threshold ~0.2 — going lower needs an HEF recompile.
- Training was CPU-starved (3× slower) whenever sweep_spectra ran; future runs: batch 96–128, workers 16 for ~2× throughput.

## What's left

**Near-term (demo hardening)**
- Per-dataset eval breakdown of 11s (find the weak regime — likely tiny/distant targets)
- Compile 11n (epoch-78 checkpoint) for 8L → higher-FPS fallback; optionally finish its training
- Tiling (2×2) mode in `drone_watch.py` for swarm/long-range at ~4× FPS cost
- Pi autostart of the live detector (replace the disabled kiosk) if desired

**ATAK / GCS integration (designed, not built)**
- mediamtx RTSP on the Pi, 720p burned-in boxes → SPI CoT with video link via existing `cot_relay.py` → EUD
- Lock panel: slim web UI on the Pi (SAR-GUI pattern) — tap box → lock track ID → publish per-target CoT (bearing-only first)
- KLV/MISB VMTI metadata stream — only if downstream consumers need it

**Two-camera architecture (sentry + pursuer — agreed direction)**
- GCS sentry: YOLO11l/x on the Legion 4090, wide stare + tiling; tracks (not video) over the mesh
- Pi5 as hub: track fusion, ATAK publish, cue arbitration
- Drone (ERNA Orin): Det-Fly manual download → air-to-air fine-tune → pixel-lock reacquire on cue
- Triangulation: dual bearings → true 3D position (solves the range problem); needs pointing calibration + NTP time sync
- Correlation/handoff logic for multi-target (swarm) scenes

**Model v2 levers**
- Thermal: extract Anti-UAV300 IR frames → fine-tune (night capability, differentiator)
- Synthetic: Cranfield mask→bbox converter → pretrain-then-finetune experiment
- Own footage: fly the drones past a tripod camera → autolabel (`/mnt/ssd/training/` SAR pipeline) → label-studio review → retrain

## Where everything lives

- a6000: `/mnt/ssd/yolo/drone-detect/` (datasets, merged set, runs, HEFs, hailo-venv, calib); SAR GUI `/mnt/ssd/sar_gui_test/` (`:8080`)
- Pi 5: `~/drone-detect/` (`drone_watch.py`, `yolo11s-drone-v1-8l.hef`, logs)
- Laptop: `~/Downloads/yolo11s-drone-v1.hef` (full Hailo-8 build), this report
