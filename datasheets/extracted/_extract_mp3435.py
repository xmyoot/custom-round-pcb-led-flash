import json, pathlib, sys, datetime
sys.path.insert(0, 'C:/Users/hecto/.codex/skills/datasheets/scripts')
import merge_results as merger
cache=pathlib.Path(__file__).parent
mpn='MP3435GL-Z'
now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def evidence(page, section, method='table', confidence='high'):
    return dict(page=page,section=section,method=method,confidence=confidence)
def spec(unit,page,section,min=None,typ=None,max=None,condition=None,notes=None,method='table',confidence='high'):
    return [dict(min=min,typ=typ,max=max,unit=unit,condition=condition,notes=notes,evidence=evidence(page,section,method,confidence))]
def write(task,data,tier='B'):
    schema=json.loads((merger.SCHEMA_DIR/f'{task}.schema.json').read_text())
    err=merger._validate(data,schema)
    if err: raise ValueError(task+': '+err)
    path=cache/f'{mpn}.{task}.result.json'
    if path.exists() and json.loads(path.read_text()).get('status')=='complete': return
    path.write_text(json.dumps(dict(task_id=task,schema_version=schema.get('x-schema-version','1.0'),status='complete',extracted_at=now,model_tier=tier,model_id='gpt-6',data=data),indent=2),encoding='utf-8')
scout=dict(mpn=mpn,metadata=dict(manufacturer='Monolithic Power Systems',datasheet_revision='1.0',datasheet_date='2021-11-30',page_count=26,source_url='https://www.MonolithicPower.com',is_family_pdf=False,family_member_mpns=['MP3435GL','MP3435GL-Z']),categories=['regulator'],extraction_pages=dict(base=[1,2,4,24,25],pinout=[2,3],regulator=[1,3,4,5,6,16,17,18,19,20,21,22,23]),quality_verdict=dict(verdict='extractable',reason=None))
write('scout',scout)
(cache/f'{mpn}.scout.json').write_text(json.dumps(scout,indent=2),encoding='utf-8')
if '--scout-only' in sys.argv: sys.exit()
base=dict(family='synchronous boost converter',description='600 kHz synchronous boost converter with input disconnect and configurable input current limit',package=dict(code='QFN-20 (3mmx4mm)',pin_count=20,body_mm=dict(length=4,width=3),evidence=evidence(2,'Ordering Information')),pinout=[],pin_relationships=[])
abssec='Absolute Maximum Ratings'; opsec='Recommended Operating Conditions'
base['absolute_max']={
 'VIN_max':spec('V',4,abssec,min=-0.3,max=24,notes='Applies to IN, SENSE, OUT, SOUT.'),
 'SW':spec('V',4,abssec,min=-0.3,max=24)+spec('V',4,abssec,min=-3.5,max=28,condition='Transient shorter than 10 ns'),
 'GATE':spec('V',4,abssec,min=-0.3,notes='Upper limit is IN + 5.5 V; symbolic upper limit retained rather than treating 5.5 V as an absolute voltage.'),
 'BST_TM':spec('V',4,abssec,min=-0.3,notes='Upper limit is VSW + 5.5 V.'),
 'other_pins':spec('V',4,abssec,min=-0.3,max=5.5),
 'EN_sink_current':spec('A',4,abssec,max=0.0005),
 'PD':spec('W',4,abssec,max=4.6,condition='TA=25 C, EVL3435-L-00A 4-layer 2oz 63mm x 63mm PCB'),
 'TJ_max':spec('°C',4,abssec,max=150),
 'lead_temperature':spec('°C',4,abssec,max=260),
 'Tstg':spec('°C',4,abssec,min=-65,max=150)}
base['recommended_operating']={'VIN':spec('V',4,opsec,min=3,max=20),'VOUT':spec('V',4,opsec,max=22,notes='Lower bound is VIN, not a fixed numeric minimum.'),'TJ':spec('°C',4,opsec,min=-40,max=125),'EN_sink_current':spec('A',4,opsec,min=0,max=0.0003)}
base['thermal']={'theta_ja':spec('°C/W',4,'Thermal Resistance',typ=27,condition='EVL3435-L-00A 4-layer 2oz 63mm x 63mm PCB')+spec('°C/W',4,'Thermal Resistance',typ=48,condition='JESD51-7 comparison only; not for actual application design'),'theta_jc':spec('°C/W',4,'Thermal Resistance',typ=4,condition='EVL3435-L-00A')+spec('°C/W',4,'Thermal Resistance',typ=11,condition='JESD51-7')}
base['esd']={'HBM':spec('V',4,'ESD Ratings',typ=2000),'CDM':spec('V',4,'ESD Ratings',typ=1500)}
base['moisture_sensitivity']=dict(msl=1,evidence=evidence(2,'Ordering Information'))
base['compliance']=[dict(mark='RoHS',evidence=evidence(1,'Features','prose'))]
write('base',base)
pins=[]
def pin(numbers,name,type,description,notes=None,domain=None,rec=None):
    pins.append(dict(numbers=numbers.split(','),name=name,type=type,description=description,power_domain=domain,alt_functions=[],is_5v_tolerant=None,absolute_max=None,recommended=rec,drive_strength=None,notes=notes,evidence=evidence(3,'Pin Functions')))
