// =====================================================================
//  Drone component tray  —  v16 "flight-ready polish".
//  + anti-vibration frame mounting ears (M3 + grommet seats), M3 heat-set
//  insert bosses for the Jetson, forward orientation arrow + FWD label,
//  bottom-edge chamfer.  Parts: "base" | "lid" | "rfdlid".  v6..v15 kept.
//  --- original header ---
//  v15 "open-bottom herelink ducts".
//  Cube Orange (+Here4) / Herelink / Jetson / RFD900.  BASE + full LID.
//  v13 + RFD bay is now a separate SNAP LID (drop the radio in from the
//  top) and both duct runs bumped to 38mm for the bent micro-HDMI.
//  Parts now: "base" | "lid" | "rfdlid".  v6..v13 untouched.
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

// Here4 cable hole (measured) + path down to the cube carrier
gps_cab_w = 7.5; gps_cab_l = 10;       // hole: width (Y) x length (fore-aft)
gps_cab_back = 12.3;                    // hole centre from the GPS back edge
gps_cab_cl = 1.5;                       // clearance around the cable
gps_cab_x = gps_cx + gps_d/2 - gps_cab_back;   // true hole X (toward the tail)
cab_sx = gps_cab_l + gps_cab_cl;        // path size fore-aft
cab_sy = gps_cab_w + gps_cab_cl;        // path size across
cab_cw = 2;                             // chute wall

// RFD bay (rear, base) + snap lid + jetson support
comp_wall = 2.4; comp_cl = 0.6;
comp_ox = rfd_l + 2*comp_cl + 2*comp_wall;
comp_oy = rfd_w + 2*comp_cl + 2*comp_wall;
comp_ix = comp_ox - 2*comp_wall;
comp_iy = comp_oy - 2*comp_wall;
rfd_bay_h = rfd_h + comp_cl;           // bay interior height = wall height
rfd_lid_t = 2.4;
rgd = 0.9;                             // RFD lid snap bead/groove depth
rgroove_z = base_t + rfd_bay_h - 4;    // snap height
deck_top = base_t + rfd_bay_h + rfd_lid_t;  // top of the closed bay (lid on)
boss_h   = 3;
jet_z0   = deck_top + boss_h;          // jetson floats above the closed bay
comp_x1  = L - 1;  comp_x0 = comp_x1 - comp_ox;
comp_cx  = comp_x0 + comp_ox/2;
jet_hi = 3.5;
jet_hx = [jet_x0 + jet_hi, jet_x1 - jet_hi];
jet_hy = [-(jet_w/2 - jet_hi), (jet_w/2 - jet_hi)];

sma_d = 6.5; rfd_sma_sp = 16;

// base/lid snap joint (continuous bead-and-groove around the faired rim)
j_gap = 0.5;             // base-wall outer to lid-wall inner clearance
bw    = 2.2;             // base perimeter wall thickness
bead  = 0.8;             // snap bead protrusion / groove depth
j_z   = 13.5;            // bead/groove height

// frame mounting ears (anti-vibration; PARAMETRIC — match to your frame)
mount_x = [40, 200];     // fore-aft mount stations
mount_y = W_end/2 + 9;   // hole offset from centreline
ear_w   = 15;            // ear size
mh      = 3.4;           // M3 clearance hole
mh_cb   = 6.8;           // grommet / washer seat dia
bch     = 1.4;           // base bottom-edge chamfer
ins_d   = 4.0;           // M3 heat-set insert bore

echo(str("v16 flight-ready  L=", L, "  mount span ", mount_x[1]-mount_x[0], " x ", 2*mount_y, "  (M3 ears + inserts)"));
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
        // (Here4 cable exits offset, not centred — path bored in lid() via cab_cut)
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
//  CABLE-ROUTING DUCTS  (each side of the middle: out duct_out, down
//  duct_down; hollow elbow built into the shell, opens into the bay)
// =====================================================================
duct_out = 38; duct_down = 23; duct_dw = 24; duct_bore = 13; duct_wall = 2.5;  // out 38 for bent micro-HDMI (v14)
duct_h  = duct_bore + 2*duct_wall;     // cross-section height / column thickness
duct_zc = 27;                          // horizontal-run centreline z

// duct stations: xc = centre, yw = half-width, dw = width, zc = height, dwn = drop, out = straight run
hl_dyw  = W_bulge/2;                   // herelink ducts (on the bulge)
jet_dx  = 186; jet_dyw = W_end/2;      // jetson ducts (for the micro-HDMI)
jet_dw  = 3 * duct_dw;                 // WIDE, to align with the HDMI port
jet_zc  = 42;                          // raised UP, clear of the prop disc
jet_down = 10;                         // shallow drop so it stays up high
jet_out  = 38;                         // straight run for the bent micro-HDMI (v14)

