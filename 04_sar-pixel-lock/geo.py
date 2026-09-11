"""
geo.py — pixel <-> world georeferencing for the SAR pixel-lock tool.

Pinhole ground-plane raycast (no lidar): a pixel is cast as a camera ray,
rotated through the camera mount and the drone attitude into the world (NED)
frame, then intersected with a flat ground plane at the drone's height AGL.
The inverse (world -> pixel) lets locked targets reproject onto the live feed
as the drone moves. Coordinates round-trip through UTM for local accuracy and
are reported as lat/lon + MGRS grid.

Frames:
  World  NED  : North(x) East(y) Down(z)         (z positive downward)
  Body   FRD  : Forward(x) Right(y) Down(z)
  Camera      : optical +Z, image-right +X, image-down +Y
Assumes flat ground at the drone's AGL height. Good over open terrain; on
steep slopes the fix is approximate (documented honestly in the UI).
"""
import math
import numpy as np

try:
    import utm as _utm
except Exception:
    _utm = None
try:
    import mgrs as _mgrs
    _MGRS = _mgrs.MGRS()
except Exception:
    _MGRS = None

R_EARTH = 6378137.0


def _Ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def dcm_body_to_ned(roll, pitch, yaw):
    """Standard 3-2-1 body->NED direction cosine matrix. Angles in radians."""
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return np.array([
        [cp * cy, sr * sp * cy - cr * sy, cr * sp * cy + sr * sy],
        [cp * sy, sr * sp * sy + cr * cy, cr * sp * sy - sr * cy],
        [-sp,     sr * cp,                cr * cp],
    ])


class Camera:
    """Camera intrinsics (for the capture resolution) + mount geometry."""

    def __init__(self, width, height, hfov_deg=78.0, fx=None, fy=None,
                 cx=None, cy=None, mount_tilt_deg=45.0, mount_yaw_deg=0.0):
        self.w, self.h = width, height
        if fx is None:
            fx = (width / 2.0) / math.tan(math.radians(hfov_deg) / 2.0)
        self.fx = fx
        self.fy = fy if fy is not None else fx
        self.cx = cx if cx is not None else width / 2.0
        self.cy = cy if cy is not None else height / 2.0
        self.set_mount(mount_tilt_deg, mount_yaw_deg)

    def set_mount(self, tilt_deg, yaw_deg=0.0):
        """tilt: 0 = forward/level, 90 = straight down (depression angle)."""
        self.mount_tilt = math.radians(tilt_deg)
        self.mount_yaw = math.radians(yaw_deg)
        # camera-frame basis expressed in body frame at tilt=0 (look forward)
        R0 = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=float)
        Rz = np.array([[math.cos(self.mount_yaw), -math.sin(self.mount_yaw), 0],
                       [math.sin(self.mount_yaw), math.cos(self.mount_yaw), 0],
                       [0, 0, 1]])
        self.R_body_cam = Rz @ _Ry(-self.mount_tilt) @ R0

    def scale_to(self, width, height):
        """Return a Camera with intrinsics scaled to a different resolution."""
        sx, sy = width / self.w, height / self.h
        return Camera(width, height, fx=self.fx * sx, fy=self.fy * sy,
                      cx=self.cx * sx, cy=self.cy * sy,
                      mount_tilt_deg=math.degrees(self.mount_tilt),
                      mount_yaw_deg=math.degrees(self.mount_yaw))


def pixel_to_world(cam, u, v, att, lat, lon, agl_m):
    """Cast pixel (u,v) to a ground lat/lon. att=(roll,pitch,yaw) rad.
    Returns dict with lat/lon/mgrs/range_m/bearing_deg or None if no ground hit."""
    if agl_m is None or agl_m <= 0:
        return None
    ray_cam = np.array([(u - cam.cx) / cam.fx, (v - cam.cy) / cam.fy, 1.0])
    ray_cam /= np.linalg.norm(ray_cam)
    ray_body = cam.R_body_cam @ ray_cam
    R = dcm_body_to_ned(*att)
    r = R @ ray_body                       # ray in NED
    if r[2] <= 1e-6:                        # not pointing at the ground
        return None
    t = agl_m / r[2]
    north, east = t * r[0], t * r[1]
    tlat, tlon = _offset_latlon(lat, lon, north, east)
    rng = math.sqrt(north * north + east * east + agl_m * agl_m)
    brg = (math.degrees(math.atan2(east, north)) + 360.0) % 360.0
    return {"lat": tlat, "lon": tlon, "mgrs": to_mgrs(tlat, tlon),
            "range_m": rng, "bearing_deg": brg,
            "ground_range_m": math.hypot(north, east)}


def world_to_pixel(cam, tlat, tlon, att, lat, lon, agl_m):
    """Project a ground lat/lon back into the image. Returns
    (u, v, visible, edge_angle_deg). edge_angle points toward an off-screen
    target (screen degrees, 0=right, CCW) for drawing an edge arrow."""
    north, east = _latlon_offset(lat, lon, tlat, tlon)
    world = np.array([north, east, agl_m if agl_m else 0.0])
    R = dcm_body_to_ned(*att)
    ray_body = R.T @ world
    ray_cam = cam.R_body_cam.T @ ray_body
    if ray_cam[2] <= 1e-3:
        # behind the camera; still give a bearing for the edge arrow
        ang = math.degrees(math.atan2(-ray_cam[1], -ray_cam[0]))
        return None, None, False, float(ang)
    u = float(cam.cx + cam.fx * ray_cam[0] / ray_cam[2])
    v = float(cam.cy + cam.fy * ray_cam[1] / ray_cam[2])
    visible = bool(0 <= u < cam.w and 0 <= v < cam.h)
    ang = math.degrees(math.atan2(-(v - cam.cy), (u - cam.cx)))
    return u, v, visible, float(ang)


def _offset_latlon(lat, lon, north, east):
    if _utm is not None:
        try:
            e, n, z, l = _utm.from_latlon(lat, lon)
            return _utm.to_latlon(e + east, n + north, z, l)
        except Exception:
            pass
    dlat = math.degrees(north / R_EARTH)
    dlon = math.degrees(east / (R_EARTH * math.cos(math.radians(lat))))
    return lat + dlat, lon + dlon


def _latlon_offset(lat0, lon0, lat1, lon1):
    if _utm is not None:
        try:
            e0, n0, z, l = _utm.from_latlon(lat0, lon0)
            e1, n1, _, _ = _utm.from_latlon(lat1, lon1, force_zone_number=z,
                                            force_zone_letter=l)
            return n1 - n0, e1 - e0
        except Exception:
            pass
    north = math.radians(lat1 - lat0) * R_EARTH
    east = math.radians(lon1 - lon0) * R_EARTH * math.cos(math.radians(lat0))
    return north, east


def to_mgrs(lat, lon, precision=5):
    if _MGRS is not None:
        try:
            return _MGRS.toMGRS(lat, lon, MGRSPrecision=precision)
        except Exception:
            pass
    return ""
