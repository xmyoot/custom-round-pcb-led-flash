"""Engineering corner calculations, not a substitute for prototype measurements.

Inputs are taken from the drafted schematic metadata. Bounds not guaranteed by a
manufacturer are explicitly marked as model assumptions in the saved evidence.
"""
from pathlib import Path
from itertools import product
import json,math
ROOT=Path(__file__).resolve().parents[1]
parts={x['reference']:x for x in json.loads((ROOT/'analysis/draft_connectivity.json').read_text())['parts']}
def resistance(ref):
 s=parts[ref]['value'].split()[0]
 return float(s[:-1])*{'k':1e3,'M':1e6}[s[-1]] if s[-1] in 'kM' else float(s)
def comp_thresholds(top,bottom,feedback,pull):
 # At switching, solve the resistor summing junction including output pull-up.
 # Includes ref limits, +/-5mV input offset model, +/-4mV internal hysteresis,
 # resistor tolerance plus differential temperature drift and output low bound.
 precise={'R143','R153','R239','R240'}
 vals=[]
 for tolerances in product((-1,1),repeat=4):
  rs=[]
  for ref,sign in zip((top,bottom,feedback,pull),tolerances):
   tol=.003 if ref in precise else .015
   rs.append(resistance(ref)*(1+sign*tol))
  rt,rb,rh,rp=rs
  for vr,offset,hys,vdd,vol in product((1.223,1.260),(-.005,.005),(-.004,.004),(3.10,3.40),(0,.4)):
   v=vr+offset+hys
   vh=(vdd/rp+v/rh)/(1/rp+1/rh)
   rise=v*(1+rt/rb+rt/rh)-vol*rt/rh
   fall=v*(1+rt/rb+rt/rh)-vh*rt/rh
   vals.append((rise,fall))
 return {'rising_min_V':min(x[0] for x in vals),'rising_max_V':max(x[0] for x in vals),
         'falling_min_V':min(x[1] for x in vals),'falling_max_V':max(x[1] for x in vals)}

boost_min=1.207*(1+resistance('R271')*.997/(resistance('R272')*1.003))
boost_max=1.243*(1+resistance('R271')*1.003/(resistance('R272')*.997))
ready=comp_thresholds('R239','R240','R241','R242')
uvlo=comp_thresholds('R142','R152','R164','R162')
boost_ready=comp_thresholds('R143','R153','R165','R163')
# Datasheet current tolerance is specified at350mA/RSET1.47k. Scaling to200mA
# is an engineering model, not a guaranteed200mA tolerance specification.
imax=.385*1470/(resistance('R230')*.99)
pout=2*imax*boost_max
pin=pout/.80
esr=.04*2*2*1.5 # cell ESR * series * aging * conservative cold multiplier
series=.050 # fuse, shunt, FET, inductor, tracks/vias combined design allocation
v0=ready['falling_min_V'];total_r=esr+series
disc=v0*v0-4*total_r*pin
vin=(v0+math.sqrt(disc))/2 if disc>=0 else 0
iin=pin/vin if vin else float('inf')
cap_terminal=v0-iin*esr
ilim_min=.045/(resistance('R270')*1.01)
window=512*resistance('R200')/50000*1e-6
cool=262144*resistance('R201')/50000*1e-6
window_min=window*.99*.977;window_max=window*1.01*1.023
# Qg maximum39nC at10V / minimum pull-up current near minimum1.7V threshold.
gate_off=39e-9/(1.7/(resistance('R232')*1.01))
bleed_seconds=2.5*1.3*1.2*resistance('R74')*1.01*math.log(4.9/.5)
adc_off_v=5e-6*max(resistance('R28'),resistance('R30'))*1.01

# Actual TDK R/T8016 min/max table at cell qualification boundaries.
ntc_table={0:(31907,33393),5:(24877,25898),40:(5236.9,5417.1),45:(4286.1,4451.3)}
ntc={}
for temp,(lo,hi) in ntc_table.items():
 fractions=[]
 for rn,rt,rdiv in product((lo,hi),(resistance('R80')*.99,resistance('R80')*1.01),(1.98e6,2.02e6)):
  effective=1/(1/rn+1/rdiv)
  fractions.append(effective/(rt+effective))
 ntc[str(temp)]={'ratio_min':min(fractions),'ratio_max':max(fractions)}

