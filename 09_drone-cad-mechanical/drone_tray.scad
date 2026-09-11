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

// ---------------------------------------------------------------------
//  COMPONENTS  (measured / *assumed)
// ---------------------------------------------------------------------
cube_l = 94.5; cube_w = 44.3; cube_h = 31;        // Cube Orange + carrier
gps_d  = 67.8; gps_h  = 14;  gps_riser = 16;       // Here4 round (213 circ); *h assumed
hl_fore = 15.5; hl_across = 78; hl_h = 31;         // Herelink, spun (overhangs width)
jet_l = 87; jet_w = 50.5; jet_h = 29;              // Jetson Orin carrier
rfd_l = 57.5; rfd_w = 30; rfd_h = 12.5;            // RFD900x

// Jetson carrier mounting (4 corner holes)
jet_hole_inset = 3.5;     // *holes inset from board edges (CONFIRM)
jet_screw_d    = 2.5;     // *M2.5 (CONFIRM)
jet_boss_d     = 6;
jet_pilot_d    = 2.1;     // M2.5 self-tap pilot
boss_h         = 3;       // boss height above the deck (jetson floats clear)

// Openings (RFD antennas aft, all wiring forward)
sma_d      = 6.5;         // RFD900 SMA bulkhead hole
rfd_sma_sp = 16;          // *RFD SMA spacing center-to-center (CONFIRM)
jet_cut_w  = 30; jet_cut_h = 16;   // Jetson wiring cutout in the upper FRONT wall

// ---------------------------------------------------------------------
//  CUBE CASE  (open-top box, Here4 lid drops on; rear cable cutout)
// ---------------------------------------------------------------------
cc_x0  = 0;
cc_ol  = cube_l + 2*cl + 2*wall;                   // outer length
cc_oy  = cube_w + 2*cl + 2*wall;                   // outer width (<= base_w)
cc_h   = cube_h + cl;                              // wall height (open top)
cc_cut_w = 32; cc_cut_h = 20;                      // rear cable cutout

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
hl_x0  = cc_ol + gap;
jp_x0  = hl_x0 + hl_fore + gap;

// ---------------------------------------------------------------------
//  JETSON POD  (RFD tray below + Jetson case above; rear OPEN for cables)
// ---------------------------------------------------------------------
jp_ol  = jet_l + 2*cl + 2*wall;                    // outer length
jp_oy  = jet_w + 2*cl + 2*wall;                    // outer width (> base_w -> flare)
base_l = jp_x0 + jp_ol + rear_margin;

deck_z   = base_t + rfd_h + cl;                    // RFD bay ceiling (deck underside)
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
//  JETSON POD  (RFD tray + Jetson case, rear OPEN, deck + screw bosses)
// =====================================================================
module jetson_pod() {
    difference() {
        ybox(jp_x0, jp_ol, jp_oy, base_t, pod_h);
        // RFD bay (lower cavity, base = floor)
        ybox(jp_x0 + wall, jp_ol - 2*wall, jp_oy - 2*wall, base_t, rfd_h + cl + 0.1);
        // jetson cavity (upper, open top -> capped by jet_lid)
        ybox(jp_x0 + wall, jp_ol - 2*wall, jp_oy - 2*wall, deck_top, pod_h);
        // RFD bay FRONT fully open: slide RFD in here, wiring exits forward
        translate([jp_x0 - 1, -(jp_oy/2 - wall), base_t])
            cube([wall + 2, jp_oy - 2*wall, rfd_h + cl + 0.1]);
        // 2x SMA bulkhead holes in the REAR wall (RFD antennas out the tail)
        for (sy=[-rfd_sma_sp/2, rfd_sma_sp/2])
            translate([jp_x0 + jp_ol - wall - 1, sy, base_t + rfd_h/2])
                rotate([0,90,0]) cylinder(d=sma_d, h=wall + 2);
        // Jetson wiring cutout in the upper FRONT wall
        translate([jp_x0 - 1, -jet_cut_w/2, deck_top + 2])
            cube([wall + 2, jet_cut_w, jet_cut_h]);
        // snap groove for the herelink cover (front/gap-facing face)
        translate([jp_x0 - 0.2, -hc_bead_w/2, hc_snap_z - hc_gh/2])
            cube([hc_bead + 0.6, hc_bead_w, hc_gh]);
    }
    // deck separating RFD bay from the jetson (supported on rear + 2 sides)
    ybox(jp_x0 + wall, jp_ol - 2*wall, jp_oy - 2*wall, deck_z, wall);
    // 4 jetson screw bosses on the deck
    for (hx=jet_hx, hy=jet_hy)
        translate([hx, hy, deck_top]) difference() {
            cylinder(d=jet_boss_d, h=boss_h);
            translate([0,0,-1]) cylinder(d=jet_pilot_d, h=boss_h + 2);
        }
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
module tray() { base_plate(); cube_case(); jetson_pod(); }

// =====================================================================
//  MOCKUPS
// =====================================================================
module mock() {
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
else if (part == "gps") gps_lid();
else if (part == "jetlid") jet_lid();
else if (part == "hlcover") herelink_cover();
else { tray(); %gps_lid(); %jet_lid(); %herelink_cover(); %mock(); }
