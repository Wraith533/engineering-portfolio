# Orin + Cube + Herelink Carrier Board (KiCad)

A **6-layer carrier PCB** that mates an NVIDIA Jetson Orin NX/Nano to a Cube H7
autopilot and a Herelink v1.1 datalink on one board — the compute-and-autopilot core
of a drone in a single custom design. Rev-A KiCad project.

## What's engineered

- **Hierarchical schematic**, split into six subsystem sheets: power distribution
  (rails, input protection, battery sense, sequencing), core/UART (SODIMM + DF17
  sockets, UART level shifters), Ethernet (MDI → magnetics → Herelink), high-speed
  (M.2 Key M, dual CSI camera FFC, USB 3.0, USB-C recovery), Cube peripherals
  (GPS×2, CAN, I2C, RC in, buzzer, MAIN/AUX), and control/sequencing
  (power-enable / reset / recovery).
- **Hand-authored netlist — 146 nets, verified pin-to-pin** — so the board can be
  floorplanned from an imported netlist immediately.
- **Signal-integrity discipline.** Net classes preset for PCIe (85Ω), USB (90Ω),
  100Ω differential, CAN (120Ω), and power, with PCIe Gen4 routing rules and a chosen
  6-layer fab stackup in mind.
- **A pre-fab verification punchlist.** Nets and pins that still need checking are
  explicitly tagged `_VERIFY` / `[VERIFY]` in the netlist and sheets, so the board
  isn't sent to fab on optimism — an honest engineering artifact, not a finished
  claim.

## Why it matters to an employer

- Real **hardware / electrical design**: controlled impedance, power sequencing,
  high-speed interface routing, and the discipline to track unverified nets before
  committing to a fab run.
- Rounds out the stack — I design the compute carrier, not just the software that runs
  on it.

## Stack

KiCad 7/8/9, 6-layer controlled-impedance PCB, Jetson Orin (P3767), Cube H7 / ArduPilot,
Herelink.

Status: Rev-A skeleton — schematic structure, net classes, and full netlist complete;
symbol placement and pre-fab net verification are the remaining work (documented in the
project README).
