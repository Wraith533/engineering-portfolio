// =====================================================================
//  Drone component tray  —  Cube Orange (+ Here4) / Herelink / Jetson /
//  RFD900.   v6 = ENCLOSURES.
//  Cube gets a CASE (cable room + rear cutout) with the Here4 stand as a
//  drop-on LID. Jetson gets a CASE (walls + screw bosses) sitting on an
//  RFD900 tray that runs the full pod length with an OPEN rear for cables.
//
//  AXES:  X = fore-aft (X=0 front/nose, +X = tail/rear; cables/SMAs aft)
//         Y = across, CENTRED on 0      Z = up (Z=0 = base bottom)
//  All dimensions in mm.                                Generated 2026-06-13
// =====================================================================

part = "assembly";        // "assembly" | "tray" | "gps"
$fn  = 64;

// ---------------------------------------------------------------------
//  GLOBAL
// ---------------------------------------------------------------------
base_t = 4;               // tray plate thickness
base_w = 50.5;            // front width (= Jetson width, per William)
wall   = 2.4;             // case wall thickness
cl     = 0.6;             // clearance around a component inside its case
gap    = 10;              // gap between the cube case / herelink / jetson pod
rear_margin = 2;

// extra interior headroom (added 2026-06-16 for component clearance)
cube_head = 2;            // Cube Orange (H7) compartment: +mm taller
rfd_head  = 2;            // RFD900 compartment: +mm taller (SMA holes stay put)

// ---------------------------------------------------------------------
//  COMPONENTS  (measured / *assumed)
// ---------------------------------------------------------------------
cube_l = 94.5; cube_w = 44.3; cube_h = 31;        // Cube Orange + carrier
gps_d  = 67.8; gps_h  = 14;  gps_riser = 16;       // Here4 round (213 circ); *h assumed
hl_fore = 15.5; hl_across = 78; hl_h = 31;         // Herelink, spun (overhangs width)
jet_l = 87; jet_w = 50.5; jet_h = 29;              // Jetson Orin carrier
rfd_l = 57.5; rfd_w = 30; rfd_h = 12.5;            // RFD900x

// CAMERA (NEW 2026-06-16) — beefy front camera; round lens pokes OUT the nose
cam_l = 49; cam_w = 38; cam_h = 38;                // body L(X) x W(Y) x H(Z)
cam_lens_d = 34;                                   // round lens dia (widest) — stays OUTSIDE the case
cam_rear   = 8;                                    // cable/connector space behind the camera body
cube_rear  = 15;                                   // cable space behind the cube (William asked)

// Jetson carrier mounting (4 corner holes)
jet_hole_inset = 3.5;     // *holes inset from board edges (CONFIRM)
jet_screw_d    = 2.5;     // *M2.5 (CONFIRM)
jet_boss_d     = 6;
jet_pilot_d    = 2.1;     // M2.5 self-tap pilot
boss_h         = 3;       // boss height above the deck (jetson floats clear)

// Openings (RFD antennas aft, all wiring forward)
sma_d      = 6.5;         // RFD900 SMA bulkhead hole
rfd_sma_sp = 19.5;        // RFD SMA spacing center-to-center (MEASURED 2026-06-15)
jet_cut_w  = 46; jet_cut_h = 16;   // (legacy, unused — replaced by jcut_* below)
// Jetson wiring cutouts — UNIFORM size on all 4 walls, 3mm below the rim (2026-06-15)
jcut_w      = 30;   // in-plane width (Y on the ends, X on the sides)
jcut_h      = 16;   // height
jcut_topgap = 3;    // top edge below the wall rim

// ---------------------------------------------------------------------
//  CAMERA CASE  (nose, open-top box; round lens hole in the front wall)
// ---------------------------------------------------------------------
cam_x0     = 0;                                    // camera is the new nose
cam_ol     = wall + cl + cam_l + cam_rear + wall;  // front wall + body + rear cable space + rear wall
cam_oy     = cam_w + 2*cl + 2*wall;                // outer width
cam_wall_h = cam_h + cl;                           // wall height (open top)
cam_top_z  = base_t + cam_wall_h;                  // camera rim height
cam_lens_z = base_t + cam_h/2;                     // lens centred on the body height
cam_x1     = cam_x0 + cam_ol;                      // camera rear face
cam_in_x0  = cam_x0 + wall + cl;                   // camera body sits here

// ---------------------------------------------------------------------
//  CUBE CASE  (open-top box, Here4 lid drops on; rear cable cutout)
//  Shifted back behind the camera (butts the camera rear wall).
// ---------------------------------------------------------------------
cc_x0  = cam_x1;                                   // cube case starts right behind the camera
cc_ol  = wall + cl + cube_l + cube_rear + wall;    // front wall + cube + 15mm rear cable space + rear wall
cc_oy  = cube_w + 2*cl + 2*wall;                   // outer width (<= base_w)
cc_h   = cube_h + cl + cube_head;                  // wall height (open top)
cc_cut_w = 40; cc_cut_h = 28;                      // rear cable cutout (w 32->40; DEEPER h 20->28, ~3.6mm lip above base)

