#!/usr/bin/env python3
# HackRF pentest control panel — authorized RF assessment use.
# Modes: GPS spoof | Transmit (noise/jam sim) | Capture (RX to file) | Replay (capture->TX)
# Plain-language target picker; custom freq; gain sweep; amp; band logging.
# *** Radiating = authorized engagement / RF chamber only. Operator is responsible. ***
import os, json, glob, time, datetime, threading, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from listen_engine import LISTENER

HOME    = os.path.expanduser("~")
SIMDIR  = os.path.join(HOME, "gps-sdr-sim")
SIM     = os.path.join(SIMDIR, "gps-sdr-sim")
GPS_IQ  = os.path.join(SIMDIR, "live.bin")
NOISE_IQ= os.path.join(SIMDIR, "noise20.bin")
CAPDIR  = os.path.join(HOME, "captures")
DUR     = os.environ.get("DUR", "60")
PORT    = int(os.environ.get("PORT", "8080"))
os.makedirs(CAPDIR, exist_ok=True)

# Targets named in PLAIN LANGUAGE — what the device IS, with the freq behind it.
# bw = MHz wide (= sample rate). Custom field overrides. Add a line to extend.
PRESETS = [
    {"id":"cam24", "label":"📷 WiFi security cameras (2.4GHz)",   "mhz":2437,   "bw":20},
    {"id":"cam5",  "label":"📷 WiFi cameras (5GHz)",             "mhz":5180,   "bw":20},
    {"id":"wifi24","label":"📶 WiFi / router — 2.4GHz",          "mhz":2437,   "bw":20},
    {"id":"wifi5", "label":"📶 WiFi / router — 5GHz",            "mhz":5500,   "bw":20},
    {"id":"bt",    "label":"🦷 Bluetooth / BLE devices",         "mhz":2402,   "bw":2},
    {"id":"zwave", "label":"🏠 Z-Wave / Zigbee smart-home (US)", "mhz":915,    "bw":2},
    {"id":"fob",   "label":"🔑 Car key fobs / remotes (433)",    "mhz":433.92, "bw":2},
    {"id":"fob315","label":"🔑 Key fobs / TPMS / garage (315)",  "mhz":315,    "bw":2},
    {"id":"lora",  "label":"📡 LoRa / IoT sensors (915)",        "mhz":915,    "bw":2},
    {"id":"alarm", "label":"🚨 Alarm sensors / LoRa (868 EU)",   "mhz":868,    "bw":2},
    {"id":"nfc",   "label":"💳 RFID / NFC badges (13.56)",       "mhz":13.56,  "bw":2},
    {"id":"drone", "label":"🚁 Drone control / FPV video (5.8G)","mhz":5800,   "bw":20},
    {"id":"dect",  "label":"☎️ DECT cordless phones (1.88G)",    "mhz":1880,   "bw":10},
    {"id":"adsb",  "label":"✈️ ADS-B aircraft (1090)",          "mhz":1090,   "bw":2},
    {"id":"iss",   "label":"🛰️ ISS voice / SSTV images (145.8)", "mhz":145.800,"bw":2},
    {"id":"issu",  "label":"🛰️ ISS UHF repeater (437.8)",       "mhz":437.800,"bw":2},
    {"id":"issap", "label":"🛰️ ISS APRS packet (145.825)",      "mhz":145.825,"bw":2},
    {"id":"noaa",  "label":"🛰️ NOAA weather sat APT (137.5)",   "mhz":137.500,"bw":2},
    {"id":"cell9", "label":"📱 Cellular GSM/LTE (900)",          "mhz":900,    "bw":10},
    {"id":"cell18","label":"📱 Cellular GSM/LTE (1800)",         "mhz":1800,   "bw":10},
    {"id":"gps",   "label":"🛰️ GPS L1 (use GPS-spoof mode)",     "mhz":1575.42,"bw":2},
]
PRESET_BY_ID = {p["id"]: p for p in PRESETS}

state = {"mode":"gps",          # gps | tx | capture
         "lat":40.8448, "lon":-73.8648,
         "preset":"cam24", "customf":0, "bw":20,
         "gain":30, "amp":0,
         "tx":False, "rx":False,
         "lastcap":"", "status":"idle",
         "msg":"GPS-spoof mode: click the map, then Start."}

