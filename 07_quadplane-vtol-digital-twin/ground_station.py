#!/usr/bin/env python3
"""
Nomad Digital Command Center
----------------------------
Tk slider GUI -> KB2040 USB CDC at 115200, 50 Hz.
KB2040 sketch (nomad_bridge.ino) packs the channel values into CRSF and
streams them at 420000 baud to the RadioMaster Nomad on JR-bay pin 1.

Channels sent (comma-separated, newline-terminated):
   CH1 Roll, CH2 Pitch, CH3 Throttle, CH4 Yaw, CH5 Arm

Run:  python3 ground_station.py
Quit: close the window. The script sends a final disarmed/throttle-low
      packet before disconnect.
"""

import sys
import glob
import serial
import tkinter as tk

# --- CONFIGURATION ---
DEFAULT_PORT = "/dev/ttyACM0"
BAUD_RATE    = 115200
TX_HZ        = 50

# Arm channel values (Betaflight default-friendly).
# Most Betaflight configs treat CH5 > 1700us as armed, < 1300us as disarmed.
ARM_HIGH_US     = 2000
ARM_LOW_US      = 1000

def autodetect_port():
    # Prefer Teensy 4.1, then KB2040, then any ACM device.
    for pattern in ("/dev/serial/by-id/usb-Teensyduino*if00",
                    "/dev/serial/by-id/usb-Adafruit_KB2040*if00"):
        for p in sorted(glob.glob(pattern)):
            return p
    for p in sorted(glob.glob("/dev/ttyACM*")):
        return p
    return DEFAULT_PORT

port = sys.argv[1] if len(sys.argv) > 1 else autodetect_port()

try:
    kb2040 = serial.Serial(port, BAUD_RATE, timeout=0.1)
    print(f"Connected to KB2040 on {port}")
except Exception as e:
    print(f"Failed to open {port}: {e}\n"
          f"Pass the correct port: python3 ground_station.py /dev/ttyACMx")
    sys.exit(1)

# --- GUI ---
root = tk.Tk()
root.title("Nomad Digital Command Center")
root.geometry("440x460")
root.configure(padx=20, pady=20)

armed_var = tk.BooleanVar(value=False)

def center_sticks():
    roll_slider.set(1500)
    pitch_slider.set(1500)
    yaw_slider.set(1500)
    # Throttle deliberately not centred -- stays where pilot left it.

def kill_throttle():
    throttle_slider.set(1000)

def disarm():
    armed_var.set(False)
    kill_throttle()

# ---- Arm toggle (top, big, visible) ----
arm_frame = tk.Frame(root)
arm_frame.pack(pady=(0, 8))
arm_label = tk.Label(arm_frame, text="DISARMED", font=("Arial", 14, "bold"),
                    fg="white", bg="darkred", width=20, height=2)
arm_label.pack(side="left", padx=(0, 10))

def toggle_arm():
    new_state = not armed_var.get()
    armed_var.set(new_state)
    if new_state:
        arm_label.config(text="ARMED", bg="darkgreen")
    else:
        arm_label.config(text="DISARMED", bg="darkred")
        kill_throttle()  # safety: disarming also cuts throttle

tk.Button(arm_frame, text="ARM / DISARM", command=toggle_arm,
          width=15, height=2).pack(side="left")

# ---- Channel sliders ----
tk.Label(root, text="Throttle (CH3)", font=("Arial", 10, "bold")).pack()
throttle_slider = tk.Scale(root, from_=1000, to=2000, orient="horizontal",
                           length=340, tickinterval=500)
throttle_slider.set(1000)
throttle_slider.pack()

tk.Label(root, text="Yaw (CH4)", font=("Arial", 10)).pack()
yaw_slider = tk.Scale(root, from_=1000, to=2000, orient="horizontal", length=340)
yaw_slider.set(1500)
yaw_slider.pack()

tk.Label(root, text="Pitch (CH2)", font=("Arial", 10)).pack()
pitch_slider = tk.Scale(root, from_=1000, to=2000, orient="horizontal", length=340)
pitch_slider.set(1500)
pitch_slider.pack()

tk.Label(root, text="Roll (CH1)", font=("Arial", 10)).pack()
roll_slider = tk.Scale(root, from_=1000, to=2000, orient="horizontal", length=340)
roll_slider.set(1500)
roll_slider.pack()

btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)
tk.Button(btn_frame, text="CENTER STICKS", command=center_sticks,
          bg="orange",          width=14).pack(side="left",  padx=8)
tk.Button(btn_frame, text="KILL THROTTLE", command=kill_throttle,
          bg="red", fg="white", width=14).pack(side="left",  padx=8)
tk.Button(btn_frame, text="DISARM",        command=disarm,
          bg="black", fg="white", width=10).pack(side="left", padx=8)

# --- Transmit loop ---
PERIOD_MS = max(1, int(1000 / TX_HZ))

def send_telemetry():
    r = roll_slider.get()
    p = pitch_slider.get()
    t = throttle_slider.get()
    y = yaw_slider.get()
    # Drive BOTH AUX1 (CH5) and AUX2 (CH6) high when armed.
    # The drone's arm config uses either AUX1 or AUX2 in the 1075-2100us
    # window; setting both covers single- and dual-AUX configurations.
    arm = ARM_HIGH_US if armed_var.get() else ARM_LOW_US
    cmd = f"{r},{p},{t},{y},{arm},{arm}\n"
    try:
        kb2040.write(cmd.encode("utf-8"))
    except Exception as e:
        print(f"Serial write error: {e}")
    root.after(PERIOD_MS, send_telemetry)

root.after(PERIOD_MS, send_telemetry)
root.mainloop()

# --- Shutdown -> safe values, then close ---
print("Shutting down link...")
try:
    kb2040.write(f"1500,1500,1000,1500,{ARM_LOW_US},{ARM_LOW_US}\n".encode())
finally:
    kb2040.close()
