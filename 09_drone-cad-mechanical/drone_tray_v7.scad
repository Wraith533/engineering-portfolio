// =====================================================================
//  Drone component tray  —  v7 "SLEEK".  Cube Orange (+Here4) / Herelink /
//  Jetson / RFD900.   Single BASE + single full-length LID.
//  Faired outline (narrow ends, herelink bulge), raked nose, two-level
//  profiled top, corner chamfers for props, fins on the rear deck.
//  v6 (drone_tray.scad) is untouched — this is a parallel concept.
//
//  AXES:  X = fore-aft (0 nose, +X tail)   Y = across (centred)   Z = up
//  All mm.                                                Generated 2026-06-13
// =====================================================================

part = "assembly";        // "assembly" | "base" | "lid"
$fn  = 72;

// ---------------------------------------------------------------------
//  COMPONENTS (same measured set as v6)
// ---------------------------------------------------------------------
cube_l = 94.5; cube_w = 44.3; cube_h = 31;
gps_d  = 67.8; gps_h  = 14;  gps_riser = 14;
hl_fore = 15.5; hl_across = 78; hl_h = 31;
jet_l = 87; jet_w = 50.5; jet_h = 29;
rfd_l = 57.5; rfd_w = 30; rfd_h = 12.5;

// ---------------------------------------------------------------------
//  SHELL PARAMS
// ---------------------------------------------------------------------
base_t = 4;
wall   = 2.6;
cl     = 0.6;
gap    = 10;
nose_run = 16;            // raked-nose length

// fore-aft layout
cube_x0 = nose_run;
hl_x0   = cube_x0 + cube_l + gap;
jet_x0  = hl_x0 + hl_fore + gap;
jet_x1  = jet_x0 + jet_l;
L       = jet_x1 + 4;
hl_cx   = hl_x0 + hl_fore/2;

// plan widths (faired outline)
W_end   = 58;            // width at the cube / jetson ends
W_bulge = 86;            // width at the herelink bulge
r_end   = 9; r_bulge = 12;
chamf   = 18;            // corner chamfer (prop clearance)

// heights
z_split = 12;            // base/lid parting line
z_rim   = 16;            // base tray wall top
z_nose  = 22;            // nose tip height
z_front = 39;            // top deck over cube + herelink
z_rear  = 55;            // top deck over jetson
x_trans = 132; slope_run = 12;

// GPS stand on the front deck
gps_cx  = cube_x0 + cube_l/2;
cup_wall = 2.5; cup_floor = 2; cup_cl = 0.6; lip = 1.2; lip_h = 1.5;
ped_bot_d = 34; ped_top_d = 26; cable_d = 12;

// RFD compartment / jetson support (in the base)
comp_wall = 2.4; comp_cl = 0.6;
comp_ox = rfd_l + 2*comp_cl + 2*comp_wall;
comp_oy = rfd_w + 2*comp_cl + 2*comp_wall;
deck_z   = base_t + rfd_h + comp_cl;
deck_top = deck_z + comp_wall;
boss_h   = 3;
jet_z0   = deck_top + boss_h;
comp_x1  = L - 1;  comp_x0 = comp_x1 - comp_ox;
jet_hi = 3.5;
jet_hx = [jet_x0 + jet_hi, jet_x1 - jet_hi];
jet_hy = [-(jet_w/2 - jet_hi), (jet_w/2 - jet_hi)];

sma_d = 6.5; rfd_sma_sp = 16;

// base/lid snap joint (continuous bead-and-groove around the faired rim)
j_gap = 0.5;             // base-wall outer to lid-wall inner clearance
bw    = 2.2;             // base perimeter wall thickness
bead  = 0.8;             // snap bead protrusion / groove depth
j_z   = 13.5;            // bead/groove height

echo(str("v7 SLEEK  L=", L, "  W ", W_end, "->", W_bulge, " (bulge)  top ", z_front, "/", z_rear));
echo(str("Jetson top z ", jet_z0 + jet_h, "   GPS top z ", z_front + gps_riser + gps_h));

