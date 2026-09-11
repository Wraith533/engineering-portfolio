#!/usr/bin/env python3
"""
Motor-spin smoke test for the Bandit USB-CRSF path.
Opens /dev/ttyUSB0 at 420000 baud, streams CRSF RC_CHANNELS_PACKED at 250 Hz.

Channels:
   CH1/CH2/CH4 = 1500   (roll/pitch/yaw centred)
   CH3         = 1100   (throttle just above min_check, motors idle)
   CH5 = CH6   = 2000   (arm AUX1+AUX2)
   CH7..CH16   = 1500

Runs for SPIN_SECONDS, then sends 8 seconds of disarmed/throttle-low frames
to ensure the FC sees a clean disarm before exit.

PROPS OFF. PROPS OFF. PROPS OFF.
"""
import serial, struct, time, sys

PORT          = "/dev/ttyUSB0"
BAUD          = 420000
FRAME_HZ      = 250
SPIN_SECONDS  = 8

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
    acc = 0
    bits = 0
    idx = 0
    for ch in channels_us:
        v = us_to_crsf(ch) & 0x07FF
        acc |= v << bits
        bits += 11
        while bits >= 8:
            payload[idx] = acc & 0xFF
            acc >>= 8
            bits -= 8
            idx += 1
    body = bytes([CRSF_FRAMETYPE_RC]) + bytes(payload)
    return bytes([CRSF_ADDR_FC, CRSF_FRAME_LEN]) + body + bytes([crc8(body)])

def stream(s, channels_us, seconds):
    period = 1.0 / FRAME_HZ
    deadline = time.time() + seconds
    next_tx  = time.time()
    frame    = build_frame(channels_us)
    while time.time() < deadline:
        s.write(frame)
        next_tx += period
        slack = next_tx - time.time()
        if slack > 0: time.sleep(slack)

def main():
    s = serial.Serial(PORT, BAUD, timeout=0.1)
    print(f"opened {PORT} @ {BAUD}")

    armed   = [1500, 1500, 1100, 1500, 2000, 2000] + [1500]*10
    disarm  = [1500, 1500, 1000, 1500, 1000, 1000] + [1500]*10

    # Warm up with disarmed frames so the FC sees a clean low-throttle/disarmed
    # state before we go armed.
    print("[disarmed warm-up: 1.5s]")
    stream(s, disarm, 1.5)

    print(f"[ARMED, throttle 1100, {SPIN_SECONDS}s] -- watch the motors")
    try:
        stream(s, armed, SPIN_SECONDS)
    except KeyboardInterrupt:
        print("\n^C -- early exit")

    print("[disarmed cool-down: 2s]")
    stream(s, disarm, 2.0)
    s.close()
    print("done.")

if __name__ == "__main__":
    main()