cube_x0 = cc_x0 + wall + cl;                       // cube sits here

// ---------------------------------------------------------------------
//  HERE4 LID + STAND
// ---------------------------------------------------------------------
lid_t   = 2.4;
gps_cx  = cc_x0 + cc_ol/2;
gps_cy  = 0;
lid_z   = base_t + cc_h;                           // lid underside (on case rim)
cup_wall = 2.5; cup_floor = 2; cup_cl = 0.6;
lip = 1.2; lip_h = 1.5;
ped_bot_d = 34; ped_top_d = 26; cable_d = 12;
gps_top_z = lid_z + lid_t + gps_riser + gps_h;

// Here4 cable hole (measured, from v12+) — exits OFFSET, not centred
gps_cab_w   = 7.5; gps_cab_l = 10;     // hole: width (Y) x length (fore-aft)
gps_cab_back = 12.3;                    // hole centre from the GPS back edge
gps_cab_cl  = 1.5;                      // clearance around the cable
gps_cab_x   = gps_cx + gps_d/2 - gps_cab_back;   // true hole X (toward the tail)
cab_sx = gps_cab_l + gps_cab_cl;        // path size fore-aft  (11.5)
cab_sy = gps_cab_w + gps_cab_cl;        // path size across    (9)
cab_cw = 2;                             // chute wall

// ---------------------------------------------------------------------
//  HERELINK COVER  (snap-on shroud over the centre gap; side cable cuts)
// ---------------------------------------------------------------------
gap_cl    = 0.4;          // cover-to-case clearance
hc_snap_z = 26;           // snap bead height (within the 31 tall herelink)
hc_bead   = 1.0;          // bead protrusion / groove depth
hc_bead_w = 20;           // bead width (across)
hc_gh     = 2*hc_bead + 0.6;   // groove height
hc_channel = 7;           // wire-channel headroom over the herelink (cube<->jetson/rfd)
hc_pass_w  = 30;          // cable pass-through width in the front & rear walls

// ---------------------------------------------------------------------
//  LAYOUT (fore-aft)
// ---------------------------------------------------------------------
hl_x0  = cc_x0 + cc_ol + gap;
jp_x0  = hl_x0 + hl_fore + gap;

// ---------------------------------------------------------------------
//  JETSON POD  (RFD tray below + Jetson case above; rear OPEN for cables)
// ---------------------------------------------------------------------
jp_ol  = jet_l + 2*cl + 2*wall;                    // outer length
jp_oy  = jet_w + 2*cl + 2*wall;                    // outer width (> base_w -> flare)
base_l = jp_x0 + jp_ol + rear_margin;

deck_z   = base_t + rfd_h + cl + rfd_head;         // RFD bay ceiling (deck underside)
deck_top = deck_z + wall;                          // deck top surface
jet_z0   = deck_top + boss_h;                      // Jetson underside
pod_h    = (jet_z0 + jet_h + cl) - base_t;         // pod wall height above base top
pod_top_z = base_t + pod_h;

jet_x0 = jp_x0 + wall + cl;                         // jetson sits here
jet_x1 = jet_x0 + jet_l;
jet_hx = [jet_x0 + jet_hole_inset, jet_x1 - jet_hole_inset];
jet_hy = [-(jet_w/2 - jet_hole_inset), (jet_w/2 - jet_hole_inset)];

rfd_x0 = jp_x0 + jp_ol - wall - rfd_l;             // RFD pushed aft (SMAs out open rear)

echo(str("BASE  ", base_l, " long;  front ", base_w, " wide, rear flares to ", jp_oy));
echo(str("Cube case  x ", cc_x0, "..", cc_x0+cc_ol, "  (", cc_oy, " wide, ", cc_h, " tall)"));
echo(str("Herelink   x ", hl_x0, "..", hl_x0+hl_fore, "  (78 across, overhangs ", (hl_across-base_w)/2, "/side)"));
echo(str("Jetson pod x ", jp_x0, "..", jp_x0+jp_ol, "  (", jp_oy, " wide, top z ", pod_top_z, ")"));
echo(str("RFD tray rear OPEN;  jetson bolt pattern ", jet_hx[1]-jet_hx[0], " x ", jet_hy[1]-jet_hy[0]));
echo(str("GPS top z = ", gps_top_z, " mm above base bottom"));

