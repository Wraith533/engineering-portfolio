"""
app.py — SAR pixel-lock web tool server (FastAPI).

Runs on the A6000. Serves the GUI, the annotated MJPEG feed, a WebSocket
state channel, and REST for locking/managing/exporting targets.
"""
import asyncio
import json
import os
import time

import yaml
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.responses import (HTMLResponse, StreamingResponse, JSONResponse,
                               FileResponse, PlainTextResponse)
from fastapi.staticfiles import StaticFiles

from camera import FrameSource
from telemetry import make_telemetry
from targets import TargetStore
from pipeline import Pipeline
from cot_publisher import CotPublisher

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = yaml.safe_load(open(os.path.join(HERE, os.environ.get("SAR_CONFIG", "config.yaml")),
                          encoding="utf-8"))


def rp(p):
    """Resolve a config path: absolute as-is, else relative to the app dir.
    Lets one config work on Linux and Windows without absolute paths."""
    if not p:
        return p
    return p if os.path.isabs(p) else os.path.join(HERE, p)


frames = FrameSource(**CFG["camera_source"]).start()
if CFG.get("image_folder"):
    frames.set_folder(rp(CFG["image_folder"]))
if CFG.get("video_folder"):
    frames.set_video_folder(rp(CFG["video_folder"]))
telem = make_telemetry(CFG["telemetry"])
targets = TargetStore(rp(CFG.get("targets_file", "targets.json")))
pipe = Pipeline(rp(CFG["model"]), frames, telem, targets, {
    "imgsz": CFG["imgsz"], "conf": CFG["conf"], "min_hits": CFG["min_hits"],
    "clutter_max": CFG["clutter_max"], "ground_anchor": CFG["ground_anchor"],
    "camera": CFG["camera"],
    "coco_model": rp(CFG.get("coco_model")), "coco_imgsz": CFG.get("coco_imgsz", 640),
    "coco_conf": CFG.get("coco_conf", 0.35),
    "coco_classes": CFG.get("coco_classes", [0])})
pipe.run()

_atak = CFG.get("atak", {}) or {}
cot_pub = CotPublisher(targets,
                       group=_atak.get("group"), port=_atak.get("port"),
                       period_s=_atak.get("period_s", 2.0),
                       stale_s=_atak.get("stale_s", 30),
                       iface_ip=_atak.get("iface_ip"),
                       unicast=_atak.get("unicast"))

app = FastAPI()


@app.middleware("http")
async def no_cache(request, call_next):
    """Never let the browser serve a stale GUI — always revalidate HTML/JS/CSS.
    (A cached index.html + fresh app.js mismatch can break startup.)"""
    resp = await call_next(request)
    p = request.url.path
    if p == "/" or p.startswith("/static"):
        resp.headers["Cache-Control"] = "no-store, must-revalidate"
    return resp


app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    return open(os.path.join(HERE, "static", "index.html"), encoding="utf-8").read()


_GUIDE_CSS = """
<style>
:root{color-scheme:dark}
body{margin:0;background:#0a0e12;color:#cfe3ee;
  font-family:'Segoe UI',Roboto,system-ui,sans-serif;line-height:1.6}
.wrap{max-width:860px;margin:0 auto;padding:32px 24px 80px}
h1,h2,h3{color:#fff;line-height:1.25}
h1{font-size:28px;border-bottom:2px solid #28e0a0;padding-bottom:10px;margin-top:0}
h2{font-size:21px;margin-top:38px;border-bottom:1px solid #1d2a33;padding-bottom:6px}
h3{font-size:16px;margin-top:24px;color:#28e0a0}
a{color:#3aa0ff}
code{background:#11202b;color:#9be8c8;padding:1px 5px;border-radius:4px;
  font-family:ui-monospace,Consolas,monospace;font-size:.92em}
pre{background:#0c1318;border:1px solid #1d2a33;border-radius:8px;padding:12px 14px;
  overflow:auto}
pre code{background:none;color:#cfe3ee;padding:0}
blockquote{margin:14px 0;padding:8px 16px;border-left:3px solid #28e0a0;
  background:#0e1620;color:#aac4d4;border-radius:0 6px 6px 0}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:.94em}
th,td{border:1px solid #1d2a33;padding:7px 10px;text-align:left;vertical-align:top}
th{background:#11202b;color:#fff}
tr:nth-child(even) td{background:#0c1318}
hr{border:none;border-top:1px solid #1d2a33;margin:30px 0}
strong{color:#eaf4fb}
.brandbar{font-size:12px;letter-spacing:1px;color:#28e0a0;font-weight:700;margin-bottom:6px}
</style>
"""


@app.get("/guide", response_class=HTMLResponse)
def guide():
    try:
        text = open(os.path.join(HERE, "USER_GUIDE.md"), encoding="utf-8").read()
    except Exception:
        return HTMLResponse("<h1>Guide not found</h1>", status_code=404)
    try:
        import markdown as _md
        body = _md.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    except Exception:
        import html as _html
        body = "<pre>" + _html.escape(text) + "</pre>"
    page = ("<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>SAR Pixel-Lock — Operator Guide</title>" + _GUIDE_CSS +
            "</head><body><div class='wrap'>"
            "<div class='brandbar'>SAR&nbsp;PIXEL-LOCK · 25ID LIGHTNING LABS</div>"
            + body + "</div></body></html>")
    return HTMLResponse(page)


@app.get("/config")
def get_config():
    return {"map": CFG["map"], "model": os.path.basename(CFG["model"])}


