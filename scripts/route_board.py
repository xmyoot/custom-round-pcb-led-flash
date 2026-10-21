"""Controlled routing passes; writes only the authoritative PCB.

Pinned tool revision and geometry are documented in IMPLEMENTATION_HANDOFF.md.
No DRC severity relaxation, pin swaps, or automatic geometry escalation.
"""
from pathlib import Path
import subprocess,sys,os,json
ROOT=Path(__file__).resolve().parents[1]
TOOL=Path.home()/'.codex/tools/KiCadRoutingTools/py_router/route.py'
mode=sys.argv[1]
base=[sys.executable,str(TOOL),str(ROOT/'Round_LED_Flash.kicad_pcb'),'--overwrite',
 '--layers','F.Cu','B.Cu','In2.Cu','--track-width','.2','--clearance','.2','--grid-step','.1',
 '--via-size','.6','--via-drill','.3','--same-net-pad-clearance','.2',
 '--no-fix-drc-settings','--escalation','off','--keep-input-copper','--no-stub-layer-swap',
 '--max-iterations','150000','--max-ripup','2','--neckdown-length','1',
 '--json-out',str(ROOT/f'analysis/route_{mode}.json')]
power={'/CAP_BANK':1.5,'/CAP_MID':1.5,'/CAP_FUSED':1.5,'/BOOST_SENSE':1.2,'/BOOST_INPUT':1.5,
 '/BOOST_OUT':.8,'/LED_ANODES':.8,'/LED_W_K':.5,'/LED_C_K':.5,'/BAT_PROT':.8,
 '/CELL_P':.8,'/CELL_N_RAW':.8,'/CELL_FET_COMMON':.8,'/3V3':.5,'/USB_5V':.5,'/VBUS_RAW':.6}
if mode=='power':
 base+=['--nets',*power,'--power-nets',*power,'--power-nets-widths',*[str(v) for v in power.values()]]
elif mode=='signals':
 base+=['--nets','*','!/GND',*['!'+n for n in power], '!/BOOST_SW','!/LOGIC_L1','!/LOGIC_L2']
elif mode=='ground':base+=['--nets','/GND']
else:raise SystemExit('mode: power, signals, ground')
env=os.environ.copy();env.update(KICAD_RIP_PREEXISTING='0',KICAD_FINALIZE_RIP='0',
 KICAD_RECONCILE_RIP_ESCALATION='0',KICAD_NET_RESCUE='0',KICAD_PLANE_FINALIZE='0')
with (ROOT/f'analysis/route_{mode}.log').open('w') as log:
 result=subprocess.run(base,cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
print(mode,'router exit',result.returncode,'; inspect summary and native DRC')
raise SystemExit(result.returncode)
