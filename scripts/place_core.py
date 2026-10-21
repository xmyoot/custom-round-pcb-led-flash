"""Conservative placement refinement for the unrouted core, with ring checks.

Bounding boxes are used only for placement screening. Native DRC remains the
authority for actual pad, hole, mask and courtyard geometry.
"""
from pathlib import Path
import json, math, pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'))
if list(b.GetTracks()): raise RuntimeError('Placement refinement is only for the unrouted stage.')
def pt(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def box(item):
    r=item.GetBoundingBox(False,False) if isinstance(item,p.FOOTPRINT) else item.GetBoundingBox()
    return tuple(p.ToMM(v) for v in (r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom()))
def overlap(a,c,gap=.15): return a[0]<c[2]+gap and a[2]>c[0]-gap and a[1]<c[3]+gap and a[3]>c[1]-gap
def in_ring(a):
    nearx=max(a[0],min(100,a[2])); neary=max(a[1],min(100,a[3]))
    rmin=math.hypot(nearx-100,neary-100)
    rmax=max(math.hypot(x-100,y-100) for x in (a[0],a[2]) for y in (a[1],a[3]))
    return rmin>=28.05 and rmax<=41.4 and not overlap(a,(76,38,124,59.5),0)
fps={f.GetReference():f for f in b.GetFootprints()}
fixed=[f for r,f in fps.items() if r in ['U10','J1','J2','H1','H2','H3','C30','C31','C32','C33']]
movable=[f for r,f in fps.items() if f not in fixed]
for f in fps.values():
    f.Reference().SetTextSize(pt(.8,.8)); f.Reference().SetTextThickness(p.FromMM(.12))
    # Reference artwork will be placed after the complete board is routed.
    f.Reference().SetVisible(False)
for ref in ('R31','R32'):
    f=fps[ref]
    if f.GetLayer()==p.F_Cu: f.Flip(f.GetPosition(),False)

def obstacles(f, placed):
    items=[]
    for other in placed:
        if other.GetLayer()==f.GetLayer(): items.append(box(other))
        else:
            for pad in other.Pads():
                if pad.GetAttribute() in (p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH): items.append(box(pad))
    return items

order={'U6':0,'L1':1,'SW1':2,'SW2':3,'C11':4,'C14':5,'C10':6}
movable.sort(key=lambda f:(order.get(f.GetReference(),10),-((box(f)[2]-box(f)[0])*(box(f)[3]-box(f)[1]))))
placed=list(fixed); result=[]
for f in movable:
    ref=f.GetReference(); desired=f.GetPosition(); dx=p.ToMM(desired.x); dy=p.ToMM(desired.y)
    obs=obstacles(f,placed)
    offsets=sorted([(ix*.5,iy*.5) for ix in range(-24,25) for iy in range(-24,25)],key=lambda xy:xy[0]**2+xy[1]**2)
    found=None
    for ox,oy in offsets:
        f.SetPosition(pt(dx+ox,dy+oy)); bounds=box(f)
        if in_ring(bounds) and not any(overlap(bounds,o) for o in obs):
            found=(dx+ox,dy+oy); break
    if found is None: raise RuntimeError(f'No conservative placement found for {ref}; revise floorplan.')
    placed.append(f); result.append({'reference':ref,'x':found[0],'y':found[1],'side':'F' if f.GetLayer()==p.F_Cu else 'B'})
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
(ROOT/'analysis'/'core_placement.json').write_text(json.dumps(result,indent=2))
print(f'Placed {len(movable)} core footprints with conservative edge/collision screening')
