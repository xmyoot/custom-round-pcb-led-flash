"""Create controlled converter rail bridges and the inner ground reference.

Run once after placement is approved; input copper is preserved by later routing.
No plated holes are placed inside component paste apertures.
"""
from pathlib import Path
import json,pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'Round_LED_Flash.kicad_pcb'
b=p.LoadBoard(str(path))
if list(b.GetTracks()):raise RuntimeError('Preparation is only valid on an unrouted board.')
fps={f.GetReference():f for f in b.GetFootprints()}
def point(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def pad(ref,num):return next(a for a in fps[ref].Pads() if a.GetNumber()==str(num))
def xy(a):return (p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y))
def trace(net,coords,width,layer=p.F_Cu):
    code=b.FindNet('/'+net).GetNetCode()
    for start,end in zip(coords,coords[1:]):
        t=p.PCB_TRACK(b);t.SetStart(point(*start));t.SetEnd(point(*end));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNetCode(code);t.SetLocked(True);b.Add(t)
# Connect the two long internal switch/ground lands before the fan-out pass.
trace('BOOST_SW',[xy(pad('U70',9)),xy(pad('U70',20))],.30)
trace('GND',[xy(pad('U70',10)),xy(pad('U70',19))],.30)
# Deliberate short switch-node trunk, with narrow package escape only.
trace('BOOST_SW',[xy(pad('U70',20)),(131.3,87.5)],.30)
trace('BOOST_SW',[(131.3,87.5),(132.0,88.2),(133.44,89.64),xy(pad('L2',2))],.80)
# Buck-boost switch nodes leave the package toward the two inductor terminals.
trace('LOGIC_L1',[xy(pad('U6',11)),(73.45,77.5),(74.5,76.45),xy(pad('L1',1))],.28)
trace('LOGIC_L2',[xy(pad('U6',9)),(73.45,78.5),(74.5,79.55),xy(pad('L1',2))],.28)
# Ground reference follows the routed annular outline and the existing RF keepout.
z=p.ZONE(b);z.SetLayer(p.In1_Cu);z.SetNet(b.FindNet('/GND'));z.SetLocalClearance(p.FromMM(.2));z.SetMinThickness(p.FromMM(.2))
z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetThermalReliefGap(p.FromMM(.25));z.SetThermalReliefSpokeWidth(p.FromMM(.3))
z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);z.SetMinIslandArea(p.FromMM(1)**2)
o=z.Outline();o.NewOutline()
for x,y in [(57,57),(143,57),(143,143),(57,143)]:o.Append(int(p.FromMM(x)),int(p.FromMM(y)))
b.Add(z)
ds=b.GetDesignSettings();ds.m_TrackMinWidth=p.FromMM(.15)
p.SaveBoard(str(path),b)
project=ROOT/'Round_LED_Flash.kicad_pro';data=json.loads(project.read_text())
data['board']['design_settings']['rules']['min_track_width']=.15
project.write_text(json.dumps(data,indent=2)+'\n')
print('Prepared locked converter rail bridges and In1.Cu ground reference; native DRC required.')