module duct_outer(xc, yw, side, dw, zc, dwn, out) {
    yo = yw + out; y_in = yw - 4;
    mirror([0, side < 0 ? 1 : 0, 0]) union() {
        // horizontal run out from the side wall
        translate([xc - dw/2, y_in, zc - duct_h/2]) cube([dw, yo - y_in, duct_h]);
        // vertical run dropping at the outboard end
        translate([xc - dw/2, yo - duct_h, zc + duct_h/2 - dwn]) cube([dw, duct_h, dwn]);
    }
}
module duct_bore(xc, yw, side, dw, zc, dwn, out) {
    yo = yw + out; y_in = yw - 7; bx = dw - 2*duct_wall;
    mirror([0, side < 0 ? 1 : 0, 0]) union() {
        translate([xc - bx/2, y_in, zc - duct_bore/2]) cube([bx, (yo - duct_wall) - y_in, duct_bore]);
        translate([xc - bx/2, yo - duct_h + duct_wall, zc + duct_h/2 - dwn - 2]) cube([bx, duct_bore, dwn + 2]);
    }
}
// open the floor along a duct's horizontal run (cable drops out the bottom)
module duct_botopen(xc, yw, side, dw, zc, out) {
    yo = yw + out; y_in = yw - 7; bx = dw - 2*duct_wall;
    mirror([0, side < 0 ? 1 : 0, 0])
        translate([xc - bx/2, y_in, zc - duct_h/2 - 1])
            cube([bx, (yo - duct_wall) - y_in, duct_h/2 + duct_bore/2 + 1]);
}

// Here4 cable chute: guided tube from the cup floor down to the deck
module cab_chute() {
    translate([gps_cab_x, 0, z_front - wall])
        linear_extrude((z_front + gps_riser) - (z_front - wall))
            square([cab_sx + 2*cab_cw, cab_sy + 2*cab_cw], center=true);
}
// the cable hole itself: bay -> deck -> chute -> cup floor
module cab_cut() {
    translate([gps_cab_x, 0, z_front - wall - 4])
        linear_extrude((z_front + gps_riser + cup_floor + 1) - (z_front - wall - 4))
            square([cab_sx, cab_sy], center=true);
}

