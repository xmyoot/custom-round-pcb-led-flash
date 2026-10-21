"""Power input, charging and protection blocks for the authoritative schematic.

Called by build_schematic; functions use its symbol/part registry. Package and
release checks are intentionally tracked separately from drafting connectivity.
"""

def populate(d):
    add,ic,r,c,text,annotations=(d[k] for k in ('add','ic','r','c','text','annotations'))
    sot='Package_TO_SOT_SMD:SOT-23'
    s6='Package_TO_SOT_SMD:SOT-23-6'
    ti='https://www.ti.com/lit/ds/symlink/'
    def npn(ref,base,collector,x,y):
        add(ref,'MMBT3904-7-F','Transistor_BJT:Q_NPN_BEC',sot,{1:base,2:'GND',3:collector},x,y,
            mpn='MMBT3904-7-F',manufacturer='Diodes Incorporated',datasheet='https://www.diodes.com/datasheet/download/MMBT3904.pdf')
    def nfet(ref,gate,source,drain,x,y):
        add(ref,'AO3400A','Transistor_FET:Q_NMOS_GSD',sot,{1:gate,2:source,3:drain},x,y,
            mpn='AO3400A',manufacturer='Alpha & Omega Semiconductor',datasheet='https://www.aosmd.com/res/data_sheets/AO3400A.pdf')

    # Protected negative is system GND, never tied directly to raw cell negative.
    ic('U1','DW01A',[(1,'OD','output'),(2,'CS','input'),(3,'OC','output'),(4,'TD','input'),(5,'VCC','power_in'),(6,'VSS','power_in')],
       {1:'CELL_OD',2:'CELL_CS',3:'CELL_OC',4:None,5:'CELL_IC_VCC',6:'CELL_N_RAW'},s6,825,60,
       'DW01A','HM Semiconductor','https://hmsemi.com/downfile/DW01A.PDF',
       'Procure the HM-specified variant; mixed-vendor DW01 substitutions require threshold review.')
    r('R1','100','BAT_PROT','CELL_IC_VCC',880,45)
    c('C1','100n','CELL_IC_VCC','CELL_N_RAW',930,45)
    r('R2','1k','GND','CELL_CS',880,70)
    nfet('Q1','CELL_OD','CELL_N_RAW','CELL_FET_COMMON',825,110)
    nfet('Q2','CELL_OC','GND','CELL_FET_COMMON',880,110)
    add('F1','2A FAST','Device:Fuse','Fuse:Fuse_Littelfuse-NANO2-451_453',{1:'CELL_P',2:'BAT_PROT'},930,110,90,
        mpn='0451002.MRL',manufacturer='Littelfuse',notes='Fuse interruption rating versus actual cell fault current remains a release gate.')
    npn('Q3','USB_INHIBIT_BASE','SYS_EN',980,110)
    r('R3','47k','VBUS_RAW','USB_INHIBIT_BASE',980,70)
    ic('U9','TPS3808G30',[(1,'RESET_N','open_collector'),(2,'GND','power_in'),(3,'MR_N','input'),(4,'CT','input'),(5,'SENSE','input'),(6,'VDD','power_in')],
       {1:'SYS_EN',2:'GND',3:'BAT_PROT',4:None,5:'BAT_PROT',6:'BAT_PROT'},s6,1080,240,
       'TPS3808G30DBVR','Texas Instruments',ti+'tps3808.pdf',
       'Independent 2.79V system undervoltage cutoff, before emergency DW01 overdischarge. CT open gives nominal 20ms release delay.')
    c('C9','100n','BAT_PROT','GND',1080,290)
    annotations.append(text('09 / CELL FUSE + DW01 LOW-SIDE PROTECTION',795,25,2))
    annotations.append(text('Raw negative is isolated from all USB, fixture and enclosure grounds.',795,155))

    # Independent USB logic supply, alive with the system switched off.
    ic('U2','TLV76033',[(1,'OUT','power_out'),(2,'IN','power_in'),(3,'GND','power_in')],
       {1:'USB_3V3',2:'VBUS_RAW',3:'GND'},sot,825,240,'TLV76033DBZR','Texas Instruments',ti+'tlv760.pdf')
    c('C2','1u 50V','VBUS_RAW','GND',880,220,fp='Capacitor_SMD:C_0805_2012Metric')
    c('C3','1u 10V','USB_3V3','GND',930,220)
    add('D6','SMF4L6.0A','Device:D_TVS','Diode_SMD:D_SOD-123F',{1:'VBUS_RAW',2:'GND'},1030,220,90,
        mpn='SMF4L6.0A',manufacturer='Littelfuse',
        datasheet='https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smf_datasheet.pdf.pdf',
        notes='6V standoff input transient clamp; place at receptacle. Not protection from a sustained non-compliant supply.')
    pins=[(1,'CC1','bidirectional'),(2,'CC2','bidirectional'),(3,'PORT','input'),(4,'VBUS_DET','input'),(5,'ADDR','input'),(6,'OUT3','open_collector'),(7,'OUT1','open_collector'),(8,'OUT2','open_collector'),(9,'ID','open_collector'),(10,'GND','power_in'),(11,'EN_N','input'),(12,'VDD','power_in')]
    ic('U3','TUSB320LAI',pins,{1:'CC1',2:'CC2',3:'GND',4:'CC_VBUS_DET',5:None,6:None,7:'CC_CURRENT_N',8:None,9:None,10:'GND',11:'GND',12:'USB_3V3'},
       'Package_DFN_QFN:Texas_X2QFN-12_1.6x1.6mm_P0.4mm',825,310,'TUSB320LAIRWBR','Texas Instruments',ti+'tusb320lai.pdf',
       'GPIO UFP mode: OUT1 low only for 1.5A/3A advertisement. Internal Rd; do not fit external Rd.')
    r('R4','887k','VBUS_RAW','CC_VBUS_DET',880,260)
    r('R5','10k','USB_3V3','CC_CURRENT_N',930,260)
    c('C4','100n','USB_3V3','GND',980,260)
    ic('U4','SN74LVC1G04',[(1,'NC','no_connect'),(2,'A','input'),(3,'GND','power_in'),(4,'Y','output'),(5,'VCC','power_in')],
       {1:None,2:'CC_CURRENT_N',3:'GND',4:'CC_ALLOWED',5:'USB_3V3'},'Package_TO_SOT_SMD:SOT-23-5',930,310,
       'SN74LVC1G04DBVR','Texas Instruments',ti+'sn74lvc1g04.pdf')
    c('C5','100n','USB_3V3','GND',980,310)
    r('R16','22','CC1_RAW','CC1',880,380,notes='Series damping after connector-side TVS; adds 0.43% to nominal 5.1k Rd path.')
    r('R17','22','CC2_RAW','CC2',980,380,notes='Series damping after connector-side TVS; adds 0.43% to nominal 5.1k Rd path.')
    for ref,cc,x in [('D4','CC1_RAW',880),('D5','CC2_RAW',980)]:
        add(ref,'PESD5V0S1BA','Device:D_TVS','Diode_SMD:D_SOD-323',{1:'GND',2:cc},x,355,90,
            mpn='PESD5V0S1BA,115',manufacturer='Nexperia',datasheet='https://assets.nexperia.com/documents/data-sheet/PESD5V0S1BA.pdf',
            notes='Bidirectional ESD device; comma is part of the orderable MPN, not a second part.')
    annotations.append(text('10 / TYPE-C SOURCE QUALIFICATION - CHARGING ONLY',795,195,2))
    annotations.append(text('Default-current and legacy USB sources do not charge this implementation.',795,395))

    # Protected VBUS powers the charger. CC and sensor health qualify EN/CE.
    pins=[(1,'OUT','power_out'),(2,'ILIM','passive'),(3,'FAULT_N','open_collector'),(4,'EN','input'),(5,'GND','power_in'),(6,'IN','power_in'),(7,'EP','power_in')]
    ic('U5','TPS25200',pins,{1:'USB_5V',2:'USB_ILIM',3:None,4:'CC_ALLOWED',5:'GND',6:'VBUS_RAW',7:'GND'},
       'Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm',335,485,'TPS25200DRVR','Texas Instruments',ti+'tps25200.pdf')
    r('R6','150k','USB_ILIM','GND',390,455)
    r('R7','10k','CC_ALLOWED','CHARGE_ALLOWED',440,455)
    r('R8','100k','CHARGE_ALLOWED','GND',490,455)
    c('C6','4.7u 16V','USB_5V','GND',390,485,fp='Capacitor_SMD:C_0805_2012Metric')
    c('C7','100n 50V','VBUS_RAW','GND',490,485)
    pins=[(1,'TEMP','input'),(2,'PROG','passive'),(3,'GND','power_in'),(4,'VCC','power_in'),(5,'BAT','passive'),(6,'STDBY_N','open_collector'),(7,'CHRG_N','open_collector'),(8,'CE','input'),(9,'EP','power_in')]
    ic('U7','TP4056',pins,{1:'PACK_TEMP',2:'CHARGE_PROG',3:'GND',4:'USB_5V',5:'BAT_PROT',6:None,7:'CHRG_N',8:'CHARGE_ALLOWED',9:'GND'},
       'Round_LED_Flash:TP4056_TopPower_ESOP8',335,550,
       'TP4056-42-ESOP8','NanJing Top Power ASIC','https://www.toppwr.com/uploadfile/file/20230304/640301eae1260.pdf',
       '300mA nominal. Project EP dimensions transcribed from TopPower package drawing page14; independent check remains.')
    r('R9','4.02k','CHARGE_PROG','GND',390,535)
    c('C8','10u 10V','BAT_PROT','GND',440,535,fp='Capacitor_SMD:C_0805_2012Metric')
    r('R15','2.2k','USB_5V','CHG_LED_A',390,570)
    add('D1','RED','Device:LED','LED_SMD:LED_0603_1608Metric',{1:'CHRG_N',2:'CHG_LED_A'},440,570,
        notes='Exact LED MPN pending.')
    annotations.append(text('11 / PROTECTED VBUS + 300 mA CELL CHARGER',285,415,2))
    annotations.append(text('Charging disables logic and cap recharge in hardware. Ground is protected pack negative.',285,605))

    # Pack NTC is physically bonded to the cell. LED-area TH1 is independent.
    ic('J3','Pack_NTC_GH',[(1,'NTC','passive'),(2,'GND','passive'),('MP','MOUNT','passive')],
       {1:'PACK_TEMP',2:'GND','MP':'GND'},'Connector_JST:JST_GH_BM02B-GHS-TBT_1x02-1MP_P1.25mm_Vertical',580,485,
       'BM02B-GHS-TBT(LF)(SN)','JST','https://www.jst-mfg.com/product/pdf/eng/eGH.pdf',
       'Different mating series from battery PH prevents connector interchange. Remote isolated TDK 10k sensor bonded to cell, through GHR-02V-S housing.')
    r('R80','6.49k','USB_5V','PACK_TEMP',630,455,
      notes='Nominal beta-model temperature band about 5 to 40C; full R/T and threshold tolerances must be checked.')
    r('R81','1M','PACK_TEMP','PACK_TEMP_HALF',680,455)
    r('R82','1M','PACK_TEMP_HALF','GND',730,455)
    r('R83','100k','TEMP_REF','TEMP_REF_HALF',630,555)
    r('R84','100k','TEMP_REF_HALF','GND',680,555)
    ic('U8','TLV3011B',[(1,'OUT','open_collector'),(2,'GND','power_in'),(3,'IN_PLUS','input'),(4,'IN_MINUS','input'),(5,'REF','output'),(6,'VDD','power_in')],
       {1:'CHARGE_ALLOWED',2:'GND',3:'PACK_TEMP_HALF',4:'TEMP_REF_HALF',5:'TEMP_REF',6:'USB_3V3'},s6,680,505,
       'TLV3011BIDBVR','Texas Instruments',ti+'tlv3011.pdf',
       'Independent shorted-NTC inhibit, because TP4056 TEMP tied low disables internal monitoring.')
    c('C80','100n','USB_3V3','GND',730,535)
    annotations.append(text('12 / CELL NTC + SHORTED-SENSOR INHIBIT',545,435,2))
    annotations.append(text('Open sensor inhibits through TP4056; short inhibits through U8. Check startup and thresholds.',545,605))

    # Discharge the bank by default when the regulated logic power-good is low.
    nfet('Q34','CAP_DUMP_GATE','GND','CAP_DUMP_DRAIN',825,485)
    r('R70','100k','CAP_BANK','CAP_DUMP_GATE',880,455)
    npn('Q35','CAP_DUMP_BASE','CAP_DUMP_GATE',880,505)
    r('R71','100k','LOGIC_PG','CAP_DUMP_BASE',930,455)
    for ref,x in [('R72',930),('R73',980)]:
        r(ref,'100 0.5W','CAP_BANK','CAP_DUMP_DRAIN',x,505,fp='Resistor_SMD:R_2010_5025Metric',
          notes='Parallel 50ohm active dump, 0.48W initial total at 4.9V. Slows near MOSFET threshold; R74 provides final bleed.')
    r('R74','330 0.25W','CAP_BANK','GND',1030,505,fp='Resistor_SMD:R_1206_3216Metric',
      notes='Permanent bleeder: 73mW maximum at 4.9V. Conservative RC model below 0.5V within 60min; always measure TP7 before service.')
    for ref,net,x in [('TP7','CAP_BANK',930),('TP8','CAP_MID',980)]:
        add(ref,net,'Connector:TestPoint','TestPoint:TestPoint_Pad_D1.5mm',{1:net},x,555,
            notes='Stored energy test access; verify safe voltage before service.')
    annotations.append(text('13 / DEFAULT-ON CAPACITOR SERVICE DISCHARGE',795,435,2))
    annotations.append(text('Active dump removes most energy; permanent 330ohm bleed provides final discharge. Measure TP7 before service.',795,605))

    # These declare externally supplied rails after passive protection elements.
    # They do not override electrical or voltage-domain verification.
    for i,net in enumerate(['BAT_PROT','VBUS_RAW','CELL_IC_VCC','CELL_N_RAW','GND','CAP_FUSED']):
        add('#FLG'+str(i+1),'PWR_FLAG','power:PWR_FLAG','',{1:net},1050,45+25*i,on_board=False,
            notes='External connector/cell or passive-filtered power source.')
        d['parts'][-1]['in_bom']=False
