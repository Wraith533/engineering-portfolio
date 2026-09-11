# SAR Pixel-Lock — Detect, Geolocate, Track

An operator tool for drone **search and rescue**. It runs a custom-trained person
detector on a live drone feed, and lets the operator **click any detection to
"pixel-lock" it to a real-world map grid (MGRS)**. Locked targets stay pinned on both
a map and the video, survive the drone moving, and can be streamed live to ATAK or
exported.

## The interesting engineering

- **Pixel → world geolocation.** A clicked pixel is cast as a camera ray through the
  camera intrinsics, mount tilt, and live drone attitude, then intersected with the
  ground plane at the drone's above-ground height to produce lat/lon → MGRS. The target
  is stored as a **world coordinate**, so it stays put on the map and **reprojects back
  onto the moving video feed** (off-screen targets get an edge arrow).
- **Telemetry fusion.** Georeferencing is driven by real MAVLink telemetry
  (`GLOBAL_POSITION_INT` + `ATTITUDE`) from the Cube, with sim and manual-vantage modes
  for the bench — and an honest "SIM" badge so no one confuses a test for a fix.
- **Dual-lane detection.** A custom SAR model (strong on small, distant, prone, aerial
  people) runs alongside a stock COCO model (strong on close, upright people) on every
  frame.
- **Alert-fatigue controls.** A recall-tuned model plus a ByteTrack persistence gate
  (a track must survive N frames before it's shown) — because false-positive spam was
  the model's #1 operational blocker, and I designed for that.
- **CoT / ATAK output** (`cot_publisher.py`) so detections flow into the tactical
  picture other tools already use. Android shell (`sar-android/`, "Huginn") wraps the
  same web console for a phone over Tailscale.

## Why it matters to an employer

- End-to-end **applied computer vision**: a trained model, real geospatial math, live
  telemetry, and an interface built around an actual operator's failure modes — not a
  notebook demo.
- Runs on real GPUs (A6000 / RTX 5090) and integrates with a broader system.

## Stack

Python, YOLO (Ultralytics), ByteTrack, OpenCV, MAVLink/pymavlink, MGRS/geodesy,
Flask-style web UI, Cursor-on-Target (CoT)/ATAK, Android WebView.

## In this folder

- `sar_gui/` — the packaged tool (app, camera, pipeline, geo, `USER_GUIDE.md`).
- `sar_gui_work/` — working version with the telemetry/vitals/CoT modules.
- `sar-android/` — the Android front end.

Note: model weights and captured footage are omitted; code and docs are included.