// =====================================================================
//  LID
// =====================================================================
module lid() {
    union() {
        difference() {
            union() {
                profiled(0);
                duct_outer(hl_cx,  hl_dyw,  1, duct_dw, duct_zc, duct_down, duct_out); duct_outer(hl_cx,  hl_dyw,  -1, duct_dw, duct_zc, duct_down, duct_out);
                duct_outer(jet_dx, jet_dyw, 1, jet_dw,  jet_zc,  jet_down,  jet_out);  duct_outer(jet_dx, jet_dyw, -1, jet_dw,  jet_zc,  jet_down,  jet_out);
            }
            profiled(wall);                          // hollow -> shell, open bottom
            // snap GROOVE on the inner wall (receives the base bead)
            translate([0,0,j_z - 0.5]) linear_extrude(bead + 2)
                difference() { offset(-wall + bead + 0.4) footprint(); offset(-wall) footprint(); }
            // Here4 cable path opened through the deck into the cube bay
            cab_cut();
            // forward orientation arrow + label, recessed in the nose deck
            translate([26, 0, z_front - 1]) linear_extrude(1.3)
                polygon([[-8,0],[-2,6],[-2,2.5],[6,2.5],[6,-2.5],[-2,-2.5],[-2,-6]]);
            translate([34, 0, z_front - 0.8]) linear_extrude(1.1)
                text("FWD", size=6, font="Liberation Sans:style=Bold", halign="left", valign="center");
            // vent slots over the jetson (between the fins)
            for (i=[0:5])
                translate([jet_x0 + 14 + i*11, 0, z_rear - 1]) cube([5, 2*fin_hw, wall + 4], center=true);
            // duct bores (also open the bay walls)
            duct_bore(hl_cx,  hl_dyw,  1, duct_dw, duct_zc, duct_down, duct_out); duct_bore(hl_cx,  hl_dyw,  -1, duct_dw, duct_zc, duct_down, duct_out);
            duct_bore(jet_dx, jet_dyw, 1, jet_dw,  jet_zc,  jet_down,  jet_out);  duct_bore(jet_dx, jet_dyw, -1, jet_dw,  jet_zc,  jet_down,  jet_out);
            // open the bottoms of ALL ducts (cable drops out / bends freely underneath)
            duct_botopen(jet_dx, jet_dyw, 1, jet_dw, jet_zc, jet_out);  duct_botopen(jet_dx, jet_dyw, -1, jet_dw, jet_zc, jet_out);
            duct_botopen(hl_cx,  hl_dyw,  1, duct_dw, duct_zc, duct_out); duct_botopen(hl_cx,  hl_dyw,  -1, duct_dw, duct_zc, duct_out);
        }
        // GPS pedestal + snap cup + cable chute on the front deck (path bored)
        difference() {
            union() {
                translate([gps_cx, 0, z_front - 1]) cylinder(d1=ped_bot_d, d2=ped_top_d, h=gps_riser + 1);
                cab_chute();
                translate([gps_cx, 0, z_front + gps_riser]) snap_cup();
            }
            cab_cut();
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
            // floor with a chamfered bottom edge
            hull() {
                linear_extrude(0.1) offset(-bch) footprint();
                translate([0,0,bch]) linear_extrude(0.1) footprint();
            }
            translate([0,0,bch]) linear_extrude(base_t - bch) footprint();
            mount_ears();                                       // frame mounting ears
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
            // RFD bay (rear): OPEN TOP for the snap lid; open FRONT for wiring
            difference() {
                translate([comp_x0, -comp_oy/2, base_t]) cube([comp_ox, comp_oy, rfd_bay_h]);
                translate([comp_x0 + comp_wall, -comp_iy/2, base_t - 1]) cube([comp_ix, comp_iy, rfd_bay_h + 2]);   // cavity, open top
                translate([comp_x0 - 1, -comp_iy/2, base_t - 1]) cube([comp_wall + 1.1, comp_iy, rfd_h + comp_cl + 1]); // open front
                translate([comp_cx, 0, rgroove_z]) linear_extrude(2.2)                                              // snap groove
                    difference() { square([comp_ix + 2*rgd, comp_iy + 2*rgd], center=true); square([comp_ix, comp_iy], center=true); }
            }
            // 4 jetson support posts (sized for M3 heat-set inserts)
            for (hx=jet_hx, hy=jet_hy)
                translate([hx, hy, base_t]) cylinder(d=7.6, h=jet_z0 - base_t);
            // herelink cradle ribs (capture the standing fin)
            for (sx=[-1,1])
                translate([hl_cx + sx*(hl_fore/2 + cl) - wall/2, -hl_across/2, base_t])
                    cube([wall, hl_across, 12]);
        }
        // RFD SMA holes out the rear (through compartment + body wall)
        for (sy=[-rfd_sma_sp/2, rfd_sma_sp/2])
            translate([comp_x1 - comp_wall - 1, sy, base_t + rfd_h/2]) rotate([0,90,0]) cylinder(d=sma_d, h=20);
        // jetson M3 heat-set insert bores
        for (hx=jet_hx, hy=jet_hy)
            translate([hx, hy, jet_z0 - 6]) cylinder(d=ins_d, h=7);
        // frame mount holes (M3 thru + grommet seat + flush head)
        mount_holes();
    }
}

// frame mounting ears + holes
module mount_ears() {
    for (mx = mount_x, sy=[-1,1])
        hull() {
            translate([mx, sy*mount_y, 0]) cylinder(d=ear_w, h=base_t);
            translate([mx - ear_w/2, sy*(mount_y - 16), 0]) cube([ear_w, 0.1, base_t]);
        }
}
module mount_holes() {
    for (mx = mount_x, sy=[-1,1]) translate([mx, sy*mount_y, 0]) {
        translate([0,0,-1]) cylinder(d=mh, h=base_t + 2);
        translate([0,0,base_t - 1.6]) cylinder(d=mh_cb, h=2);              // top grommet/washer seat
        translate([0,0,-0.01]) cylinder(d1=mh_cb, d2=mh, h=1.6);          // bottom countersink (flush head)
    }
}

// =====================================================================
//  RFD900 BAY SNAP LID  (drops in from the top, bead snaps into the bay groove)
// =====================================================================
module rfd_lid() {
    rim_ox = comp_ix - 0.6; rim_oy = comp_iy - 0.6;   // 0.3 clearance/side
    rim_t = 1.6; rim_h = rfd_bay_h - 1.5;
    union() {
        // top plate on the wall tops
        translate([comp_x0, -comp_oy/2, base_t + rfd_bay_h]) cube([comp_ox, comp_oy, rfd_lid_t]);
        // rim ring dropping into the cavity
        translate([comp_cx, 0, base_t + rfd_bay_h - rim_h]) linear_extrude(rim_h)
            difference() { square([rim_ox, rim_oy], center=true); square([rim_ox - 2*rim_t, rim_oy - 2*rim_t], center=true); }
        // snap bead ring on the rim outer face (engages the bay groove)
        translate([comp_cx, 0, rgroove_z]) linear_extrude(1.8)
            difference() { square([rim_ox + 2*(rgd - 0.1), rim_oy + 2*(rgd - 0.1)], center=true); square([rim_ox - 0.5, rim_oy - 0.5], center=true); }
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
else if (part == "rfdlid") rfd_lid();
else { base(); %mock(); %rfd_lid(); %lid(); }
