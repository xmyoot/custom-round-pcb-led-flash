"""Build the one authoritative KiCad board's mechanical feasibility stage.

Run only while the PCB is unrouted. Refuses to overwrite routed work.
All dimensions in mm; board centre (100,100).
"""
from pathlib import Path
import json, math, re, pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
FP = Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
OUT = ROOT/'Round_LED_Flash.kicad_pcb'

def point(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

def main():
    if OUT.exists():
        old=p.LoadBoard(str(OUT))
        if list(old.GetTracks()):
            raise RuntimeError('Refusing to regenerate a routed board; edit the authoritative board in place.')
        if len(list(old.GetFootprints()))>10:
            raise RuntimeError('Electrical footprints are present. Do not regenerate the mechanical seed.')
    b=p.BOARD()
    b.SetCopperLayerCount(4)
    b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
    for radius in (42,27.5):
        s=p.PCB_SHAPE()
        s.SetShape(p.SHAPE_T_CIRCLE)
        s.SetCenter(point(100,100))
        s.SetEnd(point(100+radius,100))
        s.SetLayer(p.Edge_Cuts)
        s.SetWidth(p.FromMM(.05))
        b.Add(s)
    def load(ref, value, lib, name, x,y,a=0):
        f=p.FootprintLoad(str(FP/(lib+'.pretty')),name)
        if f is None: raise ValueError((lib,name))
        f.SetReference(ref); f.SetValue(value)
        f.SetPosition(point(x,y)); f.SetOrientationDegrees(a)
        f.Value().SetVisible(False)
        f.Reference().SetTextSize(point(.8,.8))
        f.Reference().SetTextThickness(p.FromMM(.12))
        b.Add(f)
        return f
    # The module antenna overhangs the outer edge; the body also overhangs the
    # opening by ~0.6 mm. Neither overhang changes the PCB's 84/55 mm outline.
    local=ROOT/'libraries'/'Round_LED_Flash.pretty'
    local.mkdir(parents=True,exist_ok=True)
    # Store a reviewable derivative, with unchanged electrical pad coordinates.
    source=(FP/'RF_Module.pretty'/'ESP32-C3-WROOM-02.kicad_mod').read_text()
    source=source.replace('(footprint "ESP32-C3-WROOM-02"','(footprint "ESP32-C3-WROOM-02_NoViaInPad"',1)
    source=re.sub(r'\n\t\(pad "19" thru_hole.*?\n\t\)', '', source,flags=re.S)
    source=re.sub(r'\n\t\(fp_(?:line|poly).*?\n\t\)',lambda m:'' if '(layer "F.SilkS")' in m[0] else m[0],source,flags=re.S)
    (local/'ESP32-C3-WROOM-02_NoViaInPad.kicad_mod').write_text(source)
    module=p.FootprintLoad(str(local),'ESP32-C3-WROOM-02_NoViaInPad')
    module.SetReference('U10'); module.SetValue('ESP32-C3-WROOM-02-N4')
    module.SetPosition(point(100,66.1)); module.Value().SetVisible(False)
    module.SetFPID(p.LIB_ID('Round_LED_Flash','ESP32-C3-WROOM-02_NoViaInPad')); b.Add(module)
    # Upright cans, 10.5 mm maximum OD and 22.3 mm maximum height.
    # Pin 1 is offset 2.5 mm from each can's centre in the stock footprint.
    cans=[]
    for ref,ang in zip(('C30','C31','C32','C33'),(5,27,49,71)):
        t=math.radians(ang)
        cx=100+35*math.cos(t); cy=100+35*math.sin(t)
        f=load(ref,'HV1020-2R7505-R','Capacitor_THT','CP_Radial_D10.0mm_P5.00mm',cx-2.5,cy)
        cans.append(dict(reference=ref,center=[cx,cy],max_diameter=10.5,max_height=22.3))
    # USB footprint origin is the left front terminal; orient the mating face
    # downwards and put the shell's rear inward, away from the central hole.
    usb=load('J1','USB4085-GF-A','Connector_USB','USB_C_Receptacle_GCT_USB4085',102.975,139,180)
    usb.SetLocalClearance(p.FromMM(.15))
    bat=load('J2','B2B-PH-K-S(LF)(SN)','Connector_JST','JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',75,123,0)
    for ref,ang in zip(('H1','H2','H3'),(112,198,295)):
        t=math.radians(ang)
        load(ref,'M2.5 NPTH','MountingHole','MountingHole_2.7mm_M2.5',100+35*math.cos(t),100+35*math.sin(t))
    # Keepout covers the antenna and 15 mm in front/beside it. It intentionally
    # extends beyond the PCB. It does not cover the module's solder pads.
    z=p.ZONE(b)
    layers=p.LSET()
    for layer in (p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu): layers.AddLayer(layer)
    z.SetLayerSet(layers); z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
    z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowPads(True)
    # The module itself intersects its antenna keepout. A separate placement
    # rule in the project disallows other footprints in this area.
    z.SetDoNotAllowFootprints(False)
    z.SetZoneName('ANTENNA - no copper or other components; keep enclosure metal away')
    poly=z.Outline(); poly.NewOutline()
    for x,y in ((76,38),(124,38),(124,59.5),(76,59.5)): poly.Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
    text=p.PCB_TEXT(b)
    text.SetText('ROUND LED FLASH / ENGINEERING DRAFT')
    text.SetPosition(point(100,100)); text.SetLayer(p.Dwgs_User)
    text.SetTextSize(point(1.2,1.2)); b.Add(text)
    p.SaveBoard(str(OUT),b)
    report={'stage':'mechanical feasibility, incomplete electrical layout',
            'kicad':p.GetBuildVersion(),'outer_diameter_mm':84,'opening_diameter_mm':55,
            'copper_layers':4,'thickness_mm':1.6,'capacitors':cans,
            'module_origin_mm':[100,66.1],
            'module_overhang':'antenna outside OD; body ~0.7 mm inside opening',
            'remaining':'Pad-to-edge and courtyard checks, connector fit, detailed circuitry and routing are pending.'}
    (ROOT/'analysis'/'mechanical_feasibility.json').write_text(json.dumps(report,indent=2))
    print(str(OUT))

if __name__=='__main__': main()
