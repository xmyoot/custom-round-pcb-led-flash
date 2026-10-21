"""MP3435 energy stage; control-loop and transient qualification remain open."""

def populate(d):
    add,ic,r,c,text,annotations=(d[k] for k in ('add','ic','r','c','text','annotations'))
    ds='https://www.monolithicpower.cn/cn/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP3435GL/'
    pins=[(1,'OUT','passive'),(2,'OUT','passive'),(3,'TM','passive'),(4,'BST','passive'),(5,'SOUT','input'),(6,'EN','input'),(7,'GATE','output'),(8,'SENSE','input'),(9,'SW','passive'),(10,'PGND','power_in'),(11,'IN','power_in'),(12,'VDD','power_out'),(13,'COMP','passive'),(14,'FB','input'),(15,'SS','passive'),(16,'AGND','power_in'),(17,'PGND','power_in'),(18,'PGND','power_in'),(19,'PGND','power_in'),(20,'SW','passive')]
    ic('U70','MP3435',pins,{1:'BOOST_OUT',2:'BOOST_OUT',3:None,4:'BOOST_BST',5:'BOOST_OUT',6:'BOOST_EN',7:'BOOST_INPUT_GATE',8:'BOOST_SENSE',9:'BOOST_SW',10:'GND',11:'CAP_FUSED',12:'BOOST_VDD',13:'BOOST_COMP',14:'BOOST_FB',15:'BOOST_SS',16:'GND',17:'GND',18:'GND',19:'GND',20:'BOOST_SW'},
       'Round_LED_Flash:MP3435_QFN20_3x4',335,860,'MP3435GL-Z','Monolithic Power Systems',ds,
       '21.07V nominal. Kelvin IN/SENSE; compensation must be qualified for actual effective Cout and load steps.')
    add('F2','7A FAST','Device:Fuse','Fuse:Fuse_Littelfuse-NANO2-451_453',{1:'CAP_BANK',2:'CAP_FUSED'},390,835,90,
        mpn='0451007.MRL',manufacturer='Littelfuse',notes='Cap bank branch fuse; verify actual capacitor fault current and repetitive pulse I2t.')
    r('R270','0.010 0.5W','CAP_FUSED','BOOST_SENSE',440,835,fp='Resistor_SMD:R_0805_2012Metric',
      notes='Metal-element 0.5W 1% shunt; maximum steady current-limit dissipation 0.397W before tolerance. Fault pulses are time-limited by converter.')
    # Stock PowerPAK land pattern represents the continuous drain with pad 5.
    pins=[(1,'S','passive'),(2,'S','passive'),(3,'S','passive'),(4,'G','input'),(5,'D_5_6_7_8','passive')]
    ic('Q70','SiR800DP',pins,{1:'BOOST_INPUT',2:'BOOST_INPUT',3:'BOOST_INPUT',4:'BOOST_INPUT_GATE',5:'BOOST_SENSE'},
       'Package_SO:PowerPAK_SO-8_Single',440,885,'SiR800DP-T1-GE3','Vishay','https://www.vishay.com/docs/65738/sir800dp.pdf',
       'Input disconnect per MPS reference; check linear startup SOA and reverse VGS with D70.')
    add('D70','GATE CLAMP','Device:D','Diode_SMD:D_SOD-123',{1:'BOOST_INPUT_GATE',2:'BOOST_INPUT'},490,885,90,
        notes='Low-leakage silicon diode anode at source, cathode at gate; select MPN and check MPS figure4 orientation.')
    add('L2','1.5uH','Device:L','Inductor_SMD:L_Coilcraft_XAL7030-152',{1:'BOOST_INPUT',2:'BOOST_SW'},490,835,90,
        mpn='XAL7030-152MEC',manufacturer='Coilcraft',datasheet='https://www.coilcraft.com/getmedia/0d05a05e-d55d-4a0c-911d-46bd73686633/xal7030.pdf')
    for ref,x,y in [('C270',390,925),('C271',440,925),('C272',490,925)]:
        c(ref,'22u 10V','CAP_FUSED','GND',x,y,fp='Capacitor_SMD:C_1206_3216Metric')
    c('C273','100n','CAP_FUSED','GND',390,950)
    c('C274','100n 50V','BOOST_BST','BOOST_SW',440,950)
    c('C275','2.2u 10V','BOOST_VDD','GND',490,950)
    c('C276','10n','BOOST_SS','GND',390,975)
    r('R271','162k','BOOST_OUT','BOOST_FB',580,835)
    r('R272','10k','BOOST_FB','GND',630,835)
    r('R273','1k','BOOST_REQUEST','BOOST_EN',680,835)
    r('R274','100k','BOOST_EN','GND',730,835)
    # Conservative starting compensation, not copied unmodified from 12V circuit.
    # RHP zero ~84kHz at 3.3V/0.66A/1.5uH; target crossover about 1kHz.
    c('C277','33n','BOOST_COMP','BOOST_COMP_R',580,885)
    r('R275','120k','BOOST_COMP_R','GND',630,885,
      notes='Engineering starting value only. Measure/validate Bode margin and short flash load response before release.')
    c('C278','47p','BOOST_COMP','GND',680,885)
    for ref,x in [('C280',580),('C281',630),('C282',680)]:
        c(ref,'10u 50V','BOOST_OUT','GND',x,930,fp='Capacitor_SMD:C_1210_3225Metric',
          notes='Choose DC-bias-characterized MLCC; total effective ceramic output capacitance >=15uF.')
    c('C283','100n 50V','BOOST_OUT','GND',730,930)
    add('C284','120u 35V','Device:C_Polarized','Capacitor_SMD:CP_Elec_10x12.6',{1:'BOOST_OUT',2:'GND'},730,885,90,
        mpn='35SVPF120M',manufacturer='Panasonic',datasheet='https://industrial.panasonic.com/cdbs/www-data/pdf/AAB8000/AAB8000COL87.pdf',
        notes='Polymer output reservoir; independent package, ESR, ripple and loop-stability verification pending.')
    r('R276','22k 0.125W','BOOST_OUT','GND',580,975,
      notes='Discharges output reservoir; about 10s to 0.5V at 120uF nominal. Not on switched LED rail.')
    annotations.append(text('18 / 21.07 V BOOST + INPUT DISCONNECT / CURRENT LIMIT',285,820,2))
    annotations.append(text('Output reservoir is BEFORE physical cutoff. Never add bulk capacitance on LED_ANODES.',285,1010))
