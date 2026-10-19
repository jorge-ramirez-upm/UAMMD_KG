"""Exact multi-tau capacity arithmetic for the Stage 4A.3c every-step clock."""
import argparse
import math

DT = 0.000025
CHAINS = 2048
POINTER = 8
OWNING = 296  # Accepted Linux64 accounting recorded by the frozen validation plan.

def bank_bytes(slots, levels, chains=CHAINS):
    per_chain = OWNING + levels*(slots*(21*8 + 2*8) + 12*POINTER + POINTER + 6*8 + 2*4) + POINTER
    return per_chain*chains

def hierarchy(slots, levels, frames, dt=DT):
    rows=[]
    # Exported finest bins are direct frame bins; coarse levels begin at level 1.
    for level in range(levels):
        width = 2**level
        blocks = frames//width
        low, high = (0, min(slots-1, blocks-1)) if level == 0 else (slots//2, min(slots-1, blocks-1))
        if high < low: continue
        # A lag offset consumes that many complete block origins.
        supported = min(high, blocks-16)
        rows.append(dict(level=level, block_samples=width, block_time=width*dt,
                         nominal_lag_samples=high*width, nominal_lag_time=high*width*dt,
                         supported_lag_samples=(supported*width if supported >= low else None),
                         supported_lag_time=(supported*width*dt if supported >= low else None),
                         nominal_origins=(blocks-high),
                         supported_origins=(blocks-supported if supported >= low else 0),
                         bins=(high-low+1)))
    return rows

def maximum(rows, key):
    values=[r[key] for r in rows if r[key] is not None]
    return max(values) if values else None

def bins_through(rows, lag_time):
    """Exported bins at/below a target; origins remain correlated, never iid."""
    total=0
    for row in rows:
        high=min(row['nominal_lag_samples']//row['block_samples'], int(lag_time/(row['block_samples']*DT)))
        low=0 if row['level']==0 else row['nominal_lag_samples']//row['block_samples']-((row['nominal_lag_samples']//row['block_samples'])-(row['bins'])+1)
        total += max(0, high-low+1)
    return total

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=int, default=8_000_001)
    parser.add_argument('--slots', type=int, default=64)
    parser.add_argument('--levels', type=int, default=21)
    args=parser.parse_args()
    if args.frames < 1 or args.slots < 2 or args.levels < 1: raise SystemExit('positive frames/slots/levels required')
    rows=hierarchy(args.slots,args.levels,args.frames)
    print('slots,levels,frames,bank_mib,nominal_max_time,supported_max_time')
    print(f'{args.slots},{args.levels},{args.frames},{bank_bytes(args.slots,args.levels)/2**20:.6f},'
          f'{maximum(rows,"nominal_lag_time"):.9g},{maximum(rows,"supported_lag_time"):.9g}')
    print('level,block_time,nominal_lag_time,supported_lag_time,nominal_origins,supported_origins,bins')
    for r in rows:
        print(f'{r["level"]},{r["block_time"]:.9g},{r["nominal_lag_time"]:.9g},'
              f'{"" if r["supported_lag_time"] is None else format(r["supported_lag_time"],".9g")},{r["nominal_origins"]},{r["supported_origins"]},{r["bins"]}')

if __name__ == '__main__': main()