@app.get("/video.mjpg")
def video():
    def gen():
        boundary = b"--frame"
        while True:
            j = pipe.jpeg()
            if j is None:
                time.sleep(0.05)
                continue
            yield (boundary + b"\r\nContent-Type: image/jpeg\r\n"
                   b"Content-Length: " + str(len(j)).encode() + b"\r\n\r\n"
                   + j + b"\r\n")
            time.sleep(1 / 25)
    return StreamingResponse(gen(),
                             media_type="multipart/x-mixed-replace; boundary=frame")


@app.post("/ingest")
async def ingest(req: Request):
    frames.submit(await req.body())
    return {"ok": True}


@app.websocket("/ws")
async def ws(sock: WebSocket):
    await sock.accept()
    safe = lambda o: float(o) if hasattr(o, "__float__") else str(o)
    try:
        while True:
            await sock.send_text(json.dumps(pipe.state(), default=safe))
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@app.post("/lock")
async def lock(req: Request):
    body = await req.json()
    if "bbox" in body and body["bbox"]:
        x1, y1, x2, y2 = body["bbox"]
        u, v = pipe._anchor_pixel(x1, y1, x2, y2)
    else:
        u, v = float(body["u"]), float(body["v"])
    geo, drone = pipe.geolock_pixel(u, v)
    if geo is None:
        return JSONResponse({"ok": False,
                             "error": "no fix / no AGL — cannot georeference"},
                            status_code=400)
    thumb = None
    fr, _ = frames.read()
    if fr is not None and body.get("bbox"):
        thumb = pipe.thumb_at(body["bbox"], fr)
    t = targets.add(lat=geo["lat"], lon=geo["lon"], mgrs=geo["mgrs"],
                    agl_m=drone.get("agl_m"), conf=body.get("conf"),
                    thumb=thumb, range_m=geo["range_m"],
                    bearing_deg=geo["bearing_deg"], now=time.time())
    return {"ok": True, "target": t}


@app.get("/targets")
def list_targets():
    return targets.list()


@app.patch("/targets/{tid}")
async def patch_target(tid: str, req: Request):
    t = targets.update(tid, **(await req.json()))
    return t or JSONResponse({"error": "not found"}, status_code=404)


@app.delete("/targets/{tid}")
def del_target(tid: str):
    return {"ok": bool(targets.delete(tid))}


@app.post("/params")
async def params(req: Request):
    pipe.set_params(**(await req.json()))
    return {"ok": True}


@app.get("/source")
def source_status():
    return frames.source_status()


@app.post("/source")
async def source_set(req: Request):
    body = await req.json()
    if "mode" in body:
        frames.set_mode(body["mode"])
    if body.get("step"):
        frames.step(body["step"])
    if "goto" in body:
        frames.goto(body["goto"])
    if body.get("rescan"):
        frames.rescan()
        frames.rescan_videos()
    return frames.source_status()


@app.post("/telem/manual")
async def telem_manual(req: Request):
    telem.set_manual(**(await req.json()))
    return {"ok": True}


@app.get("/vitals")
def vitals_status():
    return {"on": pipe.vitals_on}


@app.post("/vitals")
async def vitals_set(req: Request):
    body = await req.json()
    return pipe.set_vitals(body.get("enabled"))


@app.get("/atak")
def atak_status():
    return cot_pub.status()


@app.post("/atak")
async def atak_toggle(req: Request):
    body = await req.json()
    return cot_pub.set_enabled(body.get("enabled"))


@app.get("/export/geojson")
def export_geojson():
    return JSONResponse(targets.geojson(), headers={
        "Content-Disposition": "attachment; filename=sar_targets.geojson"})


@app.get("/export/cot", response_class=PlainTextResponse)
def export_cot():
    return Response(targets.cot(), media_type="application/xml", headers={
        "Content-Disposition": "attachment; filename=sar_targets_cot.xml"})


def ensure_cert(cert, key):
    """Generate a self-signed cert with the cryptography lib if it's missing
    (so Windows needs no openssl). Returns True if cert+key exist/created."""
    if os.path.exists(cert) and os.path.exists(key):
        return True
    try:
        import datetime
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"sar-gui")])
        san = x509.SubjectAlternativeName([x509.DNSName(u"localhost"),
                                           x509.IPAddress(__import__("ipaddress").ip_address("127.0.0.1"))])
        now = datetime.datetime.utcnow()
        cert_obj = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                    .public_key(k.public_key()).serial_number(x509.random_serial_number())
                    .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=825))
                    .add_extension(san, critical=False)
                    .sign(k, hashes.SHA256()))
        with open(key, "wb") as f:
            f.write(k.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()))
        with open(cert, "wb") as f:
            f.write(cert_obj.public_bytes(serialization.Encoding.PEM))
        print("generated self-signed cert:", cert)
        return True
    except Exception as e:
        print("cert generation skipped (%s) — serving HTTP" % e)
        return False


if __name__ == "__main__":
    srv = CFG["server"]
    ssl = {}
    cert, key = rp(srv.get("ssl_certfile")), rp(srv.get("ssl_keyfile"))
    if cert and key and ensure_cert(cert, key):
        ssl = {"ssl_certfile": cert, "ssl_keyfile": key}
        print("HTTPS on :%d (self-signed)" % srv["port"])
    else:
        print("HTTP on :%d  (browser GPS only works via localhost or HTTPS)" % srv["port"])
    uvicorn.run(app, host=srv["host"], port=srv["port"],
                log_level="warning", **ssl)