// =====================================================================
//  HELPERS
// =====================================================================
module ybox(x0, len, w, z0, h) {        // X x Y(centred) x Z box
    translate([x0, -w/2, z0]) cube([len, w, h]);
}

module snap_cup() {                      // cup floor bottom at local z=0
    cup_id = gps_d + cup_cl;
    cup_od = cup_id + 2*cup_wall;
    difference() {
        cylinder(d=cup_od, h=cup_floor + gps_h);
        translate([0,0,cup_floor]) cylinder(d=cup_id, h=gps_h - lip_h + 0.01);
        translate([0,0,cup_floor + gps_h - lip_h])
            cylinder(d1=cup_id, d2=cup_id - 2*lip, h=lip_h + 0.5);
        translate([0,0,-1]) cylinder(d=cable_d, h=cup_floor + 2);
        for (a=[0:90:359]) rotate([0,0,a+45])
            translate([cup_id/2 - 1, -1.2, cup_floor + 3]) cube([cup_wall + 3, 2.4, gps_h]);
    }
}

// Here4 cable: guide chute (added solid) + the offset hole (subtracted), from v12+
module cab_chute() {        // guide tube from the lid plate up to the cup floor
    translate([gps_cab_x, 0, lid_z])
        linear_extrude(lid_t + gps_riser)
            square([cab_sx + 2*cab_cw, cab_sy + 2*cab_cw], center=true);
}
module cab_cut() {          // the actual cable hole: cube bay -> lid -> chute -> cup floor
    translate([gps_cab_x, 0, lid_z - 4])
        linear_extrude((lid_z + lid_t + gps_riser + cup_floor + 1) - (lid_z - 4))
            square([cab_sx, cab_sy], center=true);
}

// =====================================================================
//  CAMERA CASE  (nose; open-top, round lens hole in the front wall)
// =====================================================================
cam_cab_w = 20;   // camera<->cube cable pass-through width
cam_cab_h = 14;   // cable pass height (down from the rim)
module camera_case() {
    difference() {
        ybox(cam_x0, cam_ol, cam_oy, base_t, cam_wall_h);
        // cavity, open top (base plate is the floor)
        ybox(cam_x0 + wall, cam_ol - 2*wall, cam_oy - 2*wall, base_t, cam_wall_h + 1);
        // round LENS hole in the FRONT wall (lens pokes out; 38mm body stays inside)
        translate([cam_x0 - 1, 0, cam_lens_z])
            rotate([0,90,0]) cylinder(d=cam_lens_d + 1, h=wall + 2);
        // cable pass-through (top notch) in the REAR wall, toward the cube
        translate([cam_x1 - wall - 1, -cam_cab_w/2, cam_top_z - cam_cab_h])
            cube([wall + 2, cam_cab_w, cam_cab_h + 1]);
    }
}

// =====================================================================
//  CUBE CASE
// =====================================================================
module cube_case() {
    difference() {
        ybox(cc_x0, cc_ol, cc_oy, base_t, cc_h);
        // cavity, open top (base plate is the floor)
        ybox(cc_x0 + wall, cc_ol - 2*wall, cc_oy - 2*wall, base_t, cc_h + 1);
        // rear cable cutout (top-down notch in the rear wall)
        translate([cc_x0 + cc_ol - wall - 1, -cc_cut_w/2, base_t + cc_h - cc_cut_h])
            cube([wall + 2, cc_cut_w, cc_cut_h + 1]);
        // snap groove for the herelink cover (rear/gap-facing face)
        translate([cc_x0 + cc_ol - (hc_bead + 0.4), -hc_bead_w/2, hc_snap_z - hc_gh/2])
            cube([hc_bead + 0.6, hc_bead_w, hc_gh]);
        // cable pass-through (top notch) in the FRONT wall, toward the camera
        translate([cc_x0 - 1, -cam_cab_w/2, base_t + cc_h - cam_cab_h])
            cube([wall + 2, cam_cab_w, cam_cab_h + 1]);
    }
}

// =====================================================================
//  HERE4 LID  (drops onto the cube case; carries the stand + snap cup)
// =====================================================================
module gps_lid() {
    cup_z = lid_z + lid_t + gps_riser - cup_floor;
    difference() {
        union() {
            ybox(cc_x0, cc_ol, cc_oy, lid_z, lid_t);                 // lid plate
            // locating rim, drops into the case mouth
            translate([cc_x0 + wall + 0.4, -(cc_oy/2 - wall - 0.4), lid_z - 3])
                difference() {
                    cube([cc_ol - 2*wall - 0.8, cc_oy - 2*wall - 0.8, 3]);
                    translate([1.6, 1.6, -1])
                        cube([cc_ol - 2*wall - 4, cc_oy - 2*wall - 4, 5]);
                }
            translate([gps_cx, gps_cy, lid_z + lid_t])              // pedestal
                cylinder(d1=ped_bot_d, d2=ped_top_d, h=gps_riser);
            translate([gps_cx, gps_cy, cup_z]) snap_cup();          // cup
        }
        translate([gps_cx, gps_cy, lid_z - 1])                      // cable bore
            cylinder(d=cable_d, h=lid_t + gps_riser + 5);
    }
}

