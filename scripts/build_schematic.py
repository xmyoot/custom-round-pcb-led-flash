"""Generate the authoritative single-sheet schematic from explicit pin/net data.

This is an engineering drafting tool. Native ERC, datasheet checks, and visual
review are required after edits. It does not qualify a design for manufacture.
"""
from pathlib import Path
import copy, json, math, re, sys, uuid

ROOT=Path(__file__).resolve().parents[1]
LIB=Path('C:/Program Files/KiCad/10.0/share/kicad/symbols')
sys.path.insert(0,str(Path.home()/'.codex/skills/kicad/scripts'))
from sexp_parser import parse, find_all, find_first, find_deep, get_property

NS=uuid.UUID('25177191-f388-422d-afce-131f174624fb')
def uid(key): return str(uuid.uuid5(NS,key))
def q(s): return json.dumps(str(s),ensure_ascii=False)
def fx(size=1,justify=''): return f'(effects (font (size {size} {size})) {justify})'
def text(s,x,y,size=1.2): return f'(text {q(s)} (at {x} {y} 0) {fx(size,"(justify left)")} (uuid {q(uid("text"+str(x)+str(y)+s))}))'

def raw_symbol(lib,name):
    source=(LIB/(lib+'.kicad_sym')).read_text(encoding='utf-8')
    marker='(symbol '+q(name)
    start=source.find(marker+'\n')
    if start<0: start=source.find(marker+'\r')
    if start<0: raise KeyError((lib,name))
    depth=0; string=False; esc=False
    for i in range(start,len(source)):
        c=source[i]
        if string:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': string=False
        elif c=='"': string=True
        elif c=='(': depth+=1
        elif c==')':
            depth-=1
            if depth==0:
                raw=source[start:i+1]
                if '(extends ' in raw: raise ValueError('Resolve inherited symbol explicitly: '+lib+':'+name)
                return raw.replace(marker,'(symbol '+q(lib+':'+name),1)
    raise ValueError('Unbalanced symbol')

def ic_symbol(name,pins):
    # pins: (number, name, electrical type). Preserve physical numbers verbatim.
    n=(len(pins)+1)//2; h=max(7.62,(n+1)*1.27)
    body=[f'(symbol {q("Round_LED_Flash:"+name)} (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
          f'(property "Reference" "U" (at 0 {h+2.54} 0) {fx()})',
          f'(property "Value" {q(name)} (at 0 {-h-2.54} 0) {fx()})',
          f'(symbol {q(name+"_0_1")} (rectangle (start -10.16 {h}) (end 10.16 {-h}) (stroke (width 0) (type default)) (fill (type background))))',
          f'(symbol {q(name+"_1_1")}']
    for index,(number,pname,ptype) in enumerate(pins):
        side=index//n; j=index%n
        x=-15.24 if side==0 else 15.24
        y=(n-1)*1.27-j*2.54
        body.append(f'(pin {ptype} line (at {x} {y} {0 if side==0 else 180}) (length 5.08) (name {q(pname)} {fx(.9)}) (number {q(number)} {fx(.9)}))')
    return '\n'.join(body)+'))'

symbols={}; parts=[]; annotations=[]
def add(ref,value,libid,footprint,nets,x,y,angle=0,mpn='',manufacturer='',datasheet='',notes='',on_board=True):
    if libid not in symbols:
        lib,name=libid.split(':',1); symbols[libid]=raw_symbol(lib,name)
    x=round(x/1.27)*1.27; y=round(y/1.27)*1.27
    parts.append(dict(reference=ref,value=value,libid=libid,footprint=footprint,
                      nets={str(k):v for k,v in nets.items()},x=x,y=y,angle=angle,
                      MPN=mpn,Manufacturer=manufacturer,Datasheet=datasheet,Notes=notes,on_board=on_board,
                      in_bom=not ref.startswith(('TP','H'))))

def ic(ref,name,pins,nets,footprint,x,y,mpn,manufacturer,ds,notes=''):
    libid='Round_LED_Flash:'+name
    if libid not in symbols: symbols[libid]=ic_symbol(name,pins)
    add(ref,mpn,libid,footprint,nets,x,y,mpn=mpn,manufacturer=manufacturer,datasheet=ds,notes=notes)

