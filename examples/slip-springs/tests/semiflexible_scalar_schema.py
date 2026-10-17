"""Scalar-output V1 serialization/coverage checks; no scientific gate changes."""
import struct
from pathlib import Path

SCHEMA='scalar-output-v1'
SCHEMA_HASH='78d112f65ed47083976fd692edf959a051bd5b3a85f80dae87fdfc1c7c10deaa'
INITIAL=14695981039346656037
MASK=(1<<64)-1
# Filled from the reviewed host-only driver and compact writer, never a kernel.
DRIVER_HASH='6cec3b3effccabf8d5f48bc217b0180d6c46c60344b48951f99bc75afeb18740'
WRITER_HASH='c14dc97d19727069195ef3154ad22805b66708e0da50bf2bca6682f9aa0c6ba5'


def mix(h,word):return (h*1099511628211+word+1)&MASK

def bits(value):return struct.unpack('<Q',struct.pack('<d',float(value)))[0]

def hexdigest(h):return f'{h:016x}'

def selected_steps(steps,stride):
    return sorted({j*steps//4 for j in range(5) if j*steps%4==0 and (j*steps//4)%stride==0})

def schedule_hash(steps,stride):
    h=INITIAL
    for step in range(0,steps+1,stride):h=mix(h,step)
    return hexdigest(h)


def current_sources(legacy):
    return {**legacy,'semiflexible.cu':DRIVER_HASH,'semiflexible_scalar_output.h':WRITER_HASH}


def validate(out,opts,meta):
    import semiflexible_stress_analysis as a
    c,n,steps,stride=[int(opts[k]) for k in ('chains','springs','steps','sample')]
    frames=steps//stride+1;half=frames-(steps//2+stride-1)//stride;selected=selected_steps(steps,stride)
    a.require(not (out/'samples.csv').exists(),'compact profile contains legacy samples.csv')
    a.require(opts['stress-mode']=='stream','compact profile requires stress streaming')
    a.require(a.digest(a.PROJECT/'STAGE4A3C_OUTPUT_SCHEMA_V1.md')==SCHEMA_HASH,'local scalar schema hash mismatch')
    m=a.load(out/'scalar_metadata.json');expected=dict(profile='compact',schema=SCHEMA,schema_sha256=SCHEMA_HASH,
        chains=c,springs=n,steps=steps,stride=stride,dt=float(opts['dt']),frames=frames,finite_rows=frames*c,
        final_half_start_step=steps//2,final_half_frames=half,selected_steps=selected,serialized_rows=len(selected)*c,
        schedule_hash=schedule_hash(steps,stride),gpu_bytes=0)
    a.require(set(m)==set(expected)|{'minimum_sampled_bond','host_bytes','statistics_hash','selected_hash'},'compact metadata schema fields mismatch')
    for k,v in expected.items():a.require(m[k]==v,'compact metadata mismatch: '+k)
    a.require(88*c+8*len(selected)<=m['host_bytes']<=88*c+64,'compact host allocation inconsistent')
    a.require(half>=2,'insufficient final-half scalar support')
    tangent_names=tuple('mean_tangent'+str(i) for i in range(1,min(4,n-1)+1))
    means=('mean_re2','mean_rg2')+tangent_names
    fixed=('chain','frames','finite_rows','final_half_frames','first_step','last_step','schedule_hash','min_length')
    columns=fixed+means+('record_hash',);count=0;minimum=float('inf');hash_=INITIAL;chain_min=[];stats=[]
    for count,row in enumerate(a.rows(out/'scalar_statistics.csv',columns),1):
        a.require(count<=c and a.number(row,'chain',True)==count-1,'missing/duplicate/reordered compact chain record')
        for k,v in dict(frames=frames,finite_rows=frames,final_half_frames=half,first_step=0,last_step=(frames-1)*stride).items():
            a.require(a.number(row,k,True)==v,'compact chain coverage mismatch: '+k)
        a.require(row['schedule_hash']==expected['schedule_hash'],'compact chain schedule hash mismatch')
        value=a.number(row,'min_length');a.require(value>0,'collapsed observed bond in frozen campaign')
        chain_min.append(value);minimum=min(minimum,value)
        values=[a.number(row,k) for k in means];stats.append(values)
        words=[a.number(row,k,True) for k in fixed[:6]]+[int(row['schedule_hash'],16),bits(value)]+[bits(v) for v in values]
        h=INITIAL
        for word in words:h=mix(h,word)
        a.require(row['record_hash']==hexdigest(h),'compact record checksum mismatch')
        hash_=mix(hash_,h)
    a.require(count==c,'missing compact chain records')
    a.require(m['statistics_hash']==hexdigest(hash_),'compact statistics checksum mismatch')
    a.close(m['minimum_sampled_bond'],minimum,why='compact global minimum mismatch')
    a.close(meta['minimum_sampled_bond'],minimum,rtol=1e-14,why='compact/legacy metadata minimum mismatch')
    columns=('step','time','chain','mean_r','mean_r2','re2','rg2','cm_msd','monomer_msd','min_length')+tuple('tangent'+str(i) for i in range(1,min(4,n-1)+1))
    count=0;h=INITIAL
    for count,row in enumerate(a.rows(out/'scalar_selected.csv',columns),1):
        frame,chain=divmod(count-1,c)
        a.require(frame<len(selected) and a.number(row,'step',True)==selected[frame] and a.number(row,'chain',True)==chain,'missing/duplicate/reordered selected scalar frame')
        a.close(a.number(row,'time'),selected[frame]*float(opts['dt']),rtol=1e-14,why='selected scalar time mismatch')
        minimum_at_time=a.number(row,'min_length')
        a.require(minimum_at_time>0 and minimum_at_time>=chain_min[chain],'selected minimum inconsistent with all-frame minimum')
        for key in columns:
            v=a.number(row,key,key in ('step','chain'));h=mix(h,v if key in ('step','chain') else bits(v))
    a.require(count==len(selected)*c,'missing selected scalar frames')
    a.require(m['selected_hash']==hexdigest(h),'selected scalar checksum mismatch')
    return dict(metadata=m,columns=means,per_chain_means=stats)