// =====================================================================
//  JETSON BOX  <-->  RFD900 CASE  —  now SPLIT into two prints
//  (added 2026-06-15)
//  Lower RFD case stays on the tray (OPEN TOP).  Upper jetbox is a
//  separate print that drops in and SNAP-CLIPS: a 3-sided locating skirt
//  (rear + both sides; front stays open for RFD cabling) carries snap
//  beads that click into grooves in the RFD-case inner walls.
//  Lift the jetbox straight up to service the RFD900.
// =====================================================================
split_z   = deck_z;            // joint plane = old RFD-bay ceiling (17.1)
jb_skirt  = 5;                 // skirt drop into the RFD-case mouth
jb_cl     = 0.4;              // skirt-to-wall clearance (loosen if too tight)
skirt_t   = 1.6;              // skirt wall thickness
jb_bead   = 0.8;             // snap bead protrusion / groove depth
jb_gh     = 2*jb_bead + 0.8; // groove height
jb_snap_z = split_z - 2.8;   // bead centre (inside the RFD mouth)
jb_bw_r   = 30;              // rear bead width
jb_bw_s   = 55;              // side bead length

// inner faces of the RFD case
rc_ix0 = jp_x0 + wall;
rc_ix1 = jp_x0 + jp_ol - wall;
rc_iyp = jp_oy/2 - wall;
jb_sx0 = jp_x0 + (jp_ol - jb_bw_s)/2;   // side bead/groove start (X)

// =====================================================================
//  LID <-> BASE corner bolts   (M3 machine screw + captive nut)   2026-06-16
//  2 FRONT: short screw, lid ear -> cube-case post, nut trapped in the post.
//  2 REAR : long bolt down through the lid ear + jetbox boss, threading into
//           a captive nut in the RFD-case post -> clamps lid + jetbox + tray
//           together, flanking the rear SMA holes.
// =====================================================================
blt_clr_d  = 3.4;          // M3 screw shank clearance
blt_head_d = 6.0;          // socket-cap head counterbore dia (in the lid)
blt_head_h = 3.0;          // counterbore depth
blt_post_d = 11;           // post / boss outer dia (room around the nut)
blt_out_f  = 3.0;          // front bolt centre outboard of the cube-case wall
blt_out_r  = 3.0;          // rear  bolt centre outboard of the jetson-pod wall

blt_nx = cam_x0 + 6;                // NOSE bolts X (camera corners)
blt_ny = cam_oy/2 + blt_out_f;      // NOSE bolts Y (±)
blt_fx = cc_x0 + 6;                 // front bolts X (cube-case corners)
blt_fy = cc_oy/2 + blt_out_f;       // front bolts Y (±)
blt_rx = jp_x0 + jp_ol - 6;         // rear bolts X (near the tail, by the SMAs)
blt_ry = jp_oy/2 + blt_out_r;       // rear bolts Y (±)

nut_af = 5.5;                       // M3 nut across-flats
nut_co = nut_af / cos(30);          // across-corners (hex circumscribed dia)
nut_th = 2.7;                       // M3 nut thickness (+ a hair)

// captive-nut pocket + side insertion slot (opens outward in Y for assembly)
module nut_trap(cx, cy, znut, ysign) {
    translate([cx, cy, znut]) rotate([0,0,30])
        cylinder(d=nut_co + 0.4, h=nut_th + 0.3, $fn=6);
    yy = (ysign > 0) ? cy : cy - 18;
    translate([cx - (nut_af + 0.4)/2, yy, znut])
        cube([nut_af + 0.4, 18, nut_th + 0.3]);
}

// solid base-side post: through clearance bore + captive nut near the top,
// foot blended down onto the base plate
module base_post(cx, cy, z1, edge_y, ysign) {
    difference() {
        union() {
            translate([cx, cy, 0]) cylinder(d=blt_post_d, h=z1);
            hull() {                                   // foot ties post to plate
                translate([cx, cy, 0])     cylinder(d=blt_post_d, h=base_t);
                translate([cx, edge_y, 0]) cylinder(d=4,          h=base_t);
            }
        }
        translate([cx, cy, -1]) cylinder(d=blt_clr_d, h=z1 + 2);
        nut_trap(cx, cy, z1 - 5, ysign);
    }
}