checks={
 'permanent_bleed_to_half_volt_model_within_60min':bleed_seconds<3600,
 'ADC_off_leakage_below_unpowered_pin_limit':adc_off_v<.3,
 'cap_ready_reachable_at_charger_min':ready['rising_max_V']<4.7,
 'boost_ready_reachable_at_boost_min':boost_ready['rising_max_V']<boost_min,
 'input_above_converter_min_3V':vin>3,
 'current_below_min_average_limit':iin<ilim_min,
 'cap_terminal_above_uvlo':cap_terminal>uvlo['falling_max_V'],
 'nominal_requested_1ms_plus_50us_inside_window':window_min>.00105,
 'hardware_cutoff_model_below_2ms':window_max+gate_off<.002,
 'minimum_cooldown_exceeds_1s':cool*.99*.977>1,
 'open_ntc_halts':1/(1+resistance('R80')/2e6)>.82,
 'zeroC_always_cold_inhibited':ntc['0']['ratio_min']>.82,
 'fortyfiveC_always_hot_inhibited':ntc['45']['ratio_max']<.43,
}
result={'status':'calculated model; prototype qualification pending','checks':checks,
 'permanent_bleed_to_half_volt_model_s':bleed_seconds,'ADC_off_leakage_max_model_V':adc_off_v,
 'boost_V':[boost_min,boost_max],'cap_ready':ready,'loaded_cap_uvlo':uvlo,'boost_ready':boost_ready,
 'current_model_max_A_per_channel':imax,'output_power_max_W':pout,'input_power_model_W':pin,
 'bank_ESR_aged_cold_ohm':esr,'series_path_allocation_ohm':series,'loaded_input_min_V':vin,
 'input_current_model_max_A':iin,'input_current_limit_min_A':ilim_min,'cap_terminal_loaded_min_V':cap_terminal,
 'timer_window_s':[window_min,window,window_max],'PFET_off_bound_model_s':gate_off,
 'cooldown_min_s':cool*.99*.977,'ntc_boundary_fractions':ntc,
 'assumptions':['Indoor prototype operating range0 to40C; no subzero flash guarantee.',
 '80% boost efficiency is a design floor to qualify by measurement, not a datasheet guarantee.',
 'CAT4101 current bound extrapolated by inverse RSET from its350mA test; measure both actual channels.',
 'Cold ESR multiplier1.5 is conservative at0C from Eaton typical curve; ESR is not guaranteed for1ms by DC test.',
 'Total interconnect/FET/shunt/inductor/fuse allocation50mohm must be checked against final geometry and parts.',
 'TLV3011B offset bound+/-5mV is conservative; reference limits from extracted PDF. Internal hysteresis modeled+/-4mV.',
 'TCAD/loop and optical timing measurements are prototype qualification, not represented by ERC/DRC.'],
 'sources':{'cap':'Eaton HV TechnicalData4376 pp2-4','current':'onsemi CAT4101 Rev8 pp2,7',
 'boost':'MPS MP3435 Rev1.0 pp5-6,18-21','comparators':'TI TLV3011B SBOS300C and datasheets/extracted/TLV3011BIDBVR.json',
 'NTC':'TDK R/T8016 10k 1% B3988 1%, table in l865 sheet (same curve and tolerances as S861)',
 'timer':'ADI LTC6993 RevF pp1,13; timing resistor1%'}}
(ROOT/'analysis/design_envelope.json').write_text(json.dumps(result,indent=2))
for k,v in checks.items():print(('PASS' if v else 'FAIL'),k)
print('Vin',round(vin,3),'V; Iin',round(iin,3),'A; cap terminal',round(cap_terminal,3),'V')
print('Thresholds',ready,uvlo,boost_ready)
if not all(checks.values()):raise SystemExit(1)