// =====================================================================
//  PLAN FOOTPRINT  (faired hull of 3 rounded rects, corners chamfered)
// =====================================================================
module fp_rect(xc, len, w, r)
    translate([xc, 0]) offset(r) offset(-r) square([len, w], center=true);

module footprint() {
    difference() {
        hull() {
            fp_rect(25,      50, W_end,   r_end);
            fp_rect(hl_cx,   40, W_bulge, r_bulge);
            fp_rect(L - 25,  50, W_end,   r_end);
        }
        // 4 corner chamfers at the narrow ends (prop clearance)
        for (sx=[0, L], mx=[0,1])
            translate([sx, 0]) mirror([mx,0])
                for (sy=[-1, 1])
                    translate([0, sy*W_end/2])
                        rotate([0,0,45]) translate([-chamf, -chamf]) square([2*chamf, 2*chamf]);
    }
}

// =====================================================================
//  PROFILED SOLID  (footprint inset by `off`, top cut to the side profile)
// =====================================================================
module profiled(off) {
    difference() {
        translate([0,0,z_split]) linear_extrude(z_rear + 6 - z_split) offset(-off) footprint();
        // remove everything above the side profile line
        translate([0, 200, 0]) rotate([90,0,0]) linear_extrude(400)
            polygon([
                [-2,        z_nose  - off],
                [nose_run,  z_front - off],
                [x_trans,   z_front - off],
                [x_trans + slope_run, z_rear - off],
                [L + 2,     z_rear  - off],
                [L + 2,     z_rear + 20],
                [-2,        z_rear + 20]
            ]);
    }
}

// =====================================================================
//  GPS SNAP CUP  (floor bottom at local z=0)
// =====================================================================
module snap_cup() {
    cup_id = gps_d + cup_cl; cup_od = cup_id + 2*cup_wall;
    difference() {
        cylinder(d=cup_od, h=cup_floor + gps_h);
        translate([0,0,cup_floor]) cylinder(d=cup_id, h=gps_h - lip_h + 0.01);
        translate([0,0,cup_floor + gps_h - lip_h]) cylinder(d1=cup_id, d2=cup_id - 2*lip, h=lip_h + 0.5);
        translate([0,0,-1]) cylinder(d=cable_d, h=cup_floor + 2);
        for (a=[0:90:359]) rotate([0,0,a+45]) translate([cup_id/2 - 1, -1.2, cup_floor + 3]) cube([cup_wall + 3, 2.4, gps_h]);
    }
}

// rear-deck cooling fins (Silvus look) over the jetson
fin_hw = 16;             // fin half-width (kept inside the tapered/chamfered deck)
module deck_fins() {
    n = 7; x0 = jet_x0 + 8; x1 = jet_x1 - 16; pitch = (x1 - x0)/(n - 1);
    for (i=[0:n-1])
        translate([x0 + i*pitch, 0, z_rear - 0.5])
            hull() for (sy=[-1,1]) translate([0, sy*fin_hw, 0]) cylinder(d=2.4, h=2.6);
}

// =====================================================================
//  LID
// =====================================================================
module lid() {
    union() {
        difference() {
            profiled(0);
            profiled(wall);                          // hollow -> shell, open bottom
            // snap GROOVE on the inner wall (receives the base bead)
            translate([0,0,j_z - 0.5]) linear_extrude(bead + 2)
                difference() { offset(-wall + bead + 0.4) footprint(); offset(-wall) footprint(); }
            // cable bore under the GPS cup, into the cube
            translate([gps_cx, 0, z_front - 3]) cylinder(d=cable_d, h=gps_riser + 10);
            // vent slots over the jetson (between the fins)
            for (i=[0:5])
                translate([jet_x0 + 14 + i*11, 0, z_rear - 1]) cube([5, 2*fin_hw, wall + 4], center=true);
            // herelink cable slots, both bulge sides
            for (sy=[-1,1])
                translate([hl_cx, sy*(W_bulge/2 - wall - 1), z_split + 8]) cube([26, wall + 4, 18], center=true);
        }
        // GPS pedestal + snap cup on the front deck
        translate([gps_cx, 0, z_front - 1]) cylinder(d1=ped_bot_d, d2=ped_top_d, h=gps_riser + 1);
        difference() {
            translate([gps_cx, 0, z_front + gps_riser]) snap_cup();
            translate([gps_cx, 0, z_front - 3]) cylinder(d=cable_d, h=gps_riser + 10);
        }
        deck_fins();
    }
}