// clearance boss on the jetbox (rear) — the long through-bolt passes straight thru
module clr_boss(cx, cy, z0, z1) {
    difference() {
        translate([cx, cy, z0]) cylinder(d=blt_post_d, h=z1 - z0);
        translate([cx, cy, z0 - 1]) cylinder(d=blt_clr_d, h=(z1 - z0) + 2);
    }
}

// lid ear: pad blended out from the plate edge + clearance + head counterbore
module lid_ear(cx, cy, plate_z, edge_y) {
    eh = blt_head_h + 2;
    difference() {
        union() {
            translate([cx, cy, plate_z]) cylinder(d=blt_post_d, h=eh);
            hull() {
                translate([cx, cy, plate_z])     cylinder(d=blt_post_d, h=lid_t);
                translate([cx, edge_y, plate_z]) cylinder(d=4,          h=lid_t);
            }
        }
        translate([cx, cy, plate_z - 1]) cylinder(d=blt_clr_d, h=eh + 2);
        translate([cx, cy, plate_z + eh - blt_head_h]) cylinder(d=blt_head_d, h=blt_head_h + 1);
    }
}

module nose_bolt_posts() {         // on the tray (camera-case corners)
    base_post(blt_nx,  blt_ny, cam_top_z,  base_w/2,  +1);
    base_post(blt_nx, -blt_ny, cam_top_z, -base_w/2,  -1);
}
module front_bolt_posts() {        // on the tray (cube-case corners)
    base_post(blt_fx,  blt_fy, lid_z,  base_w/2,  +1);
    base_post(blt_fx, -blt_fy, lid_z, -base_w/2,  -1);
}
module rear_bolt_posts() {         // on the tray (RFD-case corners) — hold the nut
    base_post(blt_rx,  blt_ry, split_z,  jp_oy/2,  +1);
    base_post(blt_rx, -blt_ry, split_z, -jp_oy/2,  -1);
}

module rfd_case() {            // LOWER half — stays on the tray, open top
    difference() {
        ybox(jp_x0, jp_ol, jp_oy, base_t, split_z - base_t);
        // RFD bay (now open top)
        ybox(rc_ix0, jp_ol - 2*wall, jp_oy - 2*wall, base_t, split_z - base_t + 1);
        // FRONT fully open: slide RFD in, wiring exits forward
        translate([jp_x0 - 1, -(jp_oy/2 - wall), base_t])
            cube([wall + 2, jp_oy - 2*wall, split_z]);
        // 2x SMA bulkhead holes in the REAR wall
        for (sy=[-rfd_sma_sp/2, rfd_sma_sp/2])
            translate([jp_x0 + jp_ol - wall - 1, sy, base_t + rfd_h/2])
                rotate([0,90,0]) cylinder(d=sma_d, h=wall + 2);
        // SNAP GROOVES for the jetbox beads (rear + both sides)
        translate([rc_ix1, -(jb_bw_r + 4)/2, jb_snap_z - jb_gh/2])               // rear
            cube([jb_bead + 0.4, jb_bw_r + 4, jb_gh]);
        translate([jb_sx0 - 2,  rc_iyp,                   jb_snap_z - jb_gh/2])  // +Y (into wall)
            cube([jb_bw_s + 4, jb_bead + 0.4, jb_gh]);
        translate([jb_sx0 - 2, -rc_iyp - (jb_bead + 0.4), jb_snap_z - jb_gh/2])  // -Y (into wall)
            cube([jb_bw_s + 4, jb_bead + 0.4, jb_gh]);
    }
}

