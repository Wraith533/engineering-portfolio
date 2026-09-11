// =====================================================================
//  DRONE BATTERY CASE + FRONT CAP   —   belly-mounted, FRONT-LOADING
//  (rev2 2026-06-15 — battery now slides in from the FRONT, not the top)
//  Battery: 132 (length, X) x 80 (width, Y) x 54 (thick, Z).
//  Case is closed on top/bottom/both sides/rear; OPEN at the +X front.
//  Battery slides in lengthwise; the front CAP snap-clips on and carries
//  the XT60 pass-through. Top stays solid -> mounts flat to the drone.
//
//  AXES: X = length (centred 0, +X = front)  Y = width (centred 0)
//        Z = up (0 = bottom / ground side)
// =====================================================================
part = "assembly";   // "case" | "lid" (= front cap) | "assembly"
$fn  = 72;

// ----- battery ----------------------------------------------------
bx = 132; by = 80; bz = 54;

// ----- build ------------------------------------------------------
wall    = 3;        // side / rear wall thickness
floor_t = 3;        // bottom (ground side)
top_t   = 3;        // top (drone side, solid)
cl      = 1.0;      // clearance around the battery (LiPos swell)
flange_t = 3;       // front-cap face plate
cap_plug = 6;       // how deep the cap plugs into the cavity
cap_cl   = 0.4;     // cap plug clearance

// ----- XT60 pass-through in the FRONT cap -------------------------
xt_h = 14;          // hole height (Z)
xt_w = 22;          // hole width  (Y)
xt_r = 3;           // corner radius
// xt_zc set below (centred on battery height by default)

// ----- snap-fit cap (bead-in-groove, all 4 plug faces) ------------
bead = 0.8;         // snap bead protrusion / groove depth
b_gh = 2*bead + 0.8;
pry  = 14;          // pry-notch width in the cap (top edge)

// ----- zip-tie ridge on top (frame tie-down) ----------------------
ridge_w = 43;       // ridge width (Y)
ridge_l = 135;      // ridge length (X) — capped to fit (case is only 143 long;
                    //   asked-for 160 would overhang the rear ~17mm)
ridge_h = 14;       // ridge height (meat for the slots)
zt_n  = 6;          // number of zip-tie slots
zt_sx = 9;          // slot size fore-aft (X)
zt_sz = 5;          // slot size vertical (Z)
zt_r  = 2;          // slot corner radius

// ----- derived ----------------------------------------------------
iax = bx + 2*cl;            // cavity length (battery + clearance)
iay = by + 2*cl;            // cavity width
iaz = bz + cl;              // cavity height
cav_len = iax + cap_plug;   // cavity also houses the cap plug at the front
ox = wall + cav_len;        // outer length (rear wall + cavity, front open)
oy = iay + 2*wall;          // outer width
OH = floor_t + iaz + top_t; // overall height

front_x = ox/2;             // open front face
rear_in = -ox/2 + wall;     // rear inner wall
x_snap  = front_x - cap_plug/2;     // bead/groove centre (mid plug depth)
xt_zc   = floor_t + iaz/2;          // XT60 hole centre height

echo(str("CASE outer ", ox, " x ", oy, " x ", OH, " mm  + cap ", flange_t,
         "  (battery ", bx, "x", by, "x", bz, ")"));
echo(str("Front-load: battery slides in +X.  XT60 hole ", xt_w, "x", xt_h,
         " centred z=", xt_zc));

// ----- helpers ----------------------------------------------------
module box(l, w, z0, h) { translate([-l/2, -w/2, z0]) cube([l, w, h]); }
module rrect(l, w, r) { hull() for (sx=[-1,1], sy=[-1,1])
        translate([sx*(l/2-r), sy*(w/2-r)]) circle(r); }