pin('1,2','OUT','power_out','Power output; internal high-side MOSFET drain.')
pin('3','TM','unspecified','Internal test pin.','Float in application; only use in product test mode.')
pin('4','BST','power_in','Bootstrap supply for high-side MOSFET driver.')
pin('5','SOUT','input','Samples output voltage and charges BST capacitor; powers VDD when SOUT exceeds VIN.')
pin('6','EN','input','Regulator on/off control; high enables switching.','Do not float. For automatic start connect to input, through 100 kohm if VIN >5.5 V. Also configures input UVLO.',rec=spec('V',5,'Electrical Characteristics',min=1.26,typ=1.33,max=1.39,condition='Rising switching turn-on threshold')+spec('V',5,'Electrical Characteristics',max=0.4,condition='Falling micro-power low threshold'))
pin('7','GATE','output','Driver for optional input disconnect MOSFET.','Floating or connected to external MOSFET requires external current sense resistor. Connect directly to GND for internal sensing; do not use a pull-down resistor.')
pin('8','SENSE','input','External current sense input relative to IN.','Connect SENSE to IN when internal current sensing is selected.')
pin('9,20','SW','passive','Internal low-side MOSFET drain and synchronous high-side MOSFET source; connect power inductor.')
pin('10,17,18,19','PGND','power_in','Power ground.')
pin('11','IN','power_in','Input supply.','Must be locally bypassed.',domain='VIN')
pin('12','VDD','power_out','Internal bias supply.','Decouple with 2.2 uF ceramic capacitor placed as close as possible.')
pin('13','COMP','output','Compensation node.','Connect a resistor and capacitor in series to analog ground for loop stability. Page 23 example uses 24.9 kohm and 3.3 nF for 12 V output, VIN 3–10 V, 2 A; these are example values, not universal requirements.')
pin('14','FB','input','Feedback input with 1.225 V typical reference.','Connect output resistor divider. VOUT=VREF*(1+Rtop/Rbottom); choose resistors in 10 kohm range or higher (page 18).')
pin('15','SS','input','Soft-start control.','Connect soft-start capacitor, charged by constant current; leave disconnected if soft start unused. Typical 7 uA charge current; 10 nF sufficient for most applications (page 18).')
pin('16','AGND','power_in','Analog ground.')
write('pinout',pins,tier='A')
reg=dict(topology='boost',vin_range=spec('V',4,opsec,min=3,max=20),vout_range=spec('V',4,opsec,max=22,notes='Minimum VOUT is VIN.'),iout_max=None,reference_voltage=spec('V',5,'Electrical Characteristics',min=1.212,typ=1.225,max=1.238,condition='TJ=25 C')+spec('V',5,'Electrical Characteristics',min=1.207,typ=1.225,max=1.243,condition='TJ=-40 C to +125 C'),feedback_pin='14',compensation_pin='13',enable_pin='6',power_good_pin=None,cin_min=spec('F',18,'Selecting the Input Capacitor',min=44e-6,condition='High-power applications',notes='At least two 22 uF capacitors recommended for loop stability.',method='prose',confidence='medium'),cout_min=None,inductor_range=None,switching_freq=spec('Hz',5,'Electrical Characteristics',min=510000,typ=600000,max=690000,condition='TJ=25 C')+spec('Hz',5,'Electrical Characteristics',min=450000,max=690000,condition='TJ=-40 C to +125 C'),dropout=None,stability_conditions=dict(cap_types_allowed=['tantalum','electrolytic'],esr_range=None,notes='Page 19 also recommends ceramic without specifying dielectric; three 22 uF ceramic capacitors suitable for most applications, not a guaranteed minimum. Select COUT for ripple/transients and allow voltage derating. External series R-C compensation from COMP to AGND is required (p3); p20 gives FP1=1/(2*pi*RLOAD*COUT), FZ1=1/(2*pi*RCOMP*CCOMP). In CCM, FRHPZ=RLOAD/(2*pi*L)*(VIN/VOUT)^2 (p21), worst at minimum VIN and maximum output power. Page 23 example: RCOMP=24.9 kohm, CCOMP=3.3 nF for VIN 3–10 V, VOUT 12 V, 2 A. No universal output current rating: limited by allowable temperature rise, current limit and VIN (p21). Switch current limit is NOT output current; p6 gives 19/25/29 A min/typ/max at TJ=25 C, GATE=GND, duty=40%.',evidence=evidence(19,'Selecting the Output Capacitor','prose','medium')),sequencing=None)
write('regulator',reg)
print('Validated scout, base, pinout, regulator result files')