module jetbox() {              // UPPER half — separate print, drops in + clips
    difference() {
        union() {
            // outer walls from the joint up to the pod top
            ybox(jp_x0, jp_ol, jp_oy, split_z, pod_top_z - split_z);
            // 3-sided locating + snap skirt (front open)
            translate([rc_ix1 - jb_cl - skirt_t, -(rc_iyp - jb_cl), split_z - jb_skirt])
                cube([skirt_t, 2*(rc_iyp - jb_cl), jb_skirt]);                       // rear
            translate([rc_ix0 + jb_cl, rc_iyp - jb_cl - skirt_t, split_z - jb_skirt])
                cube([(rc_ix1 - jb_cl) - (rc_ix0 + jb_cl), skirt_t, jb_skirt]);      // +Y
            translate([rc_ix0 + jb_cl, -(rc_iyp - jb_cl), split_z - jb_skirt])
                cube([(rc_ix1 - jb_cl) - (rc_ix0 + jb_cl), skirt_t, jb_skirt]);      // -Y
            // snap beads on the skirt outer faces
            translate([rc_ix1 - jb_cl, -jb_bw_r/2, jb_snap_z])
                rotate([-90,0,0]) cylinder(r=jb_bead, h=jb_bw_r);                    // rear (+X)
            translate([jb_sx0,  rc_iyp - jb_cl, jb_snap_z])
                rotate([0,90,0]) cylinder(r=jb_bead, h=jb_bw_s);                     // +Y
            translate([jb_sx0, -(rc_iyp - jb_cl), jb_snap_z])
                rotate([0,90,0]) cylinder(r=jb_bead, h=jb_bw_s);                     // -Y
        }
        // jetson cavity (open top -> capped by jet_lid)
        ybox(rc_ix0, jp_ol - 2*wall, jp_oy - 2*wall, deck_top, pod_top_z - deck_top + 1);
        // Jetson wiring cutouts (2026-06-16): FRONT (toward cube) + LEFT (-Y) only.
        // Both carried DOWN to the bottom of the box; REAR + RIGHT (+Y) removed;
        // LEFT is 2mm longer (X).  Top edge still jcut_topgap below the rim.
        // FRONT end (toward cube) — full height
        translate([jp_x0 - 1, -jcut_w/2, split_z - 1])
            cube([wall + 2, jcut_w, (pod_top_z - jcut_topgap) - (split_z - 1)]);
        // LEFT (-Y) side — full height, 2mm longer
        translate([jp_x0 + jp_ol/2 - (jcut_w + 2)/2, -jp_oy/2 - 1, split_z - 1])
            cube([jcut_w + 2, wall + 2, (pod_top_z - jcut_topgap) - (split_z - 1)]);
        // herelink-cover snap groove (front face)
        translate([jp_x0 - 0.2, -hc_bead_w/2, hc_snap_z - hc_gh/2])
            cube([hc_bead + 0.6, hc_bead_w, hc_gh]);
    }
    // deck = jetbox floor (sits on the RFD-case rim)
    ybox(rc_ix0, jp_ol - 2*wall, jp_oy - 2*wall, split_z, wall);
    // 4 jetson screw bosses on the deck
    for (hx=jet_hx, hy=jet_hy)
        translate([hx, hy, deck_top]) difference() {
            cylinder(d=jet_boss_d, h=boss_h);
            translate([0,0,-1]) cylinder(d=jet_pilot_d, h=boss_h + 2);
        }
    // rear lid-bolt clearance bosses (the long through-bolt passes here)
    clr_boss(blt_rx,  blt_ry, split_z, pod_top_z);
    clr_boss(blt_rx, -blt_ry, split_z, pod_top_z);
}

// =====================================================================
//  JETSON LID  (drops onto the pod; vent slots for cooling)
// =====================================================================
module jet_lid() {
    difference() {
        union() {
            ybox(jp_x0, jp_ol, jp_oy, pod_top_z, lid_t);            // top plate
            // locating rim into the upper cavity
            translate([jp_x0 + wall + 0.4, -(jp_oy/2 - wall - 0.4), pod_top_z - 3])
                difference() {
                    cube([jp_ol - 2*wall - 0.8, jp_oy - 2*wall - 0.8, 3]);
                    translate([1.6, 1.6, -1])
                        cube([jp_ol - 2*wall - 4, jp_oy - 2*wall - 4, 5]);
                }
        }
        // vent slots
        for (i=[-3:3])
            translate([jp_x0 + jp_ol/2 + i*9 - 2, -16, pod_top_z - 1])
                cube([4, 32, lid_t + 2]);
    }
}

// ----- middle bump-out shroud over the Herelink air unit (lid v2) -----
bo_w      = hl_across + 2*cl + 2*wall;   // 84 — wraps the 78-wide herelink
bo_x0     = hl_x0 - 4;                    // shroud start (X)
bo_x1     = hl_x0 + hl_fore + 4;          // shroud end (X)
bo_z0     = base_t + 2;                   // side walls drop to here (open bottom)
bo_winset = 5;                            // side-window inset from the ends

// lid v3 bump-out: solid (no windows), spans the WHOLE gap, a bit wider
bo3_w  = 90;            // wider, covers the gap
bo3_x0 = cc_x0 + cc_ol;        // gap start (cube case rear)
bo3_x1 = jp_x0;        // gap end (jetson front)
module herelink_bumpout_solid() {
    bo_len = bo3_x1 - bo3_x0;
    difference() {
        // 90-wide top cap (merges with the bridge) + solid side walls
        ybox(bo3_x0, bo_len, bo3_w, bo_z0, (pod_top_z + lid_t) - bo_z0);
        // herelink cavity: open FRONT/REAR + open BOTTOM only; NO side cutouts
        ybox(bo3_x0 - 1, bo_len + 2, bo3_w - 2*wall, bo_z0 - 1, pod_top_z - (bo_z0 - 1));
    }
}

