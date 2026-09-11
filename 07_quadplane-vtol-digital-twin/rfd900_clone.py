#!/usr/bin/env python3
"""Apply the settings dumped from the source RFD900x2 (rfd900_settings_dump.txt,
2026-08-10) to another RFD900 plugged into this machine.

Usage: python3 rfd900_clone.py [port]   (default /dev/ttyUSB0)

Tries each baud rate until the target answers, writes every S-register,
then AT&W (save to EEPROM) and ATZ (reboot). After reboot the radio will
be at 115200 baud like the source.
"""
import serial, sys, time

PORT = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB0"
BAUDS = [57600, 115200, 38400, 19200, 9600]

# Settings from the source radio. S0 (FORMAT) is read-only and skipped.
SETTINGS = {
    1: 115,      # SERIAL_SPEED
    2: 200,      # AIR_SPEED
    3: 107,      # NETID
    4: 30,       # TXPOWER
    5: 0,        # ECC
    6: 1,        # MAVLINK
    7: 0,        # OPPRESEND
    8: 915000,   # MIN_FREQ
    9: 928000,   # MAX_FREQ
    10: 51,      # NUM_CHANNELS
    11: 100,     # DUTY_CYCLE
    12: 0,       # LBT_RSSI
    13: 0,       # RTSCTS
    14: 120,     # MAX_WINDOW
    15: 0,       # ENCRYPTION_LEVEL
    16: 0,       # GPI1_1R/CIN
    17: 0,       # GPO1_1R/COUT
    18: 1,       # GPO1_1SBUSIN
    19: 0,       # GPO1_1SBUSOUT
    20: 0,       # ANT_MODE
    21: 0,       # GPO1_3STATLED
    22: 0,       # GPO1_0TXEN485
    23: 0,       # RATE/FREQBAND
    24: 0,       # GPI1_2AUXIN
    25: 0,       # GPO1_3AUXOUT
    26: 120,     # AIR_FRAMELEN
    27: 0,       # RSSI_IN_DBM
    28: 50,      # FSFRAMELOSS
    29: 57,      # AUXSER_SPEED
}

def read_all(ser, quiet=0.5, total=4.0):
    buf, deadline, last = b"", time.time() + total, time.time()
    while time.time() < deadline:
        chunk = ser.read(256)
        if chunk:
            buf += chunk
            last = time.time()
        elif time.time() - last > quiet:
            break
    return buf

def cmd(ser, c, total=4.0):
    ser.reset_input_buffer()
    ser.write(c.encode() + b"\r\n")
    ser.flush()
    return read_all(ser, total=total).decode(errors="replace")

def connect():
    for baud in BAUDS:
        ser = serial.Serial(PORT, baud, timeout=0.2)
        if "OK" in cmd(ser, "AT", total=1.5):
            return ser, baud
        ser.reset_input_buffer()
        time.sleep(1.2)
        ser.write(b"+++")
        ser.flush()
        time.sleep(1.2)
        if b"OK" in read_all(ser, total=2.5):
            return ser, baud
        ser.close()
        print(f"[{baud}] no response")
    sys.exit("Could not enter command mode at any baud rate")

ser, baud = connect()
print(f"Connected at {baud} baud: {cmd(ser, 'ATI', total=2).strip()}")

failed = []
for reg, val in SETTINGS.items():
    resp = cmd(ser, f"ATS{reg}={val}", total=2)
    ok = "OK" in resp
    print(f"  ATS{reg}={val}  ->  {'OK' if ok else resp.strip()}")
    if not ok:
        failed.append(reg)

if failed:
    sys.exit(f"Registers {failed} did not take — NOT saving. Fix and rerun.")

print("Saving to EEPROM (AT&W)...", cmd(ser, "AT&W", total=3).strip())
print("Rebooting radio (ATZ)...")
ser.write(b"ATZ\r\n")
ser.flush()
time.sleep(0.5)
ser.close()
print("Done. Radio is now at 115200 baud with the cloned settings.")
