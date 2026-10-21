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
fixed=[f for r,f in fps.items() if r in ['U10','J1','J2','H1','H2','H3','C30','C32']]
movable=[f for r,f in fps.items() if f not in fixed]
for f in fps.values():
    f.Reference().SetTextSize(pt(.8,.8)); f.Reference().SetTextThickness(p.FromMM(.12))
    # Reference artwork will be placed after the complete board is routed.
    f.Reference().SetVisible(False)
for ref in ('R31','R32'):
    if ref not in fps: continue
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

def opposite_holes_clear(f,placed):
    # A through-hole pad must also clear the opposite-side body courtyard.
    for pad in f.Pads():
        if pad.GetAttribute()!=p.PAD_ATTRIB_PTH:continue
        if any(other.GetLayer()!=f.GetLayer() and overlap(box(pad),box(other)) for other in placed):return False
    return True

critical=['U60','U61','L2','C284','U70','Q70','R270','C280','C281','C282','C283','C274','C275','R271','R272','C277','R275','C278','C276',
          'U6','L1','C11','C12','C13','C14','C15','C16','C10','R10','R11',
          'U30','C61','C60','R61','Q30','SW1','SW2',
          'U7','C6','C8','U5','C7','U3','C4','D4','D5','U2','C2','C3']
order={ref:i for i,ref in enumerate(critical)}
movable.sort(key=lambda f:(order.get(f.GetReference(),100),-((box(f)[2]-box(f)[0])*(box(f)[3]-box(f)[1]))))
placed=list(fixed); result=[]
for f in movable:
    ref=f.GetReference(); desired=f.GetPosition(); dx=p.ToMM(desired.x); dy=p.ToMM(desired.y)
    obs=obstacles(f,placed)
    offsets=sorted([(ix*.5,iy*.5) for ix in range(-24,25) for iy in range(-24,25)],key=lambda xy:xy[0]**2+xy[1]**2)
    found=None
    for ox,oy in offsets:
        f.SetPosition(pt(dx+ox,dy+oy)); bounds=box(f)
        if in_ring(bounds) and not any(overlap(bounds,o) for o in obs) and opposite_holes_clear(f,placed):
            found=(dx+ox,dy+oy); break
    if found is None:
        # Broaden only when the block-local search cannot fit a component.
        candidates=[]
        for rr in (30,32,34,36,38,40):
            for deg in range(0,360,2):
                xx=100+rr*math.cos(math.radians(deg)); yy=100+rr*math.sin(math.radians(deg))
                candidates.append(((xx-dx)**2+(yy-dy)**2,xx,yy))
        for _,xx,yy in sorted(candidates):
            f.SetPosition(pt(xx,yy)); bounds=box(f)
            if in_ring(bounds) and not any(overlap(bounds,o) for o in obs) and opposite_holes_clear(f,placed):
                found=(xx,yy);break
    if found is None: raise RuntimeError(f'No conservative placement found for {ref}; revise floorplan.')
    placed.append(f); result.append({'reference':ref,'x':found[0],'y':found[1],'side':'F' if f.GetLayer()==p.F_Cu else 'B'})
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
(ROOT/'analysis'/'core_placement.json').write_text(json.dumps(result,indent=2))
print(f'Placed {len(movable)} core footprints with conservative edge/collision screening')