// =====================================================================
//  CASE  (closed top/bottom/sides/rear; OPEN front; snap grooves)
// =====================================================================
module ridge() {            // raised tie-down rib on the top
    box(ridge_l, ridge_w, OH - 0.01, ridge_h + 0.01);
}
module ziptie_slots() {     // transverse (Y) slots through the ridge
    for (i = [0 : zt_n-1]) {
        xx = -ridge_l/2 + ridge_l*(i + 0.5)/zt_n;
        translate([xx, -(ridge_w/2 + 2), OH + ridge_h/2])
            rotate([-90,0,0]) linear_extrude(ridge_w + 4) rrect(zt_sx, zt_sz, zt_r);
    }
}

module bat_case() {
    difference() {
        union() {
            box(ox, oy, 0, OH);
            ridge();
        }
        // cavity, open at the +X front
        translate([rear_in, -iay/2, floor_t]) cube([cav_len + 1, iay, iaz]);
        // zip-tie slots through the ridge
        ziptie_slots();
        // snap grooves cut INTO the cavity walls near the front (4 faces)
        // top wall groove (cut up into the top)
        translate([x_snap - 30, -iay/2, floor_t + iaz])           cube([60, iay, bead+0.4]);
        // bottom wall groove (cut down into the floor)
        translate([x_snap - 30, -iay/2, floor_t - (bead+0.4)])    cube([60, iay, bead+0.4]);
        // +Y / -Y side grooves
        translate([x_snap - 18,  iay/2,            floor_t+3]) cube([36, bead+0.4, iaz-6]);
        translate([x_snap - 18, -iay/2-(bead+0.4), floor_t+3]) cube([36, bead+0.4, iaz-6]);
        // drain / vent holes in the floor
        for (sx=[-1,1]) translate([sx*iax/4, 0, -1]) cylinder(d=6, h=floor_t+2);
    }
}

// =====================================================================
//  FRONT CAP  (face plate + plug into the cavity + XT60 hole + snaps)
// =====================================================================
module bat_lid() {              // "lid" name kept for the output filename
    plug_w = iay - 2*cap_cl;
    plug_h = iaz - 2*cap_cl;
    difference() {
        union() {
            // face plate over the whole front
            translate([front_x, -oy/2, 0]) cube([flange_t, oy, OH]);
            // plug into the cavity front
            translate([front_x - cap_plug, -plug_w/2, floor_t + cap_cl])
                cube([cap_plug, plug_w, plug_h]);
            // snap beads on the 4 plug faces (toward each wall)
            translate([x_snap, 0, floor_t + iaz - cap_cl]) rotate([-90,0,0])
                translate([0,0,-30]) cylinder(r=bead, h=60);                 // top (+Z)
            translate([x_snap, 0, floor_t + cap_cl]) rotate([-90,0,0])
                translate([0,0,-30]) cylinder(r=bead, h=60);                 // bottom (-Z)
            translate([x_snap,  iay/2 - cap_cl, floor_t + iaz/2])
                translate([0,0,-18]) cylinder(r=bead, h=36);                 // +Y
            translate([x_snap, -(iay/2 - cap_cl), floor_t + iaz/2])
                translate([0,0,-18]) cylinder(r=bead, h=36);                 // -Y
        }
        // XT60 pass-through (through plug + face plate)
        translate([front_x - cap_plug - 1, 0, xt_zc]) rotate([0,90,0])
            linear_extrude(cap_plug + flange_t + 2) rrect(xt_h, xt_w, xt_r);
        // pry notch on the top edge of the face plate
        translate([front_x - 0.01, -pry/2, OH - flange_t]) cube([flange_t + 1, pry, top_t + 1]);
    }
}

// =====================================================================
//  MOCKS / RENDER
// =====================================================================
module mock() {
    color("dimgray") translate([rear_in + cl + bx/2, 0, floor_t + cl/2])
        box(bx, by, 0, bz);                                   // battery (slid in)
    color("gold") translate([front_x + flange_t, 0, xt_zc]) rotate([0,90,0])
        linear_extrude(10) rrect(8, 16, 1.5);                 // XT60 stub out the front
}

if      (part == "case") bat_case();
else if (part == "lid")  bat_lid();
else { bat_case(); %bat_lid(); %mock(); }