RFP='Resistor_SMD:R_0603_1608Metric'
CFP='Capacitor_SMD:C_0603_1608Metric'
def r(ref,value,a,b,x,y,fp=RFP,notes=''):
    add(ref,value,'Device:R',fp,{1:a,2:b},x,y,90,notes=notes)
def c(ref,value,a,b,x,y,fp=CFP,mpn='',notes=''):
    add(ref,value,'Device:C',fp,{1:a,2:b},x,y,90,mpn=mpn,manufacturer='Murata' if mpn else '',notes=notes)
def label(s,x,y,a=0): return f'(label {q(s)} (at {x:.4f} {y:.4f} {a}) {fx(.9,"(justify left bottom)")} (uuid {q(uid("label"+str(x)+str(y)+s))}))'

def core():
    # Section 1: logic regulator. Datasheet pin table and adjustable reference.
    ds='https://www.ti.com/lit/ds/symlink/tps63070.pdf'
    pins=[('12','VIN','power_in'),('13','VIN','power_in'),('14','EN','input'),('1','PS_SYNC','input'),('15','VSEL','input'),('6','FB2','passive'),('4','GND','power_in'),('10','PGND','power_in'),('11','L1','passive'),('9','L2','passive'),('7','VOUT','power_out'),('8','VOUT','passive'),('5','FB','input'),('3','VAUX','passive'),('2','PG','open_collector')]
    ic('U6','TPS63070',pins,{12:'BAT_PROT',13:'BAT_PROT',14:'SYS_EN',1:'LOGIC_PS_SYNC',15:'GND',6:None,4:'GND',10:'GND',11:'LOGIC_L1',9:'LOGIC_L2',7:'3V3',8:'3V3',5:'LOGIC_FB',3:'LOGIC_AUX',2:'LOGIC_PG'},
       'Round_LED_Flash:TPS63070_RNM0015A',65,65,'TPS63070RNMR','Texas Instruments',ds)
    add('L1','1.5uH','Device:L','Round_LED_Flash:Coilcraft_XFL4020',{1:'LOGIC_L1',2:'LOGIC_L2'},115,55,90,mpn='XFL4020-152MEC',manufacturer='Coilcraft',datasheet='https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf',notes='Independent footprint verification remains a release gate.')
    r('R10','470k','3V3','LOGIC_FB',115,75)
    r('R11','150k','LOGIC_FB','GND',165,75)
    c('C10','100n','LOGIC_AUX','GND',115,95)
    for ref,x in (('C11',115),('C12',165),('C13',215)):
        c(ref,'10u 10V','BAT_PROT','GND',x,115,fp='Capacitor_SMD:C_0805_2012Metric')
    for ref,x in (('C14',115),('C15',165),('C16',215)):
        c(ref,'22u 16V','3V3','GND',x,135,fp='Capacitor_SMD:C_0805_2012Metric')
    r('R12','4.7k','3V3','LOGIC_PG',215,75)
    r('R18','10k','BAT_PROT','LOGIC_PS_SYNC',215,95,notes='Series control isolation required by TPS63070 datasheet section11.1 for pins tied to VIN.')
    add('SW1','POWER','Switch:SW_SPDT','Button_Switch_SMD:SW_SPDT_CK_JS102011SAQN',{1:'BAT_PROT',2:'SW_ON',3:'GND'},65,115,mpn='JS102011SAQN',manufacturer='C&K',notes='Common is pin 2. Position connects enable to cell or ground.')
    r('R13','100k','SW_ON','SYS_EN',65,145)
    r('R14','1M','SYS_EN','GND',165,95)
    # USB pulls enable low with a transistor (added in charging section).
    annotations.append(text('01 / 3.3 V BUCK-BOOST - 500 mA minimum design target',25,25,2))
    annotations.append(text('Draft: exact inductor suffix, capacitor MPNs and loop layout still require verification.',25,165))

    # Section 2: ESP32. Follow published module pin numbering, no boot-pin loads.
    nets={1:'3V3',2:'MCU_EN',3:'REQ_W',4:'REQ_C',5:'ARM',6:'TRIGGER_ALLOWED',7:'STRAP8',8:'BOOT_N',9:'GND',10:'SHUTTER_N',11:'UART_RX',12:'UART_TX',13:'BLE_LED',14:'READY_LED',15:'ADC_NTC',16:'TRIG_REQ',17:'ADC_CAP',18:'ADC_BAT',19:'GND'}
    add('U10','ESP32-C3-WROOM-02-N4','RF_Module:ESP32-C3-WROOM-02','Round_LED_Flash:ESP32-C3-WROOM-02_NoViaInPad',nets,335,80,
        mpn='ESP32-C3-WROOM-02-N4',manufacturer='Espressif Systems',datasheet='https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf')
    for ref,net,x,y in [('R20','MCU_EN',390,45),('R21','BOOT_N',440,45),('R22','TRIG_REQ',490,45),('R23','STRAP8',390,65)]: r(ref,'10k','3V3',net,x,y)
    c('C20','1u','MCU_EN','GND',440,65)
    c('C21','100n','3V3','GND',490,65)
    c('C22','10u','3V3','GND',390,85,fp='Capacitor_SMD:C_0805_2012Metric')
    for ref,net,x,y in [('R24','REQ_W',390,105),('R25','REQ_C',440,105),('R26','ARM',490,105)]:
        r(ref,'4.7k',net,'GND',x,y,notes='Default-low flash/arm request. Hardware interlocks remain mandatory during boot/reset.')
    r('R27','100k','BAT_SENSE_SW','ADC_BAT',390,125)
    r('R28','100k','ADC_BAT','GND',440,125)
    c('C23','100n','ADC_BAT','GND',490,125)
    r('R29','100k','CAP_SENSE_SW','ADC_CAP',390,145)
    r('R30','100k','ADC_CAP','GND',440,145)
    c('C24','100n','ADC_CAP','GND',490,145)
    annotations.append(text('02 / BLE CONTROLLER + UART PROGRAMMING',285,25,2))
    annotations.append(text('GPIO2 high for boot, then TRIG_REQ output LOW before ARM. GPIO7 reads TRIGGER_ALLOWED.',285,165))

    # Section 3: two 5F cells in series, charged/balanced to 4.8V by LTC3225.
    capfp='Capacitor_THT:CP_Radial_D10.0mm_P5.00mm'
    for ref,hi,lo,x,y in [('C30','CAP_BANK','CAP_MID',580,60),('C32','CAP_MID','GND',580,105)]:
        add(ref,'5F 2.7V','Device:C_Polarized',capfp,{1:hi,2:lo},x,y,
            mpn='HV1020-2R7505-R',manufacturer='Eaton',datasheet='https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-hv-supercapacitors-cylindrical-cells-data-sheet.pdf',notes='Maximum body 10.5 mm diameter x 22.3 mm high. Hand-solder after reflow. Pulse and aged ESR validation pending.')
    annotations.append(text('03 / 2.5 F EFFECTIVE CAP BANK - regulated 4.8 V',545,25,2))
    annotations.append(text('Two series cells; midpoint connects to LTC3225 CX. No bleed balancing resistors.',545,145))
    annotations.append(text('Nominal stored energy 28.8 J. Fused boost branch, timed output cutoff and default-on discharge.',545,165))

    # Section 4: user inputs and indicators.
    add('SW2','SHUTTER','Switch:SW_Push','Button_Switch_SMD:SW_SPST_TL3342',{1:'SHUTTER_N',2:'GND'},65,235,mpn='TL3342F160QG',manufacturer='E-Switch')
    r('R40','10k','3V3','SHUTTER_N',115,235)
    c('C40','100n','SHUTTER_N','GND',165,235)
    r('R41','10k','3V3','ADC_NTC',65,270)
    add('TH1','10k NTC','Device:Thermistor_NTC','Resistor_SMD:R_0603_1608Metric',{1:'ADC_NTC',2:'GND'},115,270,90,notes='LED-area sensor; actual MPN/Beta pending. Not a cell temperature sensor.')
    c('C41','100n','ADC_NTC','GND',165,270)
    for ref,rref,net,color,y in [('D2','R42','BLE_LED','BLUE',305),('D3','R43','READY_LED','GREEN',335)]:
        r(rref,'1k',net,net+'_A',65,y)
        add(ref,color,'Device:LED','LED_SMD:LED_0603_1608Metric',{1:'GND',2:net+'_A'},115,y,notes='Select LED MPN and brightness/current before BOM freeze.')
    annotations.append(text('04 / SHUTTER, INDICATORS, LED-AREA NTC',25,205,2))
    annotations.append(text('D1 indicates battery charging; D2 BLE; D3 firmware flash-ready. TH1 senses LED-area temperature.',25,365))

    # Section 5: connectors present in the mechanical placement.
    add('J1','USB4085-GF-A','Connector:USB_C_Receptacle_USB2.0_16P','Connector_USB:USB_C_Receptacle_GCT_USB4085',
        {'A1':'GND','B1':'GND','A4':'VBUS_RAW','B4':'VBUS_RAW','A5':'CC1_RAW','B5':'CC2_RAW','A6':None,'B6':None,'A7':None,'B7':None,'A8':None,'B8':None,'A9':'VBUS_RAW','B9':'VBUS_RAW','A12':'GND','B12':'GND','SH':'GND'},335,265,
        mpn='USB4085-GF-A',manufacturer='GCT',datasheet='https://gct.co/files/drawings/usb4085.pdf',notes='Charging only. Contacts and shell stakes are through-hole. Local pad clearance is 0.15 mm, per land pattern.')
    add('J2','BATTERY','Connector_Generic:Conn_01x02','Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical',{1:'CELL_P',2:'CELL_N_RAW'},440,245,
        mpn='B2B-PH-K-S(LF)(SN)',manufacturer='JST',notes='Raw cell negative is not protected system ground. Connect an isolated two-wire single-cell pack only.')
    for ref,net,y in [('TP1','GND',290),('TP2','3V3',310),('TP3','UART_TX',330),('TP4','UART_RX',350),('TP5','MCU_EN',370),('TP6','BOOT_N',390)]:
        add(ref,net,'Connector:TestPoint','TestPoint:TestPoint_Pad_D1.5mm',{1:net},440,y,notes='UART fixture uses protected ground only.')
    annotations.append(text('05 / CONNECTORS + 3.3 V UART POGO ACCESS',285,205,2))

    for ref,x in [('H1',580),('H2',640),('H3',700)]:
        add(ref,'M2.5 NPTH','Mechanical:MountingHole','MountingHole:MountingHole_2.7mm_M2.5',{},x,240)

    # Switch divider upper legs off whenever the logic rail is not power-good.
    # PMOS body diodes point from the sense node toward the source rail.
    for i,source,drain,x in [(0,'BAT_PROT','BAT_SENSE_SW',580),(1,'CAP_BANK','CAP_SENSE_SW',680)]:
        add('Q'+str(20+i),'AO3401A','Transistor_FET:Q_PMOS_GSD','Package_TO_SOT_SMD:SOT-23',
            {1:'SENSE_GATE_'+str(i),2:source,3:drain},x,375,
            mpn='AO3401A',manufacturer='Alpha & Omega Semiconductor',datasheet='https://www.aosmd.com/res/data_sheets/AO3401A.pdf',
            notes='Divider high-side switch. Gate pulls to its own source; diode blocks source-to-ADC while off.')
        add('Q'+str(22+i),'MMBT3904-7-F','Transistor_BJT:Q_NPN_BEC','Package_TO_SOT_SMD:SOT-23',
            {1:'SENSE_BASE_'+str(i),2:'GND',3:'SENSE_GATE_'+str(i)},x+40,375,
            mpn='MMBT3904-7-F',manufacturer='Diodes Incorporated',datasheet='https://www.diodes.com/datasheet/download/MMBT3904.pdf')
        r('R'+str(50+i),'100k',source,'SENSE_GATE_'+str(i),x,405)
        r('R'+str(52+i),'100k','LOGIC_PG','SENSE_BASE_'+str(i),x+40,405,
          notes='Base current limits PG loading; pull-down saturation current is only tens of microamps.')
    annotations.append(text('07 / ADC POWER-OFF ISOLATION - enabled by regulator PG',545,350,2))
    annotations.append(text('TPS63070 PG is low with EN low; dividers discharge through their lower resistors.',545,425))

    # Section 8: balanced, limited charge-pump charger. Pin mapping from ADI
    # 3225fb page 5; voltage/current choices from pages 2,3,8. No -1 suffix.
    pins=[('9','VIN','power_in'),('4','SHDN','input'),('6','VSEL','input'),('7','PROG','passive'),('8','GND','power_in'),('11','EP_GND','power_in'),('10','COUT','power_out'),('3','CX','passive'),('1','C_PLUS','passive'),('2','C_MINUS','passive'),('5','PGOOD','open_collector')]
    ic('U30','LTC3225',pins,{9:'BAT_PROT',4:'CAP_CHG_EN',6:'GND',7:'CAP_PROG',8:'GND',11:'GND',10:'CAP_BANK',3:'CAP_MID',1:'CAP_FLY_P',2:'CAP_FLY_N',5:'CAP_PGOOD'},
       'Package_DFN_QFN:DFN-10-1EP_2x3mm_P0.5mm_EP0.64x2.4mm',55,485,
       'LTC3225EDDB#TRMPBF','Analog Devices','https://www.analog.com/media/en/technical-documentation/data-sheets/3225fb.pdf',
       '4.8V selection, automatic cell balancing. EP soldered to ground. Independent package-land check pending.')
    c('C60','4.7u 10V','BAT_PROT','GND',110,505,fp='Capacitor_SMD:C_0805_2012Metric')
    c('C61','2.2u 16V','CAP_FLY_P','CAP_FLY_N',155,505,fp='Capacitor_SMD:C_0805_2012Metric',notes='Select effective capacitance >=1uF at applied voltage for charge-pump flying capacitor.')
    r('R61','24k','CAP_PROG','GND',110,485,notes='Nominal input current 150mA; nominal balanced bank charge current 75mA.')
    r('R62','10k','3V3','CAP_PGOOD',155,465)
    add('Q30','AO3401A','Transistor_FET:Q_PMOS_GSD','Package_TO_SOT_SMD:SOT-23',
        {1:'CAP_EN_GATE',2:'BAT_PROT',3:'CAP_EN_FEED'},110,440,mpn='AO3401A',manufacturer='Alpha & Omega Semiconductor',datasheet='https://www.aosmd.com/res/data_sheets/AO3401A.pdf',notes='Battery-referenced SHDN drive avoids driving SHDN above VIN when the battery supply disappears.')
    for ref,signal,drain,x,y,res,value in [('Q31','ARM','CAP_EN_GATE',155,440,'R67','100k'),('Q32','HW_WINDOW','CAP_CHG_EN',205,525,'R68','47k'),('Q33','VBUS_RAW','CAP_CHG_EN',155,545,'R69','47k')]:
        base=ref+'_BASE'
        add(ref,'MMBT3904-7-F','Transistor_BJT:Q_NPN_BEC','Package_TO_SOT_SMD:SOT-23',
            {1:base,2:'GND',3:drain},x,y,mpn='MMBT3904-7-F',manufacturer='Diodes Incorporated',datasheet='https://www.diodes.com/datasheet/download/MMBT3904.pdf')
        r(res,value,signal,base,x+40,y)
    r('R60','100k','BAT_PROT','CAP_EN_GATE',205,440)
    r('R63','10k','CAP_EN_FEED','CAP_CHG_EN',205,465)
    r('R64','100k','CAP_CHG_EN','GND',205,485)
    r('R65','100k','VBUS_RAW','GND',110,545)
    r('R66','100k','HW_WINDOW','GND',205,550)
    annotations.append(text('08 / 4.8 V SUPERCAP CHARGER + AUTOMATIC BALANCING',25,415,2))
    annotations.append(text('Charge enabled by ARM; USB presence or timed flash window forces SHDN low.',25,570))

