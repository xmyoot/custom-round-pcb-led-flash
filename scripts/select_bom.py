"""Exact BOM candidates stored in schematic properties, never in a parallel BOM.

Manufacturer series coding is used for ordinary resistors. Distributor stock and
DC-bias qualification are independent checks; assigning an MPN does not pass them.
"""
from decimal import Decimal

def enrich(d):
    for p in d['parts']:
        ref=p['reference'];v=p['value'];fp=p['footprint']
        if ref=='R276':p['footprint']=fp='Resistor_SMD:R_0805_2012Metric'
        if ref=='C275':p['footprint']=fp='Capacitor_SMD:C_0805_2012Metric'
        if p['libid']=='Device:R' and not p['MPN'] and ref!='R270':
            token=v.split()[0]
            suffix='R'
            if token[-1:] in ('k','M'):
                suffix=token[-1].upper();token=token[:-1]
            txt=format(Decimal(token).normalize(),'f')
            code=txt.replace('.',suffix) if '.' in txt else txt+suffix
            size='2010' if '2010' in fp else ('0805' if '0805' in fp else '0603')
            series='RC'+size+('FK-07' if size=='2010' else 'FR-07')
            p['MPN']=series+code+'L';p['Manufacturer']='Yageo'
            p['Notes']+=' 1% general-purpose resistor; individual sourcing and series-code audit pending.'
        if p['libid']=='Device:C' and not p['MPN']:
            token=v.split()[0];size=fp.split(':')[-1]
            candidates={
                ('100n','C_0603_1608Metric'):'GRM188R71H104KA93D',
                ('1u','C_0603_1608Metric'):'GRM188R61C105KA12D',
                ('10n','C_0603_1608Metric'):'GRM188R71H103KA01D',
                ('33n','C_0603_1608Metric'):'GRM188R71H333KA61D',
                ('47p','C_0603_1608Metric'):'GRM1885C1H470JA01D',
                ('100p','C_0603_1608Metric'):'GRM1885C1H101JA01D',
                ('10u','C_0805_2012Metric'):'GRM21BR61C106KE15L',
                ('22u','C_0805_2012Metric'):'GRM21BR61C226ME44L',
                ('4.7u','C_0805_2012Metric'):'GRM21BR71E475KA73L',
                ('2.2u','C_0805_2012Metric'):'GRM21BR71C225KA12L',
                ('1u','C_0805_2012Metric'):'GRM21BR71H105KA12L',
                ('22u','C_1206_3216Metric'):'GRM31CR61C226KE15L',
                ('10u','C_1210_3225Metric'):'GRM32ER71H106KA12L',
            }
            if (token,size) in candidates:
                p['MPN']=candidates[token,size];p['Manufacturer']='Murata'
                p['Datasheet']='https://www.murata.com/en-global/api/pdfdownloadapi?cate=luCeramicCapacitorsSMD&partno='+p['MPN']
                p['Notes']+=' Exact nominal/package selection; effective capacitance and source verification pending.'
    updates={
        'R270':('WSLP0805R0100FEA','Vishay','https://www.vishay.com/docs/30122/wslp.pdf'),
        'R271':('TNPW0603162KBEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'R272':('TNPW060310K0BEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'R143':('TNPW0603147KBEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'R153':('TNPW060310K0BEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'R239':('TNPW0603261KBEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'R240':('TNPW0603100KBEEA','Vishay','https://www.vishay.com/docs/28758/tnpw_e3.pdf'),
        'D60':('BZT52C10-7-F','Diodes Incorporated','https://www.diodes.com/datasheet/download/BZT52Cxx.pdf'),
        'D70':('BAV21W-7-F','Diodes Incorporated','https://www.diodes.com/datasheet/download/BAV19W-BAV21W.pdf'),
        'D1':('LTST-C190KRKT','Lite-On','https://optoelectronics.liteon.com/upload/download/DS-22-99-0178/LTST-C190KRKT.pdf'),
        'D2':('LTST-C190KFKT','Lite-On','https://optoelectronics.liteon.com/upload/download/DS-22-99-0186/LTST-C190KFKT.PDF'),
        'D3':('LTST-C190KGKT','Lite-On',''),
        'TH1':('NTCG163JF103FT1','TDK','https://product.tdk.com/system/files/dam/doc/product/sensor/ntc/chip-ntc-thermistor/data_sheet/datasheet_ntcg163jf103ft1.pdf'),
    }
    for p in d['parts']:
        ref=p['reference']
        if ref in updates:
            p['MPN'],p['Manufacturer'],p['Datasheet']=updates[ref]
        if ref=='D2':p['value']='AMBER BLE'
        if ref=='R276':p['footprint']='Resistor_SMD:R_0805_2012Metric'
        if ref in ('R271','R272','R143','R153','R239','R240'):
            p['Notes']='0.1% 25ppm/C precision divider; verify orderable MPN. Tight ratios preserve boost-ready margin.'
        if ref in ('J4','J5'):p['in_bom']=False

    # External assembly items appear once in the same schematic BOM.
    d['ic']('LED1','Vesta_Tunable_COB',[(1,'W_PLUS','passive'),(2,'W_MINUS','passive'),(3,'C_PLUS','passive'),(4,'C_MINUS','passive')],
            {1:'LED_ANODES',2:'LED_W_K',3:'LED_ANODES',4:'LED_C_K'},'',1080,750,
            'BXRV-TR-2765G-10A0-A-23','Bridgelux','https://www.bridgelux.com/sites/default/files/DS350.pdf',
            'OFFBOARD assembly item: 2700/6500K, 15.8mm square, separate warm/cool terminals; mount on electrically isolated heat spreader.')
    d['parts'][-1]['on_board']=False
    d['add']('TH2','10k CELL NTC','Device:Thermistor_NTC','',{1:'PACK_TEMP',2:'GND'},1080,550,
             mpn='B57861S0103F040',manufacturer='TDK',
             datasheet='https://product.tdk.com/system/files/dam/doc/product/sensor/ntc/ntc_element/data_sheet/50/db/ntc/ntc_mini_sensors_s861.pdf',
             notes='OFFBOARD assembly item bonded to cell; connect through J3. 10k 1%, B25/100=3988K 1%.',on_board=False)
