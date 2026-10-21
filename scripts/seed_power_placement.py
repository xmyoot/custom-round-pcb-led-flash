"""Reviewable critical block seeds; run only before routing, then place_core/DRC."""
from pathlib import Path
import pcbnew as p
root=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(root/'Round_LED_Flash.kicad_pcb'))
if list(b.GetTracks()):raise RuntimeError('Cannot reseed a routed board.')
fp={f.GetReference():f for f in b.GetFootprints()}
seeds={
 'U6':(72,78,0,False),'L1':(76.5,78,270,False),
 'U70':(131,85,180,False),'L2':(134,92,90,False),
 'C284':(134,95.1,90,True),'Q70':(132,83,0,True),
 'R270':(132,79,0,True),'F2':(132,107.5,0,True),
 'C270':(128,82,0,True),'C271':(129,79,0,True),'C272':(127,85,0,True),
 'C280':(135,85,90,False),'C281':(135,82,90,False),'C282':(132,80,0,False),
 'C283':(134,87,0,False),'C274':(134.5,83.5,0,False),
 'C275':(128,83,90,False),'C276':(128,88,90,False),
 'R271':(127,85.5,90,False),'R272':(127,88,90,False),
 'C277':(126,80,0,False),'R275':(126,77,0,False),'C278':(128,78,0,False),
 'U30':(130,109,0,True),'C61':(130,112.5,0,True),'C60':(133.5,109,90,True),
 'R61':(127,110,90,True),'Q30':(135,112.5,0,True),
 'U7':(110,132,180,True),'C6':(114,132,90,True),'C8':(107,130,0,True),
 'U5':(112,134,0,True),'U3':(95,131,0,True),'C4':(92,130,0,True),
 'D4':(97,132,0,True),'D5':(100,132,0,True),'R16':(97,130,0,True),'R17':(100,130,0,True),
 'U2':(90,132,0,True),'C2':(90,134,90,True),'C3':(92,134,90,True),
}
for ref,(x,y,a,back) in seeds.items():
 f=fp[ref];f.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
 if (f.GetLayer()==p.B_Cu)!=back:f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(a)
p.SaveBoard(str(root/'Round_LED_Flash.kicad_pcb'),b)
print('Seeded critical converter block for constrained refinement; run native DRC.')
