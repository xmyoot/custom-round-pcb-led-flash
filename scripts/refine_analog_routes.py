"""Reviewed analog fan-out: escape away from the switching rail, then route."""
from pathlib import Path
import pcbnew as p,math
from shapely.geometry import box,Point,LineString
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for t in list(b.GetTracks()):
    if t.GetNetname() in ('/BOOST_FB','/BOOST_VDD','/BOOST_COMP','/BOOST_SS'):b.DeleteNative(t)
fps['C275'].SetPosition(pt(129.5,79));fps['C275'].SetOrientationDegrees(0)
def bounds(item):
    r=item.GetBoundingBox(False,False) if isinstance(item,p.FOOTPRINT) else item.GetBoundingBox()
    return box(*[p.ToMM(v) for v in (r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom())])
f=fps['C278']
for dist,x,y in sorted((i*i+j*j,128+i*.25,78+j*.25) for i in range(-20,21) for j in range(-20,21)):
    f.SetPosition(pt(x,y));bb=bounds(f)
    if not any(bb.buffer(.15).intersects(bounds(o)) for o in fps.values() if o!=f and o.GetLayer()==f.GetLayer()):break
else:raise RuntimeError('No local C278 site')
fps['R272'].SetOrientationDegrees(270)
def trace(net,coords,layer=p.F_Cu,width=.15):
    for a,c in zip(coords,coords[1:]):
        t=p.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*c));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet('/'+net));t.SetLocked(True);b.Add(t)
def via(net,x,y):
    v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('/'+net));v.SetLocked(True);b.Add(v)
trace('BOOST_VDD',[(129.6,83.25),(128.9,83.25),(128.4,82.75),(128.4,79.15),(128.55,79)])
trace('BOOST_COMP',[(129.6,83.75),(128,83.75)])
via('BOOST_COMP',128,83.75)
origin=(125.225,80)
for dist,x,y in sorted((i*i+j*j,origin[0]+i*.1,origin[1]+j*.1) for i in range(-30,31) for j in range(-30,31)):
    site=Point(x,y).buffer(.5)
    if any(site.intersects(bounds(a)) for f in fps.values() for a in f.Pads()):continue
    line=LineString([origin,(x,y)]).buffer(.275)
    if any(line.intersects(bounds(a)) for f in fps.values() if f.GetLayer()==p.F_Cu for a in f.Pads() if a.GetNetname()!='/BOOST_COMP'):continue
    if any(line.intersects(LineString([(p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y))]).buffer(p.ToMM(t.GetWidth())/2)) for t in b.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetLayer()==p.F_Cu and t.GetNetname()!='/BOOST_COMP'):continue
    target=(x,y);break
else:raise RuntimeError('No clear COMP via escape')
trace('BOOST_COMP',[(128,83.75),target],p.In2_Cu)
via('BOOST_COMP',*target)
trace('BOOST_COMP',[target,origin])
print('C278 site',p.ToMM(fps['C278'].GetPosition().x),p.ToMM(fps['C278'].GetPosition().y),'COMP via',target)
trace('BOOST_FB',[(129.6,84.25),(128.9,84.25),(127.475,85.675),(127,85.675)])
trace('BOOST_FB',[(128.9,84.25),(128.9,87.775),(127.5,89.175)])
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
print('Replaced boxed analog routes with explicit fan-out; native DRC required.')
