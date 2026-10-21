"""Synchronize drafted symbols to the one PCB; preserve existing placements.

Initial placement is deliberately reviewable and unrouted. Refuses to change
pad nets on a routed board. Placement/clearance checks are required afterward.
"""
from pathlib import Path
import json, math, uuid, sys, pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
FP=Path('C:/Program Files/KiCad/10.0/share/kicad/footprints')
NS=uuid.UUID('25177191-f388-422d-afce-131f174624fb')
def uid(key): return str(uuid.uuid5(NS,key))
def pos(x,y): return p.VECTOR2I(p.FromMM(x),p.FromMM(y))

b=p.LoadBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'))
if list(b.GetTracks()): raise RuntimeError('Routed board: use an incremental, reviewed net update instead.')
data=json.loads((ROOT/'analysis'/'draft_connectivity.json').read_text())
live_refs={part['reference'] for part in data['parts'] if part['on_board']}
for old in list(b.GetFootprints()):
    if old.GetReference() in {'C31','C33','R31','R32'} and old.GetReference() not in live_refs:
        b.DeleteNative(old)
sys.path.insert(0,str(Path.home()/'.codex/skills/kicad/scripts'))
from sexp_parser import parse_file,find_first,find_all
native_file=ROOT/'analysis'/'draft.net'
if native_file.stat().st_mtime<(ROOT/'Round_LED_Flash.kicad_sch').stat().st_mtime:
    raise RuntimeError('Export a fresh KiCad netlist before synchronization.')
native=parse_file(str(native_file)); pin_nets={}; pin_metadata={}
for net in find_all(find_first(native,'nets'),'net'):
    name=find_first(net,'name')[1]
    for node in find_all(net,'node'):
        key=(find_first(node,'ref')[1],find_first(node,'pin')[1])
        pin_nets[key]=name
        pin_metadata[key]={x[0]:x[1] for x in node[1:] if isinstance(x,list) and len(x)>1}
