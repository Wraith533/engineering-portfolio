import os
from roboflow import Roboflow
rf = Roboflow(api_key=os.environ["ROBOFLOW_KEY"])
candidates = [
    ("hituav-dataset-for-yolov5", "hit-uav-for-yolov5-rjdrs"),
    ("datasetsenhance", "hit-uav-xl17h"),
    ("thermal-disasters-project", "thermal-human-detection-from-uav"),
]
for ws, pj in candidates:
    try:
        proj = rf.workspace(ws).project(pj)
        vers = [int(str(v.version).split("/")[-1]) for v in proj.versions()]
        print("FOUND", ws, "/", pj, "versions:", vers)
        if not vers:
            continue
        for v in sorted(vers, reverse=True):
            try:
                proj.version(v).download("yolov11",
                    location="/mnt/ssd/training/datasets/thermal/hit-uav", overwrite=False)
                print("DOWNLOADED hit-uav v", v, "from", ws)
                break
            except Exception as e:
                print("  v", v, "failed:", repr(e)[:80])
        break
    except Exception as e:
        print("probe failed", ws, "/", pj, ":", repr(e)[:120])
print("__HITUAV_DONE__")
