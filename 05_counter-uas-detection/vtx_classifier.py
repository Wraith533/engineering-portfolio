#!/usr/bin/env python3
"""HackRF VTX hunter: find 5 GHz emitters, then park on each and classify
VTX (continuous video carrier) vs Wi-Fi router (bursty) by duty cycle +
power steadiness. Sweeps to 5950 MHz to catch analog/raceband FPV.
"""
import subprocess, statistics, time

def sweep(fmin, fmax, secs, binhz=1_000_000):
    out = subprocess.run(["sudo","timeout",str(secs),"hackrf_sweep","-f",
        f"{fmin}:{fmax}","-w",str(binhz),"-l","32","-g","20"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
    peak={}
    for line in out.splitlines():
        f=line.split(", ")
        if len(f)<7: continue
        try: low=int(f[2]); bw=float(f[4]); vals=[float(x) for x in f[6:]]
        except ValueError: continue
        for i,v in enumerate(vals):
            mhz=round((low+(i+0.5)*bw)/1e6); peak[mhz]=max(peak.get(mhz,-200),v)
    return peak

def park_duty(fc, secs=3):
    """Park on fc; return (duty%, power_std, peak) over the window."""
    out = subprocess.run(["sudo","timeout",str(secs),"hackrf_sweep","-f",
        f"{fc-10}:{fc+10}","-w","200000","-l","32","-g","20"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True).stdout
    samp=[]
    for line in out.splitlines():
        f=line.split(", ")
        if len(f)<7: continue
        try: low=int(f[2]); bw=float(f[4]); vals=[float(x) for x in f[6:]]
        except ValueError: continue
        best=max((v for i,v in enumerate(vals) if abs((low+(i+0.5)*bw)/1e6-fc)<3),default=None)
        if best is not None: samp.append(best)
    if len(samp)<10: return None
    floor=sorted(samp)[len(samp)//10]            # 10th pctile ~ off-air level
    thr=floor+6
    duty=100.0*sum(1 for v in samp if v>thr)/len(samp)
    return duty, statistics.pstdev(samp), max(samp), floor

if __name__ == "__main__":
    print("Sweeping 5150-5950 MHz (incl. analog/raceband FPV)...")
    pk = sweep(5150, 5950, 8)
    floor = sorted(pk.values())[len(pk)//5]
    # find emitter centers: local maxima >= floor+10, dedup within 15 MHz
    cands=[]
    for m in sorted(pk):
        if pk[m] >= floor+10:
            if not cands or m-cands[-1][0] > 15: cands.append([m,pk[m]])
            elif pk[m]>cands[-1][1]: cands[-1]=[m,pk[m]]
    print(f"noise floor ~{floor:.0f} dB; {len(cands)} emitter(s) found\n")
    print(f"{'MHz':>5} {'peak':>6} {'duty%':>6} {'steady':>7}  classification")
    for fc,_ in cands:
        r=park_duty(fc)
        if not r: continue
        duty,std,mx,fl = r
        # VTX: high duty (continuous) AND steady (low std). Router: bursty.
        if duty>70 and std<6:   cls="VTX-like (continuous video carrier)"
        elif duty>70:           cls="continuous but noisy (digital VTX or saturated AP)"
        elif duty>15:           cls="Wi-Fi router (bursty traffic)"
        else:                   cls="idle AP / beacons only"
        print(f"{fc:>5} {mx:6.1f} {duty:6.1f} {std:7.1f}  {cls}")