existing={f.GetReference():f for f in b.GetFootprints()}
known={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
for name in sorted(set(pin_nets.values())):
    if name not in known:
        n=p.NETINFO_ITEM(b,name); b.Add(n); known[name]=n

locations={
 'U6':(72,78,0),'L1':(76.5,74.5,90),
 'R10':(70,81,90),'R11':(73,81,90),'R12':(78,77,90),
 'R13':(69,107,0),'R14':(71,75,90),
 'C10':(70,78,0),'C11':(69,75,0),'C12':(72,72,90),'C13':(75,70,90),
 'C14':(74.5,82,0),'C15':(77,80,0),'C16':(78.5,83,90),
 'R20':(87,73,90),'R21':(84,73,90),'R22':(85,76,90),'R23':(88,76,90),
 'R24':(85,79,90),'R25':(82,76,90),'R26':(82,79,90),
 'R27':(63,95,0),'R28':(66,95,0),'R29':(63,98,0),'R30':(66,98,0),
 'C20':(87,70,90),'C21':(87,67,90),'C22':(86,63.5,90),
 'C23':(69,95,0),'C24':(69,98,0),
 'SW1':(65,106,0),'SW2':(68,115,0),
 'R40':(70,110,90),'C40':(73,110,90),
 'R41':(126,85,0),'TH1':(125.5,88,0),'C41':(129,87,90),
 'R42':(65,119,90),'D2':(67,121,90),'R43':(67,123,90),'D3':(69,125,90),
 'R31':(130,121,0),'R32':(128,124,0),
 'Q20':(64,95,0),'Q21':(64,100,0),'Q22':(68,95,0),'Q23':(68,100,0),
 'R50':(72,95,0),'R51':(72,100,0),
 'R52':(71,92,0),'R53':(71,103,0),
 'U30':(133,109,0),'C60':(130,107,90),'C61':(130,110,90),
 'R60':(134,105,0),'R61':(136,109,90),'R62':(129,108,90),
 'R63':(129,113,90),'R64':(132,118,90),'R65':(110,137,0),'R66':(128,122,0),
 'Q30':(130,112,0),'Q31':(134,113,0),'Q32':(130,120,0),'Q33':(108,134,0),
 'R67':(136,113,0),'R68':(130,123,0),'R69':(108,137,0),
}
problems=[]
for part in data['parts']:
    ref=part['reference']
    if not part['on_board'] or not part['footprint']: continue
    f=existing.get(ref)
    if f is None:
        lib,name=part['footprint'].split(':',1)
        directory=ROOT/'libraries'/'Round_LED_Flash.pretty' if lib=='Round_LED_Flash' else FP/(lib+'.pretty')
        f=p.FootprintLoad(str(directory),name)
        if f is None: problems.append(f'{ref}: missing {part["footprint"]}'); continue
        f.SetFPID(p.LIB_ID(lib,name)); f.SetReference(ref); b.Add(f)
        if ref.startswith('TP'):
            ang=math.radians(133+7*(int(ref[2:])-1))
            x=100+31*math.cos(ang); y=100+31*math.sin(ang)
            f.SetPosition(pos(x,y)); f.Flip(f.GetPosition(),False)
        elif ref in locations:
            x,y,a=locations[ref]; f.SetPosition(pos(x,y)); f.SetOrientationDegrees(a)
            if ref in ('Q20','Q21','Q22','Q23','R50','R51','R52','R53','U30','C60','C61','R60','R61','R62','R63','R64','R66','Q30','Q31','Q32','R67','R68'):
                f.Flip(f.GetPosition(),False)
        else:
            problems.append(f'{ref}: no initial placement')
    f.SetValue(part['value']); f.Value().SetVisible(False)
    if ref=='C32':
        t=math.radians(27)
        f.SetPosition(pos(100+35*math.cos(t)-2.5,100+35*math.sin(t)))
    lib,name=part['footprint'].split(':',1); f.SetFPID(p.LIB_ID(lib,name))
    attributes=f.GetAttributes()
    if part['in_bom']: attributes &= ~p.FP_EXCLUDE_FROM_BOM
    else: attributes |= p.FP_EXCLUDE_FROM_BOM
    f.SetAttributes(attributes)
    for field,value in {'Datasheet':part['Datasheet'],'MPN':part['MPN'],'Manufacturer':part['Manufacturer'],'BOM Comments':part['Notes'],'Design_Status':'DRAFT - UNRELEASED'}.items():
        f.SetField(field,value); ff=f.GetField(field); ff.SetVisible(False); ff.SetPosition(f.GetPosition())
    f.Reference().SetTextSize(pos(.7,.7)); f.Reference().SetTextThickness(p.FromMM(.1))
    path=p.KIID_PATH(); path.push_back(p.KIID(data['root_uuid'])); path.push_back(p.KIID(uid(ref))); f.SetPath(path)
    padnums=set()
    for pad in f.Pads():
        n=pad.GetNumber()
        if not n: continue
        padnums.add(n)
        if n not in part['nets']:
            problems.append(f'{ref}: footprint pad {n} absent in symbol mapping'); continue
        net=pin_nets.get((ref,n))
        if net: pad.SetNet(known[net])
        meta=pin_metadata.get((ref,n),{})
        pad.SetPinFunction(meta.get('pinfunction',''))
        pad.SetPinType(meta.get('pintype',''))
    for n in part['nets']:
        if n not in padnums: problems.append(f'{ref}: symbol pin {n} absent in footprint')
if problems: raise ValueError('\n'.join(problems))
used={pad.GetNetname() for f in b.GetFootprints() for pad in f.Pads() if pad.GetNetCode()>0}
for net in list(b.GetNetInfo().NetsByNetcode().values()):
    if net.GetNetCode()>0 and net.GetNetname() not in used: b.Remove(net)
p.SaveBoard(str(ROOT/'Round_LED_Flash.kicad_pcb'),b)
print(f'Synchronized {len(data["parts"])} symbols; {len(list(b.GetFootprints()))} PCB footprints')
