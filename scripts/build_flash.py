"""Flash timing and constant-current channels; release validation still required."""

def populate(d):
    add,ic,r,c,text,annotations=(d[k] for k in ('add','ic','r','c','text','annotations'))
    ti='https://www.ti.com/lit/ds/symlink/'
    s5='Package_TO_SOT_SMD:SOT-23-5'
    s6='Package_TO_SOT_SMD:SOT-23-6'
    def gate(ref,kind,a,b,y,xp,yp):
        pins=[(1,'A','input'),(2,'B','input'),(3,'GND','power_in'),(4,'Y','output'),(5,'VCC','power_in')]
        nets={1:a,2:b,3:'GND',4:y,5:'3V3'}
        if kind=='04':
            pins[0]=(1,'NC','no_connect');nets[1]=None;nets[2]=a
        ic(ref,'SN74LVC1G'+kind,pins,nets,s5,xp,yp,'SN74LVC1G'+kind+'DBVR','Texas Instruments',ti+'sn74lvc1g'+kind+'.pdf')
        c('C'+str(100+int(ref[1:])),'100n','3V3','GND',xp+45,yp)

    # Independent cap and boost rail comparators have fail-safe inputs (B part).
    for ref,rail,top,bottom,out,x,y in [
        ('U42','CAP_BANK','165k','100k','CAP_OK',55,665),
        ('U43','BOOST_OUT','147k','10k','BOOST_OK',55,755)]:
        n=int(ref[1:]); sense=rail+'_HW_SENSE'; vref=rail+'_HW_REF'
        ic(ref,'TLV3011B',[(1,'OUT','open_collector'),(2,'GND','power_in'),(3,'IN_PLUS','input'),(4,'IN_MINUS','input'),(5,'REF','output'),(6,'VDD','power_in')],
           {1:out,2:'GND',3:sense,4:vref,5:vref,6:'3V3'},s6,x,y,'TLV3011BIDBVR','Texas Instruments',ti+'tlv3011.pdf')
        r('R'+str(100+n),top,rail,sense,x+50,y-20)
        r('R'+str(110+n),bottom,sense,'GND',x+100,y-20)
        r('R'+str(120+n),'10k','3V3',out,x+150,y-20)
        c('C'+str(100+n),'100n','3V3','GND',x+50,y+20)
        r('R'+str(122+n),'2.21M' if ref=='U42' else '1M',out,sense,x+150,y+20,
          notes='Positive feedback provides rail hysteresis. Include pull-up loading, reference and resistor tolerances in thresholds.')
    annotations.append(text('14 / INDEPENDENT RAIL INTERLOCKS',25,625,2))
    annotations.append(text('Loaded-rail interlocks: cap ~3.39V rising / 3.15V falling; boost ~19.67V / 19.20V.',25,805))

    # Timers operate independently from firmware. The -1 suffix is mandatory.
    pins=[(1,'TRIG','input'),(2,'GND','power_in'),(3,'SET','passive'),(4,'DIV','input'),(5,'VDD','power_in'),(6,'OUT','output')]
    for ref,trig,out,rset,rtop,rbot,x,y in [
        ('U40','FLASH_TRIGGER','TIMER_WINDOW','137k','357k','100k',335,665),
        ('U41','TIMER_WINDOW','COOLDOWN','240k','146k','100k',335,755)]:
        n=int(ref[1:]);setnet=ref+'_SET';divnet=ref+'_DIV'
        ic(ref,'LTC6993_1',pins,{1:trig,2:'GND',3:setnet,4:divnet,5:'3V3',6:out},s6,x,y,
           'LTC6993CS6-1#TRMPBF','Analog Devices',
           'https://www.analog.com/media/en/technical-documentation/data-sheets/ltc6993-6993-1-6993-2-6993-3-6993-4.pdf',
           'Rising-edge non-retriggerable. 1% timing resistors. -2 variant is not permitted.')
        for offset,val,a,b,xx,yy in [(160,rset,setnet,'GND',x+50,y),(170,rtop,'3V3',divnet,x+100,y),(180,rbot,divnet,'GND',x+150,y)]:
            r('R'+str(offset+n),val,a,b,xx,yy)
        c('C'+str(100+n),'100n','3V3','GND',x+50,y+25)
    annotations.append(text('15 / NON-RETRIGGERABLE PULSE + COOLDOWN',285,625,2))
    annotations.append(text('U40: 1.403ms nominal maximum window; U41: 1.258s lockout from each window start.',285,805))

    # Separate trigger permits the physical LED switch to settle before PWM.
    # A held trigger can repeat windows at cooldown, always bounded in duration.
    gate('U44','08','TRIG_REQ','POR_OK','TRIG_SAFE',580,655)
    gate('U45','04','COOLDOWN',None,'COOLDOWN_READY',680,655)
    gate('U46','08','POR_OK','CAP_OK','RAILS_OK',580,700)
    gate('U47','08','RAILS_OK','ARM','BOOST_REQUEST',680,700)
    gate('U48','08','BOOST_REQUEST','BOOST_OK','HW_OK',580,745)
    gate('U49','08','HW_OK','ENERGY_REARM_OK','TRIGGER_ALLOWED',680,745)
    gate('U50','08','TRIG_SAFE','TRIGGER_ALLOWED','FLASH_TRIGGER',580,790)
    # Requalify the physical power window continuously, even if a rail fails.
    gate('U51','08','TIMER_WINDOW','HW_OK','HW_WINDOW',680,790)
    gate('U52','08','REQ_W','HW_WINDOW','SINK_W_EN',825,655)
    gate('U53','08','REQ_C','HW_WINDOW','SINK_C_EN',925,655)
    r('R100','4.7k','SINK_W_EN','GND',825,700)
    r('R101','4.7k','SINK_C_EN','GND',925,700)
    annotations.append(text('16 / HARDWARE FLASH PERMISSION + CHANNEL GATING',545,625,2))

    # D2PAK tab is grounded pin 3. Current includes aged/cold bank ESR margin.
    for ref,en,led,setnet,rref,cref,x,y in [
        ('U60','SINK_W_EN','LED_W_K','W_ISET','R230','C230',825,750),
        ('U61','SINK_C_EN','LED_C_K','C_ISET','R231','C231',925,750)]:
        ic(ref,'CAT4101',[(1,'EN_PWM','input'),(2,'VIN','power_in'),(3,'GND_TAB','power_in'),(4,'RSET','passive'),(5,'LED','passive')],
           {1:en,2:'3V3',3:'GND',4:setnet,5:led},'Package_TO_SOT_SMD:TO-263-5_TabPin3',x,y,
           'CAT4101TV-T75','onsemi','https://www.onsemi.com/download/data-sheet/pdf/cat4101-d.pdf',
           'Nominal 200mA from manufacturer RSET table. Conservative simultaneous-channel budget; characterize pulse current on prototype.')
        r(rref,'2.49k',setnet,'GND',x,y+35)
        c(cref,'1u 10V','3V3','GND',x+45,y+35)

    # Series high-side cutoff removes LED energy if a current sink shorts.
    pins=[(1,'S','passive'),(2,'S','passive'),(3,'S','passive'),(4,'G','input'),(5,'D','passive'),(6,'D','passive'),(7,'D','passive'),(8,'D','passive')]
    ic('Q60','AO4407A',pins,{1:'BOOST_OUT',2:'BOOST_OUT',3:'BOOST_OUT',4:'LED_POWER_GATE',5:'LED_ANODES',6:'LED_ANODES',7:'LED_ANODES',8:'LED_ANODES'},
       'Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',55,860,'AO4407A','Alpha & Omega Semiconductor','https://www.aosmd.com/res/data_sheets/AO4407A.pdf')
    r('R232','4.7k','BOOST_OUT','LED_POWER_GATE',110,835)
    r('R233','2.2k','LED_POWER_GATE','LED_GATE_PULL',160,835)
    r('R234','2.2k','HW_WINDOW','LED_GATE_BASE',110,885)
    r('R235','100k','LED_GATE_BASE','GND',160,885)
    add('Q61','MMBT3904-7-F','Transistor_BJT:Q_NPN_BEC','Package_TO_SOT_SMD:SOT-23',
        {1:'LED_GATE_BASE',2:'GND',3:'LED_GATE_PULL'},210,860,mpn='MMBT3904-7-F',manufacturer='Diodes Incorporated',datasheet='https://www.diodes.com/datasheet/download/MMBT3904.pdf')
    add('D60','10V ZENER','Device:D_Zener','Diode_SMD:D_SOD-123',{1:'BOOST_OUT',2:'LED_POWER_GATE'},210,900,90,
        notes='Select 10V zener; cathode to PFET source. Gate transient and off-time verification pending.')
    add('J4','WARM COB','Connector_Generic:Conn_01x02','Connector_Wire:SolderWire-0.5sqmm_1x02_P4.6mm_D0.9mm_OD2.1mm',
        {1:'LED_ANODES',2:'LED_W_K'},110,935,notes='Offboard Bridgelux warm channel; wire polarity and heat spreader drawing required.')
    add('J5','COOL COB','Connector_Generic:Conn_01x02','Connector_Wire:SolderWire-0.5sqmm_1x02_P4.6mm_D0.9mm_OD2.1mm',
        {1:'LED_ANODES',2:'LED_C_K'},210,935,notes='Same physical bicolor COB as J4, cool channel. Do not count as a second emitter.')
    annotations.append(text('17 / PHYSICAL LED POWER CUTOFF - DEFAULT OFF',25,820,2))
    annotations.append(text('External COB: BXRV-TR-2765G-10A0-A-23, independent channels, bonded heat spreader.',25,970))

    # Delay hardware permission until both timer start-up sequences finish.
    ic('U54','TPS3808G33',[(1,'RESET_N','open_collector'),(2,'GND','power_in'),(3,'MR_N','input'),(4,'CT','input'),(5,'SENSE','input'),(6,'VDD','power_in')],
       {1:'POR_OK',2:'GND',3:'LOGIC_PG',4:None,5:'3V3',6:'3V3'},s6,825,860,
       'TPS3808G33DBVR','Texas Instruments',ti+'tps3808.pdf',
       'CT intentionally open for nominal 20ms release delay; MR follows regulator PG. 3.07V brownout threshold.')
    r('R236','10k','3V3','POR_OK',880,835)
    c('C236','100n','3V3','GND',930,835)

    # Ioff UART isolation avoids host-powered signals feeding an unpowered MCU.
    for ref,a,y,xp in [('U62','UART_RX_EXT','UART_RX',825),('U63','UART_TX','UART_TX_EXT',925)]:
        ic(ref,'SN74LVC1G125',[(1,'OE_N','input'),(2,'A','input'),(3,'GND','power_in'),(4,'Y','tri_state'),(5,'VDD','power_in')],
           {1:'UART_OE_N',2:a,3:'GND',4:y,5:'3V3'},s5,xp,930,
           'SN74LVC1G125DBVR','Texas Instruments',ti+'sn74lvc1g125.pdf')
        c('C'+str(100+int(ref[1:])),'100n','3V3','GND',xp,965)
    r('R237','10k','3V3','UART_OE_N',825,1005)
    r('R238','56k','POR_OK','UART_ENABLE_BASE',925,1005)
    add('Q62','MMBT3904-7-F','Transistor_BJT:Q_NPN_BEC','Package_TO_SOT_SMD:SOT-23',
        {1:'UART_ENABLE_BASE',2:'GND',3:'UART_OE_N'},825,1040,
        mpn='MMBT3904-7-F',manufacturer='Diodes Incorporated',datasheet='https://www.diodes.com/datasheet/download/MMBT3904.pdf')
    for part in d['parts']:
        if part['reference']=='TP3':part['nets']={'1':'UART_TX_EXT'};part['value']='UART_TX_EXT'
        if part['reference']=='TP4':part['nets']={'1':'UART_RX_EXT'};part['value']='UART_RX_EXT'
    annotations.append(text('19 / POWER-ON DELAY + Ioff UART ISOLATION',795,820,2))

    # Ready is sampled only at triggering. Loaded-bank UVLO remains independent.
    ic('U55','TLV3011B',[(1,'OUT','open_collector'),(2,'GND','power_in'),(3,'IN_PLUS','input'),(4,'IN_MINUS','input'),(5,'REF','output'),(6,'VDD','power_in')],
       {1:'CAP_READY',2:'GND',3:'CAP_READY_SENSE',4:'CAP_READY_REF',5:'CAP_READY_REF',6:'3V3'},s6,580,1065,
       'TLV3011BIDBVR','Texas Instruments',ti+'tlv3011.pdf',
       'Separate preflash readiness comparator. Do not AND CAP_READY into HW_WINDOW: normal pulse sag must not truncate an otherwise valid flash.')
    r('R239','261k','CAP_BANK','CAP_READY_SENSE',630,1040)
    r('R240','100k','CAP_READY_SENSE','GND',680,1040)
    r('R241','10M','CAP_READY','CAP_READY_SENSE',630,1090)
    r('R242','10k','3V3','CAP_READY',680,1090)
    c('C155','100n','3V3','GND',730,1090)
    gate('U56','08','CAP_READY','COOLDOWN_READY','ENERGY_REARM_OK',580,1130)
    annotations.append(text('20 / PRE-FLASH ENERGY QUALIFICATION',545,1010,2))
    annotations.append(text('Nominal cap-ready ~4.51V rising / 4.43V falling. Pulse sag is handled by U42 UVLO.',545,1165))