proc=None; proc_lock=threading.Lock()
gen_cv=threading.Condition(); pending={"req":None}

def find_eph():
    c=sorted(glob.glob(os.path.join(SIMDIR,"brdc*.[0-9][0-9]n")))
    return c[-1] if c else os.path.join(SIMDIR,"brdc1510.26n")

# ---- ISS pass prediction (skyfield + cached TLE) ----
_tle_cache={"t":0,"lines":None}
def get_iss_tle():
    import urllib.request
    if _tle_cache["lines"] and (time.time()-_tle_cache["t"]<6*3600):
        return _tle_cache["lines"]
    url="https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=tle"
    raw=urllib.request.urlopen(url,timeout=10).read().decode()
    lines=[l.strip() for l in raw.splitlines() if l.strip()]
    _tle_cache.update({"t":time.time(),"lines":lines})
    return lines

def iss_passes(lat,lon,hours=24,min_elev=10.0):
    """Return upcoming ISS passes over (lat,lon) in the next `hours`."""
    from skyfield.api import load, wgs84, EarthSatellite
    l=get_iss_tle()                          # [name, line1, line2]
    ts=load.timescale()
    sat=EarthSatellite(l[1],l[2],l[0],ts)
    obs=wgs84.latlon(lat,lon)
    t0=ts.now(); t1=ts.tt_jd(t0.tt+hours/24.0)
    times,events=sat.find_events(obs,t0,t1,altitude_degrees=min_elev)
    passes=[]; cur={}
    for t,e in zip(times,events):
        if e==0: cur={"rise":t.utc_iso()}
        elif e==1:
            alt,az,_=(sat-obs).at(t).altaz()
            cur["peak"]=t.utc_iso(); cur["max_elev"]=round(alt.degrees,1)
        elif e==2:
            cur["set"]=t.utc_iso()
            if "rise" in cur: passes.append(cur)
            cur={}
    return passes

def kill_proc(keep_listen=False):
    global proc
    if not keep_listen:
        LISTENER.stop()          # free the radio from the listen pipeline
    with proc_lock:
        if proc and proc.poll() is None:
            proc.terminate()
            try: proc.wait(3)
            except Exception: proc.kill()
        proc=None
    state["tx"]=False; state["rx"]=False

def rf_mhz():
    if state["customf"] and state["customf"]>0: return state["customf"]
    return PRESET_BY_ID.get(state["preset"],PRESETS[0])["mhz"]

def label_now():
    if state["customf"] and state["customf"]>0: return "%g MHz (custom)"%state["customf"]
    return PRESET_BY_ID.get(state["preset"],PRESETS[0])["label"]

