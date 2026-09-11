#!/usr/bin/env python3
"""
Rebuild pi5_silvus_lite_body.stl as a radio enclosure body, sized to the
reference enclosures the radios live in.

  - strips every internal mounting feature (keeps walls, lid groove, top ribs, side vents, side tabs)
  - plugs the old 3x SMA holes and the old charger/port cutout
  - ENLARGES the body by inserting extruded slices (ribs/fillets/vents are preserved exactly)
  - cuts 2+2 SMA holes at the jack spacing of the actual devices:
        top row    = Alfa dongle  (jacks 44.7 mm apart, measured from bottom_v2.3mf)
        bottom row = RFD900x      (jacks 20.5 mm apart, measured from RDF_bottom/top.STL)
  - cuts a Neutrik D-series cutout (24 mm + 2x M3 diagonal) for the dual USB-A panel coupler
  - also writes a snap-in lid for the enlarged body

Requires: pip install trimesh manifold3d numpy shapely
"""
import numpy as np, trimesh, os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, '..', 'pi5_silvus_lite_body.stl')
OUT  = os.path.join(HERE, 'pi5_radio_body.stl')
LID  = os.path.join(HERE, 'pi5_radio_lid.stl')

# ---- original body, measured ------------------------------------------------
X1, Y0, Y1, ZC, WALL = 62.19, 0.008564, 123.491, 35.0, 2.6   # outer faces, inner ceiling, wall
Y1_IN = 120.9                                                # inner face of SMA end wall
RIB_PITCH, RIB0 = 5.5, (27.25, 29.45)                        # one rib's x-span (the 5th rib)
EPS = 0.02

# ---- component envelopes (from the reference STL/3MF files) -----------------
ALFA = dict(W=56, L=82, H=19, sma_cc=44.7, sma_z=4.5)   # shell 82x56x17 + 2mm plate; jacks ~4.5 above its bottom
RFD  = dict(W=34, L=66, H=13, sma_cc=20.5, sma_z=7.5)   # case 34x66x13; jacks 7.5 above its bottom
LID_T = 4.0                                             # lid plate thickness -> floor is at z=4
GAP   = 5.0                                             # air between RFD top and Alfa bottom

# ---- how much bigger ---------------------------------------------------------
ADD_W = 44.0          # 57 -> 101 inner width (v1 was 11; +33 mm = 1.3" wider per test-print feedback; = 8 rib pitches, pattern stays even)
ADD_L = 26.5          # 118.3 -> 144.8 inner length
ADD_H = 9.0           # 35 -> 44 inner height
X_CUT, Y_CUT, Z_CUT = 31.1, 40.0, 10.0   # slice planes: rib gap / plain wall / plain wall ring

# ---- cutouts -----------------------------------------------------------------
SMA_D = 6.5                       # RP-SMA / SMA jack thread is 6.35
Z_RFD  = LID_T + RFD['sma_z']                      # 11.5
Z_ALFA = LID_T + RFD['H'] + GAP + ALFA['sma_z']    # 26.5
D_HOLE, D_SCREW, D_DX, D_DZ = 24.2, 3.4, 19.0, 24.0

# =============================================================================
def box(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]); return b

def ycyl(d, x, z, y0, y1):
    c = trimesh.creation.cylinder(radius=d / 2, height=y1 - y0, sections=96)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    c.apply_translation([x, (y0 + y1) / 2, z]); return c

def U(*ms):  return trimesh.boolean.union(list(ms), engine='manifold')
def D(a, *ms): return trimesh.boolean.difference([a] + list(ms), engine='manifold')
def I(a, b):  return trimesh.boolean.intersection([a, b], engine='manifold')

BIG = 500
def halfspace(axis, pos, side):
    lo = [-BIG] * 3; hi = [BIG] * 3
    if side > 0: lo[axis] = pos
    else:        hi[axis] = pos
    return box(lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])

def stretch(mesh, axis, pos, amount):
    """cut mesh at plane axis=pos, move the + side by `amount`, fill with the extruded cross-section"""
    keep = I(mesh, halfspace(axis, pos, -1))
    move = I(mesh, halfspace(axis, pos, +1))
    t = [0, 0, 0]; t[axis] = amount; move.apply_translation(t)
    o = [0, 0, 0]; o[axis] = pos; n = [0, 0, 0]; n[axis] = 1
    path, to3d = mesh.section(plane_origin=o, plane_normal=n).to_2D()
    slabs = []
    for poly in path.polygons_full:
        s = trimesh.creation.extrude_polygon(poly, height=amount)
        s.apply_transform(to3d)
        t2 = [0, 0, 0]; t2[axis] = pos - s.bounds[0][axis]; s.apply_translation(t2)
        slabs.append(s)
    return U(keep, move, *slabs)

