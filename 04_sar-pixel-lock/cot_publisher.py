"""
cot_publisher.py — live ATAK Cursor-on-Target broadcaster.

When toggled ON from the web GUI, this periodically multicasts a CoT event for
every active (locked) target to ATAK's default SA mesh group (239.2.3.1:6969),
so EUDs on the same network see the pixel-locked targets with ZERO config.

Toggling OFF (or a target being deleted/dismissed) emits a stale-in-the-past
delete event so ATAK drops the marker immediately instead of waiting it out.

Optional config (config*.yaml -> `atak:`):
  group:     multicast group   (default 239.2.3.1)
  port:      multicast port     (default 6969)
  period_s:  resend interval    (default 2.0)
  stale_s:   marker lifetime    (default 30)
  iface_ip:  outbound iface IP for multicast (default OS-chosen)
  unicast:   ["ip:port", ...]   extra direct sends if mcast is filtered
"""
import socket
import threading
import time

DEF_GROUP = "239.2.3.1"
DEF_PORT = 6969


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _z(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


class CotPublisher:
    def __init__(self, store, group=DEF_GROUP, port=DEF_PORT, period_s=2.0,
                 stale_s=30, iface_ip=None, unicast=None):
        self.store = store
        self.group = group or DEF_GROUP
        self.port = int(port or DEF_PORT)
        self.period_s = float(period_s)
        self.stale_s = int(stale_s)
        self.iface_ip = iface_ip
        self.unicast = []
        for u in (unicast or []):
            try:
                ip, _, p = str(u).partition(":")
                self.unicast.append((ip, int(p or DEF_PORT)))
            except Exception:
                pass
        self._enabled = False
        self._thread = None
        self._stop = threading.Event()
        self._sock = None
        self._sent = set()         # uids we've published (for delete-on-vanish)
        self._lock = threading.Lock()

    # ---- public API ----
    @property
    def enabled(self):
        return self._enabled

    def status(self):
        return {"enabled": self._enabled, "group": self.group,
                "port": self.port, "unicast": ["%s:%d" % u for u in self.unicast],
                "count": len(self._sent)}

    def set_enabled(self, on):
        on = bool(on)
        with self._lock:
            if on == self._enabled:
                return self.status()
            self._enabled = on
            if on:
                self._start()
            else:
                self._shutdown()
        return self.status()

    # ---- internals ----
    def _open(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        if self.iface_ip:
            try:
                s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
                             socket.inet_aton(self.iface_ip))
            except OSError:
                pass
        self._sock = s

    def _start(self):
        self._stop.clear()
        self._sent = set()
        self._open()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _shutdown(self):
        self._stop.set()
        try:
            for uid in list(self._sent):
                self._send(self._delete_event(uid))
        except Exception:
            pass
        self._sent = set()
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _send(self, xml):
        if not self._sock:
            return
        data = xml.encode("utf-8")
        try:
            self._sock.sendto(data, (self.group, self.port))
        except Exception:
            pass
        for ip, port in self.unicast:
            try:
                self._sock.sendto(data, (ip, port))
            except Exception:
                pass

    def _event(self, t):
        now = time.time()
        # active locked target = unknown ground (yellow); found = friendly (green)
        typ = "a-f-G" if t.get("status") == "found" else "a-u-G"
        uid = "SAR.%s" % t["id"]
        name = _esc(t.get("name", t["id"]))
        remarks = _esc(" ".join(str(x) for x in
                       (t.get("mgrs", ""), t.get("status", ""),
                        t.get("notes", "")) if x))
        return ('<?xml version="1.0" standalone="yes"?>'
                '<event version="2.0" uid="%s" type="%s" how="m-g" '
                'time="%s" start="%s" stale="%s">'
                '<point lat="%.7f" lon="%.7f" hae="0" ce="15" le="15"/>'
                '<detail><contact callsign="%s"/>'
                '<remarks>%s</remarks></detail></event>'
                % (uid, typ, _z(now), _z(now), _z(now + self.stale_s),
                   t["lat"], t["lon"], name, remarks))

    def _delete_event(self, uid):
        now = time.time()
        past = _z(now - 60)
        return ('<?xml version="1.0" standalone="yes"?>'
                '<event version="2.0" uid="%s" type="a-u-G" how="m-g" '
                'time="%s" start="%s" stale="%s">'
                '<point lat="0" lon="0" hae="0" ce="9999999" le="9999999"/>'
                '<detail/></event>' % (uid, _z(now), past, past))

    def _loop(self):
        while not self._stop.is_set():
            try:
                current = set()
                for t in self.store.list(include_thumbs=False):
                    if t.get("status") == "dismissed":
                        continue
                    if t.get("lat") is None or t.get("lon") is None:
                        continue
                    uid = "SAR.%s" % t["id"]
                    current.add(uid)
                    self._send(self._event(t))
                for uid in list(self._sent):
                    if uid not in current:
                        self._send(self._delete_event(uid))
                self._sent = current
            except Exception:
                pass
            self._stop.wait(self.period_s)
