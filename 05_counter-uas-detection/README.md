# Counter-UAS Drone Detection — Data to Edge Silicon

A complete **machine-learning lifecycle** for detecting drones/UAS in real time on
commodity edge hardware: dataset engineering → GPU training → INT8 quantization →
deployment on a Hailo AI chip → integration into the SAR operator tool.

## The pipeline, end to end

1. **Multi-dataset merge.** Stock COCO YOLO has no drone class (it calls quadcopters
   birds or kites), and no single public dataset covers the hard cases. I merged **6
   public datasets into one single-class set: 117,471 training / 20,321 validation
   images, ~158k boxes.** All drone-type labels were remapped to one class; bird,
   airplane, and helicopter images were kept as **hard negatives** to fight false
   positives; VOC XML was converted to YOLO; names were split-prefixed to prevent
   label collisions; images were symlinked for near-zero extra disk. The value is in
   the data engineering, not the architecture.
2. **Training (A6000, YOLO11).** YOLO11s, 100 epochs (~36 h): **mAP50 0.802,
   mAP50-95 0.559, precision 0.91, recall 0.77.** A lighter YOLO11n checkpoint for
   tighter budgets.
3. **Edge compile chain.** ONNX → INT8 quantization with a 512-image calibration set →
   Hailo HEF, built for both Hailo-8 and the 5-context Hailo-8L that the Pi actually
   carries.
4. **Deployment (Raspberry Pi 5 + Hailo AI HAT).** **20.9 FPS on-chip**, ~14 FPS
   end-to-end with a live pipeline (USB cam → letterbox → on-chip NMS → IOU persistence
   tracker → annotated output), running fullscreen on the attached display.
5. **Integration.** Added as a third detector lane in SAR Pixel-Lock, switchable live
   from the UI. Airborne targets deliberately get **no ground-plane geolock** (it would
   be wrong for something in the air) — a correctness call that matters operationally.

## Why it matters to an employer

- Proof I can own an **ML problem from raw public data to a shipping edge deployment**,
  including the unglamorous parts (label remapping, hard negatives, quantization
  calibration, FPS on real silicon).
- Counter-UAS is a genuinely open, active problem; this is a working commodity-hardware
  chain for it.

## Stack

Python, Ultralytics YOLO11, PyTorch, ONNX, Hailo DFC / Model Zoo, HailoRT, OpenCV,
Raspberry Pi 5.

## In this folder

- `source_and_reports/counter-uas-drone-detect-report.md` — full build report
  (datasets, metrics, compile gotchas, deployment).
- `source_and_reports/counter-uas-report.txt` — companion notes.
- `source_and_reports/vtx_classifier.py` — a video-transmitter (VTX) signal classifier,
  the RF side of the counter-UAS picture.
- `source_and_reports/hit_uav.py` — engagement/geometry helper.

Note: the training set, weights, and HEFs live on the A6000 and are not copied here.