body = trimesh.load(SRC); assert body.is_watertight
print('source', round(body.volume), 'mm3', len(body.faces), 'faces')

# 1) gut the interior (lid groove sits inside the wall, so it survives)
shell = D(body, box(WALL - EPS, X1 - WALL + EPS, WALL - EPS, Y1_IN + EPS, -1, ZC + EPS))
# 2) plug the old holes
shell = U(shell, box(14, 48, Y1_IN + EPS, Y1, 6, 34), box(17, 45.5, Y0, WALL - EPS, 8, 24))

# 3) widen: slice through the rib gap on the centreline, then copy two ribs into the new flat strip
shell = stretch(shell, 0, X_CUT, ADD_W)
rib = I(body, box(RIB0[0] - 1.2, RIB0[1] + 1.2, -1, 200, ZC + 2.3, 60))   # one rib + a sliver of plate
for k in range(1, int(round(ADD_W / RIB_PITCH)) + 1):
    r = rib.copy(); r.apply_translation([k * RIB_PITCH, 0, 0]); shell = U(shell, r)
# 4) lengthen, 5) raise
shell = stretch(shell, 1, Y_CUT, ADD_L)
shell = stretch(shell, 2, Z_CUT, ADD_H)

XO = X1 + ADD_W; YO = Y1 + ADD_L; ZCN = ZC + ADD_H; XC = XO / 2
print(f'new outer {XO:.1f} x {YO:.1f} x {ZCN + 2.6 + 2.2:.1f} (incl. ribs), inner {XO-2*WALL:.1f} x {YO-2*WALL:.1f} x {ZCN:.1f}')

# 6) cutouts
cuts = []
for x in (XC - ALFA['sma_cc'] / 2, XC + ALFA['sma_cc'] / 2): cuts.append(ycyl(SMA_D, x, Z_ALFA, YO - 10, YO + 5))
for x in (XC - RFD['sma_cc'] / 2,  XC + RFD['sma_cc'] / 2):  cuts.append(ycyl(SMA_D, x, Z_RFD,  YO - 10, YO + 5))
DZ = (WALL + ZCN) / 2                                   # centred on the flat part of the end face
cuts.append(ycyl(D_HOLE, XC, DZ, -5, 10))
for sx, sz in ((-1, 1), (1, -1)): cuts.append(ycyl(D_SCREW, XC + sx * D_DX / 2, DZ + sz * D_DZ / 2, -5, 10))
result = D(shell, *cuts)
print('body', round(result.volume), 'mm3', len(result.faces), 'faces, watertight', result.is_watertight)
print('bounds', np.round(result.bounds, 2).tolist())
result.export(OUT); print('wrote', OUT)

# 7) lid: plate flush with the bottom + snap ridges into the groove on the long sides
CL = 0.25                                               # clearance per side
ix0, ix1, iy0, iy1 = WALL + CL, XO - WALL - CL, WALL + CL, YO - WALL - CL
plate = box(ix0, ix1, iy0, iy1, 0, LID_T)
ridges = []
for (xa, xb) in ((ix0 - 0.25 - 0.7, ix0 + 0.5), (ix1 - 0.5, ix1 + 0.25 + 0.7)):
    for (ya, yb) in ((iy0 + 12, iy0 + 12 + 40), (iy1 - 12 - 40, iy1 - 12)):
        ridges.append(box(xa, xb, ya, yb, LID_T, LID_T + 1.3))   # groove is z 3.5..5.5
lid = U(plate, *ridges)
lid.export(LID); print('lid', np.round(lid.extents, 2).tolist(), 'watertight', lid.is_watertight)
print(f'SMA rows: Alfa z={Z_ALFA} x={XC-ALFA["sma_cc"]/2:.2f}/{XC+ALFA["sma_cc"]/2:.2f}   RFD z={Z_RFD} x={XC-RFD["sma_cc"]/2:.2f}/{XC+RFD["sma_cc"]/2:.2f}   D-centre ({XC:.1f},{DZ:.2f})')
