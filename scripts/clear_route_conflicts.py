"""Remove conflicting unprotected routes after reviewed locked fan-out edits.

No rule changes or suppressions. Removed branches must be reconnected by routing.
"""
from pathlib import Path
import pcbnew as p
from shapely.geometry import LineString,Point
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'))
def shape(t):
    if isinstance(t,p.PCB_VIA):return Point(p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2)
    return LineString([(p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)),(p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y))]).buffer(p.ToMM(t.GetWidth())/2)
locked=[(t,shape(t)) for t in b.GetTracks() if t.IsLocked()]
removed=[]
for t in list(b.GetTracks()):
    if t.IsLocked():continue
    geom=shape(t)
    forced=t.GetNetname() in ('/GND','/BOOST_BST','/LOGIC_FB')
    edge=geom.distance(Point(100,100))<28.005 or not Point(100,100).buffer(41.495,resolution=256).contains(geom)
    conflict=any(t.GetNetname()!=a.GetNetname() and (isinstance(t,p.PCB_VIA) or isinstance(a,p.PCB_VIA) or t.GetLayer()==a.GetLayer()) and geom.distance(ag)<.20001 for a,ag in locked)
    if forced or edge or conflict:removed.append(t.GetNetname());b.DeleteNative(t)
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
from collections import Counter
print('Removed unprotected branches; reroute required:',dict(Counter(removed)))
