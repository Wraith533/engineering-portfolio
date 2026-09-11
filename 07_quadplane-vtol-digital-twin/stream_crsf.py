#!/usr/bin/env python3
"""
Continuous CRSF streamer for diagnostic / BF Receiver-tab observation.

Streams 250 Hz CRSF RC_CHANNELS_PACKED at 420000 baud out of /dev/ttyUSB0.
Reads "r,p,t,y,arm,arm\n" lines on stdin while running -- if a complete line
arrives, channel values update.  Default values are armed + throttle low so
the user can immediately see CH5/CH6 hit ~2000 us in BF.

Type 'q' + Enter to quit, or Ctrl+C.
"""
import serial, sys, threading, time, select

PORT     = "/dev/ttyUSB0"
BAUD     = 420000
FRAME_HZ = 250

CRSF_ADDR_FC      = 0xC8
CRSF_FRAMETYPE_RC = 0x16
CRSF_FRAME_LEN    = 24

def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0xD5) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc

def us_to_crsf(us):
    v = (us - 1500) * 8 // 5 + 992
    return max(0, min(2047, v))

def build_frame(channels_us):
    payload = bytearray(22)
    acc, bits, idx = 0, 0, 0
    for ch in channels_us:
        v = us_to_crsf(ch) & 0x07FF
        acc |= v << bits
        bits += 11
        while bits >= 8:
            payload[idx] = acc & 0xFF
            acc >>= 8; bits -= 8; idx += 1
    body = bytes([CRSF_FRAMETYPE_RC]) + bytes(payload)
    return bytes([CRSF_ADDR_FC, CRSF_FRAME_LEN]) + body + bytes([crc8(body)])

# Default channels: armed, throttle low.  Visible in BF: AUX1+AUX2 ~2000us,
# CH3 throttle ~1000us, sticks centred.
channels = [1500, 1500, 1000, 1500, 2000, 2000] + [1500]*10

def main():
    s = serial.Serial(PORT, BAUD, timeout=0.1)
    print(f"streaming CRSF on {PORT} @ {BAUD} baud, 250 Hz")
    print("default channels: CH1=1500 CH2=1500 CH3=1000 CH4=1500 CH5=2000 CH6=2000")
    print("type 'arm', 'disarm', 'tXXXX' (set throttle), or 'q' + Enter")
    period = 1.0 / FRAME_HZ
    next_tx = time.time()
    try:
        while True:
            # Allow stdin to inject commands without blocking the TX loop
            if select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline().strip().lower()
                if line == "q":
                    break
                elif line == "arm":
                    channels[4] = 2000; channels[5] = 2000
                    print("  -> armed (CH5=CH6=2000)")
                elif line == "disarm":
                    channels[4] = 1000; channels[5] = 1000
                    channels[2] = 1000  # also kill throttle
                    print("  -> disarmed (CH5=CH6=1000)")
                elif line.startswith("t") and line[1:].isdigit():
                    val = max(1000, min(2000, int(line[1:])))
                    channels[2] = val
                    print(f"  -> throttle = {val}")

            s.write(build_frame(channels))
            next_tx += period
            slack = next_tx - time.time()
            if slack > 0:
                time.sleep(slack)
            elif slack < -0.05:  # fell badly behind
                next_tx = time.time()
    except KeyboardInterrupt:
        print("\n^C")
    finally:
        # Send disarmed cool-down before close
        cool = [1500, 1500, 1000, 1500, 1000, 1000] + [1500]*10
        for _ in range(int(FRAME_HZ * 1.0)):
            s.write(build_frame(cool))
            time.sleep(period)
        s.close()
        print("port closed; final frames were disarmed.")

if __name__ == "__main__":
    main()
