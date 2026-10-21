"""Download manufacturer evidence, never substitute HTML for a PDF."""
from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'Bridgelux_DS350': 'https://www.bridgelux.com/sites/default/files/DS350.pdf',
    'Eaton_HV': 'https://www.eaton.com/content/dam/eaton/products/electronic-components/resources/data-sheet/eaton-hv-supercapacitors-cylindrical-cells-data-sheet.pdf',
    'MP3435': 'https://www.monolithicpower.cn/cn/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP3435GL/',
    'CAT4101': 'https://www.onsemi.com/download/data-sheet/pdf/cat4101-d.pdf',
    'TPS63070': 'https://www.ti.com/lit/ds/symlink/tps63070.pdf',
    'TLVH431': 'https://www.ti.com/lit/ds/symlink/tlvh431.pdf',
    'ESP32-C3-WROOM-02': 'https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf',
    'USB4085': 'https://gct.co/files/drawings/usb4085.pdf',
    'SN74LVC1G123': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g123.pdf',
    'SN74LVC1G74': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf',
    'LTC6993': 'https://www.analog.com/media/en/technical-documentation/data-sheets/ltc6993-6993-1-6993-2-6993-3-6993-4.pdf',
    'TPS3808': 'https://www.ti.com/lit/ds/symlink/tps3808.pdf',
    'TP4056': 'https://www.toppwr.com/uploadfile/file/20230304/640301eae1260.pdf',
    'DW01A': 'https://hmsemi.com/downfile/DW01A.PDF',
    'TUSB320LAI': 'https://www.ti.com/lit/ds/symlink/tusb320lai.pdf',
    'AO3401A': 'https://www.aosmd.com/res/data_sheets/AO3401A.pdf',
    '2N7002': 'https://www.diodes.com/datasheet/download/2N7002.pdf',
    'XFL4020': 'https://www.coilcraft.com/getmedia/50632d43-da1b-4cdb-8ab4-3029cab51df3/xfl4020.pdf',
    'LTC3225': 'https://www.analog.com/media/en/technical-documentation/data-sheets/3225fb.pdf',
    'MMBT3904': 'https://www.diodes.com/datasheet/download/MMBT3904.pdf',
    'TLV760': 'https://www.ti.com/lit/ds/symlink/tlv760.pdf',
    'TLV3011': 'https://www.ti.com/lit/ds/symlink/tlv3011.pdf',
    'SN74LVC1G04': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g04.pdf',
    'SN74LVC1G125': 'https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf',
    'AO4407A': 'https://www.aosmd.com/res/data_sheets/AO4407A.pdf',
    'TPS25200': 'https://www.ti.com/lit/ds/symlink/tps25200.pdf',
}

def fetch(item):
    name, url = item
    out = ROOT / 'datasheets' / (name + '.pdf')
    try:
        if not out.exists():
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            data = urllib.request.urlopen(req, timeout=45).read()
            if not data.startswith(b'%PDF'):
                raise ValueError('Server did not return a PDF')
            out.write_bytes(data)
        data = out.read_bytes()
        return name, dict(url=url, file=out.name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data), status='downloaded')
    except Exception as e:
        return name, dict(url=url, status='failed', reason=str(e))

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',nargs='+',choices=list(SOURCES))
    args=parser.parse_args()
    (ROOT/'datasheets').mkdir(exist_ok=True)
    previous=ROOT/'datasheets'/'sources.json'
    manifest=json.loads(previous.read_text()) if previous.exists() else {}
    selected={k:v for k,v in SOURCES.items() if not args.only or k in args.only}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        manifest.update(dict(pool.map(fetch, selected.items())))
    (ROOT/'datasheets'/'sources.json').write_text(json.dumps(manifest, indent=2))
    for name, info in manifest.items():
        print(name, info['status'], info.get('bytes', info.get('reason')))