module herelink_bumpout() {               // over + around the herelink, cable room
    bo_len = bo_x1 - bo_x0;
    difference() {
        // 84-wide top cap (merges with the bridge) + side walls
        ybox(bo_x0, bo_len, bo_w, bo_z0, (pod_top_z + lid_t) - bo_z0);
        // herelink cavity: open FRONT/REAR (thru X) + open BOTTOM; cap stays on top
        ybox(bo_x0 - 1, bo_len + 2, bo_w - 2*wall, bo_z0 - 1, pod_top_z - (bo_z0 - 1));
        // cable windows in both side walls (herelink's own cabling)
        translate([bo_x0 + bo_winset,  bo_w/2 - wall - 1, base_t + 5])
            cube([bo_len - 2*bo_winset, wall + 2, 25]);
        translate([bo_x0 + bo_winset, -bo_w/2 - 1,        base_t + 5])
            cube([bo_len - 2*bo_winset, wall + 2, 25]);
    }
}

// =====================================================================
//  FULL LID  (ONE lid for the whole assembly — added 2026-06-15)
//  Stepped: low CUBE level (carries the GPS holder) -> step riser ->
//  high level bridging the herelink gap + capping the JETSON box.
//  Replaces the separate gps_lid + jet_lid.  Locating rim into each box.
//  bo=true adds the middle bump-out shroud over the Herelink (lid v2).
// =====================================================================
module full_lid(bo=0) {     // bo: 0 none | 1 windowed shroud | 2 solid full-gap shroud
    difference() {
        union() {
            // --- CUBE section (low level) ---
            ybox(cc_x0, cc_ol, cc_oy, lid_z, lid_t);
            translate([cc_x0 + wall + 0.4, -(cc_oy/2 - wall - 0.4), lid_z - 3])
                difference() {
                    cube([cc_ol - 2*wall - 0.8, cc_oy - 2*wall - 0.8, 3]);
                    translate([1.6, 1.6, -1]) cube([cc_ol - 2*wall - 4, cc_oy - 2*wall - 4, 5]);
                }
            // GPS pedestal + snap cup (the GPS holder)
            translate([gps_cx, gps_cy, lid_z + lid_t])
                cylinder(d1=ped_bot_d, d2=ped_top_d, h=gps_riser);
            translate([gps_cx, gps_cy, lid_z + lid_t + gps_riser - cup_floor]) snap_cup();
            cab_chute();                                  // Here4 offset-cable guide tube
            // --- step riser: cube level up to jetson level ---
            translate([cc_x0 + cc_ol - wall, -cc_oy/2, lid_z])
                cube([wall, cc_oy, (pod_top_z + lid_t) - lid_z]);
            // --- gap bridge + JETSON section (high level) ---
            ybox(cc_x0 + cc_ol - wall, jp_x0 - (cc_x0 + cc_ol - wall), cc_oy, pod_top_z, lid_t);   // bridge
            ybox(jp_x0, jp_ol, jp_oy, pod_top_z, lid_t);                           // jetson plate
            translate([jp_x0 + wall + 0.4, -(jp_oy/2 - wall - 0.4), pod_top_z - 3])
                difference() {
                    cube([jp_ol - 2*wall - 0.8, jp_oy - 2*wall - 0.8, 3]);
                    translate([1.6, 1.6, -1]) cube([jp_ol - 2*wall - 4, jp_oy - 2*wall - 4, 5]);
                }
            // --- CAMERA section (nose, high level) + step down to the cube ---
            ybox(cam_x0, cam_ol, cam_oy, cam_top_z, lid_t);                        // camera plate
            translate([cam_x0 + wall + 0.4, -(cam_oy/2 - wall - 0.4), cam_top_z - 3])
                difference() {
                    cube([cam_ol - 2*wall - 0.8, cam_oy - 2*wall - 0.8, 3]);
                    translate([1.6, 1.6, -1]) cube([cam_ol - 2*wall - 4, cam_oy - 2*wall - 4, 5]);
                }
            translate([cc_x0 - wall, -cc_oy/2, lid_z])                             // step riser cam->cube
                cube([wall, cc_oy, (cam_top_z + lid_t) - lid_z]);
            // corner lid-bolt ears (2 nose @ cam level, 2 front @ cube level, 2 rear @ jetson level)
            lid_ear(blt_nx,  blt_ny, cam_top_z,  cam_oy/2);
            lid_ear(blt_nx, -blt_ny, cam_top_z, -cam_oy/2);
            lid_ear(blt_fx,  blt_fy, lid_z,      base_w/2);
            lid_ear(blt_fx, -blt_fy, lid_z,     -base_w/2);
            lid_ear(blt_rx,  blt_ry, pod_top_z,  jp_oy/2);
            lid_ear(blt_rx, -blt_ry, pod_top_z, -jp_oy/2);
            // middle bump-out shroud over the Herelink (lid v2 / v3)
            if (bo == 1) herelink_bumpout();
            else if (bo == 2) herelink_bumpout_solid();
        }
        // Here4 OFFSET cable hole (replaces the old centred bore) + cup-floor passage
        cab_cut();
        // vent slots over the jetson
        for (i=[-3:3])
            translate([jp_x0 + jp_ol/2 + i*9 - 2, -16, pod_top_z - 1]) cube([4, 32, lid_t + 2]);
    }
}