// =====================================================================
//  BASE  (shallow faired tray + RFD compartment + jetson bosses + ribs)
// =====================================================================
module base() {
    difference() {
        union() {
            linear_extrude(base_t) footprint();                 // floor
            // perimeter wall (sits inside the lid wall with j_gap clearance)
            linear_extrude(z_rim) difference() {
                offset(-wall - j_gap) footprint();
                offset(-wall - j_gap - bw) footprint();
            }
            // snap BEAD ring on the wall outer face
            translate([0,0,j_z]) linear_extrude(2) difference() {
                offset(-wall + bead - 0.5) footprint();
                offset(-wall - j_gap) footprint();
            }
            // RFD compartment (rear): open top + open FRONT for wiring
            translate([comp_x0, -comp_oy/2, base_t])
                difference() {
                    cube([comp_ox, comp_oy, deck_top - base_t]);
                    translate([comp_wall, comp_wall, 0])
                        cube([comp_ox - 2*comp_wall, comp_oy - 2*comp_wall, rfd_h + comp_cl + 0.1]);
                    translate([-1, comp_wall, 0])
                        cube([comp_wall + 1.1, comp_oy - 2*comp_wall, rfd_h + comp_cl + 0.1]);
                }
            // deck over the RFD bay (jetson floor)
            translate([comp_x0 + comp_wall, -(comp_oy/2 - comp_wall), deck_z])
                cube([comp_ox - 2*comp_wall, comp_oy - 2*comp_wall, comp_wall]);
            // 4 jetson support posts, full height from the floor to jet_z0
            for (hx=jet_hx, hy=jet_hy)
                translate([hx, hy, base_t]) cylinder(d=6.5, h=jet_z0 - base_t);
            // herelink cradle ribs (capture the standing fin)
            for (sx=[-1,1])
                translate([hl_cx + sx*(hl_fore/2 + cl) - wall/2, -hl_across/2, base_t])
                    cube([wall, hl_across, 12]);
        }
        // RFD SMA holes out the rear (through compartment + body wall)
        for (sy=[-rfd_sma_sp/2, rfd_sma_sp/2])
            translate([comp_x1 - comp_wall - 1, sy, base_t + rfd_h/2]) rotate([0,90,0]) cylinder(d=sma_d, h=20);
        // jetson screw pilots
        for (hx=jet_hx, hy=jet_hy)
            translate([hx, hy, jet_z0 - 7]) cylinder(d=2.1, h=8);
    }
}

// =====================================================================
//  MOCKUPS
// =====================================================================
module mock() {
    color("dimgray")   translate([cube_x0, -cube_w/2, base_t]) cube([cube_l, cube_w, cube_h]);
    color("navy")      translate([gps_cx, 0, z_front + gps_riser]) cylinder(d=gps_d, h=gps_h);
    color("darkgreen") translate([hl_x0, -hl_across/2, base_t]) cube([hl_fore, hl_across, hl_h]);
    color("darkred")   translate([jet_x0, -jet_w/2, jet_z0]) cube([jet_l, jet_w, jet_h]);
    color("orange")    translate([comp_x0 + comp_wall + comp_cl, -rfd_w/2, base_t]) cube([rfd_l, rfd_w, rfd_h]);
}

// =====================================================================
//  RENDER
// =====================================================================
if (part == "base") base();
else if (part == "lid") lid();
else { base(); %mock(); %lid(); }