def write():
    rootid=uid('root')
    out=['(kicad_sch (version 20250114) (generator "eeschema") (generator_version "10.0")',f'(uuid {q(rootid)}) (paper "User" 1189 1189)',
         '(title_block (title "ROUND LED FLASH - ENGINEERING DRAFT") (date "2026-10-20") (rev "A-draft") (comment 1 "Incomplete electrical design - NOT FOR FABRICATION"))',
         '(lib_symbols '+'\n'.join(symbols.values())+')']
    errors=[]
    for part in parts:
        ref=part['reference']; x=part['x']; y=part['y']; a=part['angle']
        parsed=parse(symbols[part['libid']]); pins=[]
        for sub in find_all(parsed,'symbol'):
            # All selected stock symbols use one unit (unit 0 common also valid).
            pins.extend(find_all(sub,'pin'))
        uuidpart=uid(ref)
        b=['(symbol',f'(lib_id {q(part["libid"])}) (at {x} {y} {a}) (unit 1)',
           f'(in_bom {"yes" if part["in_bom"] else "no"}) (on_board {"yes" if part["on_board"] else "no"}) (dnp no) (uuid {q(uuidpart)})']
        props={'Reference':ref,'Value':part['value'],'Footprint':part['footprint'],'Datasheet':part['Datasheet'],'MPN':part['MPN'],'Manufacturer':part['Manufacturer'],'BOM Comments':part['Notes'],'Design_Status':'DRAFT - UNRELEASED'}
        for i,(key,val) in enumerate(props.items()):
            yy=y-4.0 if i==0 else y-1.8
            hidden='' if i<2 else '(hide yes)'
            b.append(f'(property {q(key)} {q(val)} (at {x} {yy} 0) {hidden} {fx(.9)})')
        seen=set()
        for pin in pins:
            number=find_first(pin,'number')[1]
            if number in seen: continue
            seen.add(number)
            b.append(f'(pin {q(number)} (uuid {q(uid(ref+"pin"+number))}))')
            if number not in part['nets']:
                errors.append(f'{ref} missing pin {number}')
                continue
            at=find_first(pin,'at'); px=float(at[1]); py=float(at[2]); theta=math.radians(a)
            # Library y is up; sheet y is down. KiCad angle is CCW.
            xx=x+px*math.cos(theta)-py*math.sin(theta)
            yy=y-px*math.sin(theta)-py*math.cos(theta)
            net=part['nets'][number]
            if net is None:
                out.append(f'(no_connect (at {xx:.4f} {yy:.4f}) (uuid {q(uid(ref+"NC"+number))}))')
            else:
                pa=(float(at[3])+a)%360
                # Continue each pin outwards. Pin orientation points toward body.
                dx=-2.54*math.cos(math.radians(pa)); dy=2.54*math.sin(math.radians(pa))
                ex=xx+dx; ey=yy+dy
                out.append(f'(wire (pts (xy {xx:.4f} {yy:.4f}) (xy {ex:.4f} {ey:.4f})) (stroke (width 0) (type default)) (uuid {q(uid(ref+"wire"+number))}))')
                out.append(label(net,ex,ey,0 if dx>=0 else 180))
        b.append(f'(instances (project "Round_LED_Flash" (path {q("/"+rootid)} (reference {q(ref)}) (unit 1))))')
        b.append(')'); out.append('\n'.join(b))
    if errors: raise ValueError('\n'.join(errors))
    out+=annotations; out.append(')')
    (ROOT/'Round_LED_Flash.kicad_sch').write_text('\n'.join(out),encoding='utf-8')
    (ROOT/'analysis'/'draft_connectivity.json').write_text(json.dumps({'root_uuid':rootid,'parts':parts},indent=2))
    custom=[v for k,v in symbols.items() if k.startswith('Round_LED_Flash:')]
    (ROOT/'libraries'/'Round_LED_Flash.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor")\n'+'\n'.join(s.replace('Round_LED_Flash:','',1) for s in custom)+'\n)')
    print(f'Wrote {len(parts)} symbols to the authoritative schematic')

if __name__=='__main__':
    core()
    import build_power, build_flash, build_boost, select_bom
    build_power.populate(globals())
    build_flash.populate(globals())
    build_boost.populate(globals())
    select_bom.enrich(globals())
    write()
