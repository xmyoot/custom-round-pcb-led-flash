"""Move the disconnect FET away from analog escape vias; deliberate power fan-out.

Use once on the first routed candidate. Native DRC must follow. Component moves
preserve the one authoritative schematic/PCB and all electrical net assignments.
"""
from pathlib import Path
import pcbnew as p
from shapely.geometry import LineString,Point,box
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
def pt(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
for t in list(b.GetTracks()):
    if t.GetNetname() in ('/BOOST_INPUT_GATE','/BOOST_SENSE','/BOOST_INPUT','/CAP_FUSED'):b.DeleteNative(t)
fps['Q70'].SetPosition(pt(132,86))
fps['R270'].SetPosition(pt(137,86));fps['R270'].SetOrientationDegrees(90)
fps['C284'].SetPosition(pt(134.4,95.5));fps['C284'].SetOrientationDegrees(0)
def bbox(a):
    r=a.GetBoundingBox();return box(*[p.ToMM(v) for v in (r.GetLeft(),r.GetTop(),r.GetRight(),r.GetBottom())])
# Moving SMT pads can invalidate previously routed local copper. Remove only
# affected unlocked items; preserved/locked copper must pass DRC unchanged.
removed=[]
for t in list(b.GetTracks()):
    if isinstance(t,p.PCB_VIA):shape=Point(p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2+.2)
    else:shape=LineString([(p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y))]).buffer(p.ToMM(t.GetWidth())/2+.2)
    if any(t.GetNetname()!=a.GetNetname() and (isinstance(t,p.PCB_VIA) or a.IsOnLayer(t.GetLayer())) and shape.intersects(bbox(a)) for ref in ('Q70','R270','C284') for a in fps[ref].Pads()):
        if t.IsLocked():raise RuntimeError('Moved component conflicts with locked '+t.GetNetname())
        removed.append(t.GetNetname());b.DeleteNative(t)
def trace(net,coords,width=.2,layer=p.F_Cu):
    for a,c in zip(coords,coords[1:]):
        t=p.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*c));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet('/'+net));t.SetLocked(True);b.Add(t)
def via(net,x,y):
    v=p.PCB_VIA(b);v.SetPosition(pt(x,y));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('/'+net));v.SetLocked(True);b.Add(v)
# Gate and Kelvin sense escape into clear through-via sites above the FET pad.
trace('BOOST_INPUT_GATE',[(132.4,83.25),(133.0,83.25),(133.2,83.45)],.15)
via('BOOST_INPUT_GATE',133.2,83.45)
trace('BOOST_INPUT_GATE',[(133.2,83.45),(132.6,82.85),(130.575,82.85),(129.33,84.095)],.2,p.B_Cu)
trace('BOOST_SENSE',[(132.4,82.75),(132.95,82.75),(133.3,82.4)],.15)
via('BOOST_SENSE',133.3,82.4)
trace('BOOST_SENSE',[(133.3,82.4),(137,82.4),(137,85.0875)],.2,p.B_Cu)
# High-current shunt-to-disconnect branch and joined source fingers.
trace('BOOST_SENSE',[(137,85.0875),(135.0725,85.0875),(134.795,85.365)],.8,p.B_Cu)
trace('BOOST_INPUT',[(129.33,85.365),(129.33,87.905),(129.33,89)],.6,p.B_Cu)
trace('BOOST_INPUT',[(129.33,89),(130.13,89.8)],.8,p.B_Cu)
via('BOOST_INPUT',129.33,89);via('BOOST_INPUT',130.13,89.8)
trace('BOOST_INPUT',[(129.33,89),(129.33,91.5),(132.19,94.36),(134,94.36)],1.2)
trace('BOOST_INPUT',[(130.13,89.8),(130.13,92.3)],.8)
# Short output collector; separate feedback/logic branches may be thinner.
trace('BOOST_OUT',[(132.4,85.75),(132.4,86.25),(133.2,86.25)],.25)
trace('BOOST_OUT',[(133.2,86.25),(133.425,86.475),(135,86.475)],.8)
trace('BOOST_OUT',[(132.4,84.25),(133.3,84.25),(133.3,85.5),(134.275,86.475)],.2)
# Ground land15 can return directly to the nearby input ceramic ground.
trace('GND',[(71.275,76.6),(71.275,75.6),(70.95,75.275),(70.95,74.5)],.15)
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
print('Refined boost power placement; removed local conflicting copper',removed)