// =====================================================================
//  HERELINK COVER  (snap-on shroud; open bottom, cable windows each end)
// =====================================================================
module herelink_cover() {
    cv_x0  = cc_x0 + cc_ol + gap_cl;          // butts the cube case
    cv_x1  = jp_x0 - gap_cl;                   // butts the jetson pod
    cv_len = cv_x1 - cv_x0;
    cv_w   = hl_across + 2*cl + 2*wall;        // wraps the herelink
    top_z  = base_t + hl_h + hc_channel + wall;   // wire channel over the herelink
    pass_z0 = base_t + hl_h - 2;               // pass-through starts near herelink top
    difference() {
        union() {
            // shell: 4 walls + top, open bottom
            difference() {
                translate([cv_x0, -cv_w/2, base_t]) cube([cv_len, cv_w, top_z - base_t]);
                translate([cv_x0 + wall, -(cv_w/2 - wall), base_t - 1])
                    cube([cv_len - 2*wall, cv_w - 2*wall, (top_z - wall) - (base_t - 1)]);
            }
            // snap beads engaging the case grooves
            translate([cv_x0, -hc_bead_w/2, hc_snap_z]) rotate([-90,0,0]) cylinder(r=hc_bead, h=hc_bead_w);
            translate([cv_x1, -hc_bead_w/2, hc_snap_z]) rotate([-90,0,0]) cylinder(r=hc_bead, h=hc_bead_w);
        }
        // cable windows in the +/-Y end walls (herelink's own connectors)
        translate([cv_x0 + 3,  cv_w/2 - wall - 1, base_t + 4]) cube([cv_len - 6, wall + 2, top_z - base_t - 8]);
        translate([cv_x0 + 3, -cv_w/2 - 1,        base_t + 4]) cube([cv_len - 6, wall + 2, top_z - base_t - 8]);
        // cable PASS-THROUGHs front & rear (cube carrier <-> jetson / RFD900, over the herelink)
        translate([cv_x0 - 1,        -hc_pass_w/2, pass_z0]) cube([wall + 2, hc_pass_w, top_z - pass_z0]);
        translate([cv_x1 - wall - 1, -hc_pass_w/2, pass_z0]) cube([wall + 2, hc_pass_w, top_z - pass_z0]);
    }
}

// =====================================================================
//  TRAY  (the one big printed part: plate + both cases)
// =====================================================================
module base_plate() {
    ybox(0, jp_x0, base_w, 0, base_t);                 // front section
    ybox(jp_x0, base_l - jp_x0, jp_oy, 0, base_t);     // flared rear section
}
module tray() { base_plate(); camera_case(); cube_case(); rfd_case();
                nose_bolt_posts(); front_bolt_posts(); rear_bolt_posts(); }

// =====================================================================
//  MOCKUPS
// =====================================================================
module mock() {
    color("purple")    ybox(cam_in_x0, cam_l, cam_w, base_t, cam_h);                 // camera body
    color("black")     translate([cam_x0, 0, cam_lens_z]) rotate([0,90,0]) cylinder(d=cam_lens_d, h=8);  // lens (pokes out)
    color("dimgray")   ybox(cube_x0, cube_l, cube_w, base_t, cube_h);
    color("navy")      translate([gps_cx, gps_cy, lid_z + lid_t + gps_riser]) cylinder(d=gps_d, h=gps_h);
    color("darkgreen") ybox(hl_x0, hl_fore, hl_across, base_t, hl_h);
    color("darkred")   ybox(jet_x0, jet_l, jet_w, jet_z0, jet_h);
    color("orange")    ybox(rfd_x0, rfd_l, rfd_w, base_t, rfd_h);
}

// =====================================================================
//  RENDER
// =====================================================================
if (part == "tray") tray();
else if (part == "jetbox") jetbox();
else if (part == "lid") full_lid(0);
else if (part == "lid2") full_lid(1);       // lid v2: windowed Herelink shroud
else if (part == "lid3") full_lid(2);       // lid v3: solid full-gap shroud
else if (part == "gps") gps_lid();          // old separate lids kept as fallback
else if (part == "jetlid") jet_lid();
else if (part == "hlcover") herelink_cover();
else { tray(); jetbox(); %full_lid(); %herelink_cover(); %mock(); }