def start_tx():
    """Transmit noise (jam/interference sim) on the selected band."""
    global proc
    if not os.path.exists(NOISE_IQ):
        state["status"]="error"; state["msg"]="Missing noise file — run make_noise.py."; return False
    kill_proc()
    mhz=rf_mhz(); bw=max(2,min(20,int(state["bw"])))
    with proc_lock:
        proc=subprocess.Popen(
            ["hackrf_transfer","-t",NOISE_IQ,"-f",str(int(mhz*1e6)),"-s",str(bw*10**6),
             "-a",str(state["amp"]),"-x",str(state["gain"]),"-R"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    state["tx"]=True; state["status"]="transmitting"
    state["msg"]="TRANSMITTING — %s  %g MHz  amp %s  gain %d dB"%(
        label_now(),mhz,"ON(MAX)" if state["amp"] else "off",state["gain"])
    return True

def start_gps_tx():
    global proc
    if not os.path.exists(GPS_IQ):
        state["status"]="error"; state["msg"]="No GPS IQ yet — click the map first."; return False
    kill_proc()
    with proc_lock:
        proc=subprocess.Popen(
            ["hackrf_transfer","-t",GPS_IQ,"-f","1575420000","-s","2600000",
             "-a",str(state["amp"]),"-x",str(state["gain"]),"-R"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    state["tx"]=True; state["status"]="transmitting"
    state["msg"]="GPS SPOOF — %.5f, %.5f  gain %d dB"%(state["lat"],state["lon"],state["gain"])
    return True

def start_capture(secs):
    """Receive (RX) the selected band to a timestamped file for offline analysis."""
    global proc
    kill_proc()
    mhz=rf_mhz(); bw=max(2,min(20,int(state["bw"])))
    sr=bw*10**6
    fn="cap_%dMHz_%dMsps_%s.iq"%(int(mhz),bw,time.strftime("%Y%m%d_%H%M%S"))
    path=os.path.join(CAPDIR,fn)
    nsamp=int(sr*secs)
    with proc_lock:
        # LNA + VGA gains fixed reasonable for RX; -n limits length
        proc=subprocess.Popen(
            ["hackrf_transfer","-r",path,"-f",str(int(mhz*1e6)),"-s",str(sr),
             "-l","32","-g","40","-n",str(nsamp)],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    state["rx"]=True; state["status"]="capturing"; state["lastcap"]=fn
    state["msg"]="CAPTURING %ds — %s  %g MHz  -> %s"%(secs,label_now(),mhz,fn)
    # watcher: when capture process ends, flip back to idle
    def watch(p,f):
        p.wait()
        if state.get("rx"):
            state["rx"]=False; state["status"]="idle"
            sz=os.path.getsize(os.path.join(CAPDIR,f)) if os.path.exists(os.path.join(CAPDIR,f)) else 0
            state["msg"]="Capture done: %s (%d MB). Ready."%(f,sz//(1<<20))
    threading.Thread(target=watch,args=(proc,fn),daemon=True).start()
    return True

def replay_file(fn, srate_hz):
    """Retransmit a previously captured IQ file on the selected band."""
    global proc
    path=os.path.join(CAPDIR,fn)
    if not os.path.exists(path):
        state["status"]="error"; state["msg"]="Capture not found: %s"%fn; return False
    kill_proc()
    mhz=rf_mhz()
    with proc_lock:
        proc=subprocess.Popen(
            ["hackrf_transfer","-t",path,"-f",str(int(mhz*1e6)),"-s",str(int(srate_hz)),
             "-a",str(state["amp"]),"-x",str(state["gain"]),"-R"],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    state["tx"]=True; state["status"]="transmitting"
    state["msg"]="REPLAYING %s on %g MHz  gain %d dB"%(fn,mhz,state["gain"])
    return True

def list_caps():
    out=[]
    for f in sorted(glob.glob(os.path.join(CAPDIR,"*.iq")),reverse=True)[:30]:
        b=os.path.basename(f); sr=2000000
        # filename pattern cap_<mhz>MHz_<bw>Msps_...
        try: sr=int(b.split("_")[2].replace("Msps",""))*10**6
        except Exception: pass
        out.append({"file":b,"mb":os.path.getsize(f)//(1<<20),"srate":sr})
    return out

def generate(lat,lon):
    now=datetime.datetime.utcnow().strftime("%Y/%m/%d,%H:%M:%S")
    try:
        subprocess.run([SIM,"-e",find_eph(),"-l","%f,%f,10"%(lat,lon),
            "-t",now,"-T",now,"-d",DUR,"-b","8","-s","2600000","-o",GPS_IQ],
            cwd=SIMDIR,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        state["status"]="error"; state["msg"]="gps-sdr-sim failed: %s"%e; return False

def worker():
    while True:
        with gen_cv:
            while pending["req"] is None: gen_cv.wait()
            req=pending["req"]; pending["req"]=None
        lat,lon=req["lat"],req["lon"]
        state["status"]="generating"; state["msg"]="Generating GPS signal at %.5f, %.5f ..."%(lat,lon)
        kill_proc()
        ok=generate(lat,lon)
        with gen_cv: superseded=pending["req"] is not None
        if superseded: continue
        if ok:
            state["lat"],state["lon"]=lat,lon
            if state["mode"]=="gps": start_gps_tx()
            else: state["status"]="idle"; state["msg"]="GPS signal ready."

def request_gen(lat,lon):
    with gen_cv: pending["req"]={"lat":lat,"lon":lon}; gen_cv.notify()
threading.Thread(target=worker,daemon=True).start()

class H(BaseHTTPRequestHandler):
    def log_message(self,fmt,*a):
        import sys; sys.stderr.write("REQ "+(fmt%a)+"\n"); sys.stderr.flush()
    def _send(self,body,ctype="application/json",code=200):
        if isinstance(body,(dict,list)): body=json.dumps(body)
        if isinstance(body,str): body=body.encode()
        self.send_response(code); self.send_header("Content-Type",ctype)
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Cache-Control","no-store, no-cache, must-revalidate")
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=="/": self._send(PAGE,"text/html")
        elif self.path=="/status":
            st=dict(state); st.update(LISTENER.status()); self._send(st)
        elif self.path=="/presets": self._send(PRESETS)
        elif self.path=="/caps": self._send(list_caps())
        elif self.path=="/iss":
            try:
                ps=iss_passes(state["lat"],state["lon"])
                self._send({"ok":True,"lat":state["lat"],"lon":state["lon"],"passes":ps})
            except Exception as e:
                self._send({"ok":False,"err":str(e)})
        else: self.send_response(404); self.end_headers()
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0))
        try: data=json.loads(self.rfile.read(n) or b"{}") if n else {}
        except Exception: data={}
        p=self.path
        if p=="/mode":
            m=data.get("mode")
            if m in ("gps","tx","capture"):
                kill_proc(); state["mode"]=m; state["status"]="idle"
                state["msg"]={"gps":"GPS-spoof mode: click the map, then Start.",
                              "tx":"Transmit mode (jam/interference sim) — pick a target, Start.",
                              "capture":"Capture mode — pick a target, set seconds, Capture."}[m]
            self._send(state)
        elif p=="/preset":
            pid=data.get("preset")
            if pid in PRESET_BY_ID:
                state["preset"]=pid; state["customf"]=0; state["bw"]=PRESET_BY_ID[pid]["bw"]
                if state["tx"] and state["mode"]=="tx": start_tx()
                elif LISTENER.running: LISTENER.start(rf_mhz()*1e6, LISTENER.mode)
                else: state["msg"]="Target: %s"%PRESET_BY_ID[pid]["label"]
            self._send(state)
        elif p=="/freq":
            try: f=float(data.get("mhz"))
            except Exception: f=0
            if f and not (1<=f<=6000): f=max(1,min(6000,f))
            state["customf"]=f
            if state["tx"] and state["mode"]=="tx": start_tx()
            elif LISTENER.running: LISTENER.start(rf_mhz()*1e6, LISTENER.mode)
            else: state["msg"]=("Custom freq %g MHz."%f if f else "Using preset target.")
            self._send(state)
        elif p=="/bw":
            try: b=max(2,min(20,int(data.get("bw"))))
            except Exception: b=state["bw"]
            state["bw"]=b
            if state["tx"] and state["mode"]=="tx": start_tx()
            else: state["msg"]="Bandwidth %d MHz."%b
            self._send(state)
        elif p=="/gain":
            try: g=max(0,min(47,int(data.get("gain"))))
            except Exception: g=state["gain"]
            state["gain"]=g
            if state["tx"]: (start_gps_tx() if state["mode"]=="gps" else start_tx())
            else: state["msg"]="Gain %d dB."%g
            self._send(state)
        elif p=="/loc":
            lat=float(data["lat"]); lon=float(data["lon"])
            state["lat"],state["lon"]=lat,lon; request_gen(lat,lon)
            self._send({"ok":True})
        elif p=="/start":
            if state["mode"]=="gps": start_gps_tx()
            elif state["mode"]=="tx": start_tx()
            self._send(state)
        elif p=="/capture":
            try: secs=max(1,min(720,int(data.get("secs",5))))
            except Exception: secs=5
            start_capture(secs); self._send(state)
        elif p=="/replay":
            fn=data.get("file","");
            try: sr=int(data.get("srate",2000000))
            except Exception: sr=2000000
            replay_file(fn,sr); self._send(state)
        elif p=="/amp":
            state["amp"]=1 if data.get("on") else 0
            if state["tx"]: (start_gps_tx() if state["mode"]=="gps" else start_tx())
            else: state["msg"]="Amp %s%s"%("ON (MAX POWER)" if state["amp"] else "off",
                               "  — needs powered USB hub!" if state["amp"] else "")
            self._send(state)
        elif p=="/listen":
            on=bool(data.get("on"))
            if on:
                if state["tx"] or state["rx"]:
                    state["msg"]="Stop TX/Capture before Listen (radio busy)."
                else:
                    mhz=rf_mhz(); mode=data.get("mode","wfm")
                    LISTENER.start(mhz*1e6, mode)
                    state["status"]="listening"; state["msg"]="🔊 LISTENING %s  %g MHz (%s)"%(label_now(),mhz,mode.upper())
            else:
                LISTENER.stop(); state["status"]="idle"; state["msg"]="Listen off."
            st=dict(state); st.update(LISTENER.status()); self._send(st)
        elif p=="/tune":
            # fine tuning + controls while listening: offset(Hz), mode, vol, squelch
            kw={}
            for k in ("offset","mode","vol","squelch"):
                if k in data: kw[k]=data[k]
            LISTENER.set(**kw)
            tuned=(LISTENER.freq+LISTENER.offset)/1e6
            state["msg"]="🔊 %.4f MHz (%s)  vol %d%%  sql %.2f"%(
                tuned,LISTENER.mode.upper(),int(LISTENER.vol*100),LISTENER.squelch)
            st=dict(state); st.update(LISTENER.status()); self._send(st)
        elif p=="/stop":
            kill_proc(); state["status"]="idle"; state["msg"]="Stopped."
            st=dict(state); st.update(LISTENER.status()); self._send(st)
        else: self.send_response(404); self.end_headers()

PAGE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>RF pentest console</title>
<link rel=stylesheet href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body{margin:0;height:100%;font-family:system-ui,Arial,sans-serif;background:#0d0d0d;color:#eee}
 #banner{padding:10px;text-align:center;font-size:18px;font-weight:800;color:#fff;background:#444}
 #banner.live{background:#c0392b;animation:blink 1s steps(2,start) infinite}
 #banner.rx{background:#16a085;animation:blink 1s steps(2,start) infinite}
 #banner.gen{background:#e67e22}
 @keyframes blink{50%{opacity:.55}}
 .bar{padding:7px 10px;background:#161616;display:flex;gap:7px;align-items:center;flex-wrap:wrap;border-bottom:1px solid #222}
 #map{height:calc(100vh - 250px)}
 button{font-size:14px;padding:7px 12px;border:0;border-radius:6px;cursor:pointer;color:#fff}
 .go{background:#27ae60}.stop{background:#c0392b}.cap{background:#16a085}
 #startbtn.live{outline:3px solid #fff}
 .mode{background:#2c3e50}.mode.sel{background:#2980b9;outline:2px solid #fff}
 .pre{background:#34495e;text-align:left;font-size:13px;padding:7px 10px}.pre.sel{background:#2980b9;outline:2px solid #fff}
 #presets{display:flex;flex-wrap:wrap;gap:6px;max-width:100%}
 #amp{background:#555}#amp.on{background:#e67e22}
 .pill{padding:4px 9px;border-radius:12px;background:#2a2a2a;font-variant-numeric:tabular-nums}
 input[type=number]{width:78px;font-size:14px;padding:5px;border-radius:5px;border:0}
 input[type=range]{vertical-align:middle}
 #status{margin-left:auto;font-weight:bold;max-width:48%;text-align:right}
 .lbl{opacity:.6;font-size:13px}
 select{font-size:13px;padding:5px;border-radius:5px;border:0;max-width:300px}
 .warn{color:#e67e22;font-size:12px}
</style></head><body>
<div id=banner>● IDLE</div>

<div class=bar>
 <span class=lbl>Mode:</span>
 <button class=mode data-mode=gps>🛰️ GPS spoof</button>
 <button class=mode data-mode=tx>📡 Transmit (jam-sim)</button>
 <button class=mode data-mode=capture>🎯 Capture (listen)</button>
 <span id=status>idle</span>
</div>

<div class=bar>
 <span class=lbl>Target system:</span><span id=presets></span>
</div>

<div class=bar id=ctlbar>
 <button id=startbtn class=go>▶ Start</button>
 <button id=stopbtn class=stop>■ Stop</button>
 <span id=capwrap><span class=lbl>capture</span> <input id=secs type=number min=1 max=720 value=5> s
   <button id=capbtn class=cap>● Capture</button>
   <button id=issbtn style=background:#8e44ad>🛰️ ISS passes</button></span>
 <button id=listenbtn style=background:#2980b9>🔊 Listen</button>
 <select id=lmode><option value=wfm>WFM</option><option value=nfm>NFM</option><option value=am>AM</option></select>
 <button id=amp>Amp: OFF</button>
 <span class=lbl>Power</span><input id=gain type=range min=0 max=47 value=30 style=width:150px>
 <span class=pill id=gainv>30 dB</span>
 <span class=lbl>| Custom MHz</span><input id=freq type=number min=1 max=6000 step=0.01 placeholder=auto>
 <button id=freqset>set</button><button id=freqclr>clr</button>
 <span class=lbl>BW</span><input id=bw type=number min=2 max=20 value=20>
</div>

<div class=bar id=replaybar>
 <span class=lbl>Replay capture:</span>
 <select id=capsel></select>
 <button id=replaybtn class=go>▶ Replay on target freq</button>
 <span class=warn>replay/transmit = authorized engagement / chamber only</span>
</div>

<div id=isspanel style="display:none;padding:8px 12px;background:#1d1233;border-bottom:1px solid #333;font-size:13px"></div>
<div id=tunebar class=bar style="display:none;background:#10212b">
 <span class=lbl>Tuned:</span><span class=pill id=tunedf style=font-size:16px>—</span>
 <span class=lbl>fine</span>
 <button class=tn data-d=-100000>⏪100k</button>
 <button class=tn data-d=-25000>◀25k</button>
 <button class=tn data-d=-5000>◀5k</button>
 <button class=tn data-d=5000>5k▶</button>
 <button class=tn data-d=25000>25k▶</button>
 <button class=tn data-d=100000>100k⏩</button>
 <button id=tcenter>⊙ center</button>
 <span class=lbl>vol</span><input id=lvol type=range min=0 max=100 value=80 style=width:90px>
 <span class=lbl>squelch</span><input id=lsq type=range min=0 max=100 value=0 style=width:90px>
 <span class=pill id=siglvl>sig —</span>
 <span class=lbl>(click the spectrum to tune to a spike)</span>
</div>
<canvas id=spec width=900 height=150 style="display:none;width:100%;height:150px;background:#000;border-bottom:1px solid #333;cursor:crosshair"></canvas>
<div id=map></div>
<script>
let lat=40.8448,lon=-73.8648,pinHeld=0,gainHeld=0,fieldHeld=0,PRE={};
const map=L.map('map').setView([lat,lon],11);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(map);
let marker=L.marker([lat,lon],{draggable:true}).addTo(map);
function post(u,b){return fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});}
fetch('/presets').then(r=>r.json()).then(ps=>{const w=document.getElementById('presets');
 ps.forEach(p=>{PRE[p.id]=p;const b=document.createElement('button');b.className='pre';b.dataset.pre=p.id;
 b.textContent=p.label;b.title=p.mhz+' MHz';b.onclick=()=>post('/preset',{preset:p.id});w.appendChild(b);});});
function refreshCaps(){fetch('/caps').then(r=>r.json()).then(cs=>{const s=document.getElementById('capsel');
 const cur=s.value;s.innerHTML='';if(!cs.length){const o=document.createElement('option');o.textContent='(no captures yet)';o.value='';s.appendChild(o);}
 cs.forEach(c=>{const o=document.createElement('option');o.value=c.file;o.dataset.sr=c.srate;o.textContent=c.file+'  ('+c.mb+'MB)';s.appendChild(o);});
 if(cur)s.value=cur;});}
refreshCaps();setInterval(refreshCaps,4000);
function setLoc(la,lo){lat=la;lon=lo;marker.setLatLng([la,lo]);pinHeld=Date.now()+5000;post('/loc',{lat:la,lon:lo});}
map.on('click',e=>setLoc(e.latlng.lat,e.latlng.lng));
marker.on('dragend',e=>{const p=e.target.getLatLng();setLoc(p.lat,p.lng);});
document.querySelectorAll('.mode').forEach(b=>b.onclick=()=>{
 if(b.dataset.mode==='tx' && !confirm('TRANSMIT mode radiates a jam/interference signal.\nAuthorized engagement or RF chamber ONLY. Continue?'))return;
 post('/mode',{mode:b.dataset.mode});});
document.getElementById('startbtn').onclick=()=>post('/start');
document.getElementById('stopbtn').onclick=()=>post('/stop');
document.getElementById('capbtn').onclick=()=>post('/capture',{secs:parseInt(document.getElementById('secs').value)});
document.getElementById('issbtn').onclick=()=>{const p=document.getElementById('isspanel');
 p.style.display='';p.innerHTML='🛰️ computing ISS passes over your map pin ('+lat.toFixed(2)+', '+lon.toFixed(2)+')…';
 fetch('/iss').then(r=>r.json()).then(d=>{
  if(!d.ok){p.innerHTML='ISS error: '+d.err;return;}
  if(!d.passes.length){p.innerHTML='No ISS passes >10° in the next 24h over '+d.lat.toFixed(2)+', '+d.lon.toFixed(2)+'. Drag the map pin to your location.';return;}
  const now=Date.now();
  let h='<b>🛰️ Next ISS passes over '+d.lat.toFixed(3)+', '+d.lon.toFixed(3)+'</b> (times UTC, set 145.800 + Capture during the pass):<br>';
  h+=d.passes.slice(0,6).map(x=>{const rise=new Date(x.rise),mins=Math.round((rise-now)/60000);
    return '&nbsp;• rise '+x.rise.replace('T',' ').replace('Z','')+' UTC — max '+(x.max_elev||'?')+'° — in '+(mins>0?mins+' min':'now')+(mins<0?' (in progress)':'');}).join('<br>');
  h+='<br><span class=lbl>Pick the 🛰️ ISS preset, switch to Capture, set seconds to the pass length (~600), and Capture as it rises.</span>';
  p.innerHTML=h;});};
document.getElementById('replaybtn').onclick=()=>{const s=document.getElementById('capsel');const o=s.options[s.selectedIndex];
 if(!o||!o.value)return;if(!confirm('Replay (retransmit) '+o.value+'?\nAuthorized engagement / chamber ONLY.'))return;
 post('/replay',{file:o.value,srate:parseInt(o.dataset.sr||2000000)});};
document.getElementById('amp').onclick=()=>{const on=!document.getElementById('amp').classList.contains('on');
 if(on && !confirm('RF amp = MAX power. Needs a powered USB hub or it can brown out and reboot the Pi.'))return;post('/amp',{on:on});};
let listening=false, curOffset=0, SR=2000000, lmodeSel=document.getElementById('lmode');
document.getElementById('listenbtn').onclick=()=>{listening=!listening;
 post('/listen',{on:listening,mode:lmodeSel.value});};
lmodeSel.onchange=()=>{if(listening)post('/tune',{mode:lmodeSel.value});};
function tune(off){curOffset=Math.max(-950000,Math.min(950000,off));post('/tune',{offset:curOffset});}
document.querySelectorAll('.tn').forEach(b=>b.onclick=()=>tune(curOffset+parseInt(b.dataset.d)));
document.getElementById('tcenter').onclick=()=>tune(0);
document.getElementById('lvol').oninput=e=>post('/tune',{vol:e.target.value/100});
document.getElementById('lsq').oninput=e=>post('/tune',{squelch:e.target.value/100});
// click the spectrum to tune: x maps to -SR/2..+SR/2 around center
document.getElementById('spec').onclick=e=>{const c=e.target,r=c.getBoundingClientRect();
 const frac=(e.clientX-r.left)/r.width; tune(Math.round((frac-0.5)*SR));};
function drawSpec(arr){const c=document.getElementById('spec'),x=c.getContext('2d');
 const W=c.width,H=c.height;x.fillStyle='#000';x.fillRect(0,0,W,H);
 if(!arr||!arr.length)return;let mn=Math.min(...arr),mx=Math.max(...arr);if(mx-mn<1)mx=mn+1;
 x.strokeStyle='#0f0';x.beginPath();
 for(let i=0;i<arr.length;i++){const px=i/arr.length*W,py=H-((arr[i]-mn)/(mx-mn))*H;
  if(i==0)x.moveTo(px,py);else x.lineTo(px,py);}x.stroke();
 // tuner cursor (yellow) at current offset
 const cx=(curOffset/SR+0.5)*W;
 x.strokeStyle='#ff0';x.beginPath();x.moveTo(cx,0);x.lineTo(cx,H);x.stroke();
 x.fillStyle='#777';x.font='11px monospace';
 x.fillText('-1MHz',4,H-4);x.fillText('center',W/2-18,H-4);x.fillText('+1MHz',W-44,H-4);}
const fr=document.getElementById('freq');
document.getElementById('freqset').onclick=()=>{if(fr.value){fieldHeld=Date.now()+2000;post('/freq',{mhz:parseFloat(fr.value)});}};
document.getElementById('freqclr').onclick=()=>{fr.value='';fieldHeld=Date.now()+2000;post('/freq',{mhz:0});};
const bw=document.getElementById('bw');bw.onchange=()=>{fieldHeld=Date.now()+2000;post('/bw',{bw:parseInt(bw.value)});};
const gs=document.getElementById('gain');
gs.oninput=()=>{document.getElementById('gainv').textContent=gs.value+' dB';gainHeld=Date.now()+1500;};
gs.onchange=()=>{gainHeld=Date.now()+1500;post('/gain',{gain:parseInt(gs.value)});};
function show(id,on){document.getElementById(id).style.display=on?'':'none';}
function poll(){fetch('/status').then(r=>r.json()).then(s=>{
 document.getElementById('status').textContent=s.msg||s.status;
 const a=document.getElementById('amp');a.textContent='Amp: '+(s.amp?'ON (MAX)':'OFF');a.className=s.amp?'on':'';
 document.querySelectorAll('.mode').forEach(b=>b.className='mode'+(b.dataset.mode===s.mode?' sel':''));
 document.querySelectorAll('.pre').forEach(b=>b.className='pre'+(b.dataset.pre===s.preset&&!s.customf?' sel':''));
 // show controls relevant to the mode
 show('capwrap',s.mode==='capture');
 show('startbtn',s.mode!=='capture');
 document.getElementById('replaybar').style.display=(s.mode==='tx')?'':'none';
 document.getElementById('map').style.filter=(s.mode==='gps')?'':'grayscale(1) opacity(.35)';
 if(Date.now()>gainHeld){gs.value=s.gain;document.getElementById('gainv').textContent=s.gain+' dB';}
 if(Date.now()>fieldHeld){bw.value=s.bw;if((s.customf||0)>0)fr.value=s.customf;}
 listening=!!s.listening;
 const lb=document.getElementById('listenbtn');
 lb.textContent=listening?'🔊 Listening (stop)':'🔊 Listen';lb.style.background=listening?'#16a085':'#2980b9';
 const sc=document.getElementById('spec');sc.style.display=listening?'':'none';
 document.getElementById('tunebar').style.display=listening?'':'none';
 if(listening){
   if(typeof s.loffset==='number')curOffset=s.loffset;
   drawSpec(s.spectrum);
   const tuned=((s.lfreq+(s.loffset||0))/1e6).toFixed(4);
   document.getElementById('tunedf').textContent=tuned+' MHz';
   document.getElementById('siglvl').textContent='sig '+(s.lsig!=null?s.lsig:'—');
 }
 const ban=document.getElementById('banner');
 if(listening){ban.className='rx';ban.textContent='🔊 LISTENING — '+s.msg;}
 else if(s.tx){ban.className='live';ban.textContent='● ON AIR — '+s.msg;}
 else if(s.rx){ban.className='rx';ban.textContent='● CAPTURING — '+s.msg;}
 else if(s.status==='generating'){ban.className='gen';ban.textContent='⚙ '+s.msg;}
 else{ban.className='';ban.textContent='● IDLE — '+({gps:'GPS spoof',tx:'Transmit',capture:'Capture'}[s.mode]||'');}
 const sb=document.getElementById('startbtn');sb.className='go'+(s.tx?' live':'');
 if(s.mode==='gps'&&Date.now()>pinHeld){lat=s.lat;lon=s.lon;marker.setLatLng([s.lat,s.lon]);}
}).catch(()=>{});}
setInterval(poll,1000);poll();
</script></body></html>"""

if __name__=="__main__":
    try: ip=subprocess.run(["hostname","-I"],capture_output=True,text=True).stdout.split()[0]
    except Exception: ip="127.0.0.1"
    print("=== RF pentest console ===  http://%s:%d"%(ip,PORT))
    srv=ThreadingHTTPServer(("0.0.0.0",PORT),H)
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
    finally: kill_proc()
