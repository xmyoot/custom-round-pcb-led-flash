"""Fetch explicit BOM manufacturer URLs; record gaps instead of substitutions."""
from pathlib import Path
import concurrent.futures,hashlib,json,re,urllib.request
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'analysis/draft_connectivity.json').read_text())
old=json.loads((ROOT/'datasheets/sources.json').read_text())
aliases={v['url']:v['file'] for v in old.values() if v.get('status')=='downloaded'}
aliases['https://www.toppwr.com/uploadfile/file/20230304/640301eae1260.pdf']='TP4056.pdf'
parts={p['MPN']:p for p in data['parts'] if p['MPN']}
def fetch(item):
 mpn,part=item;url=part['Datasheet'];out=ROOT/'datasheets'/(aliases.get(url) or re.sub(r'[^A-Za-z0-9_.-]','_',mpn)+'.pdf')
 entry={'mpn':mpn,'manufacturer':part['Manufacturer'],'url':url}
 try:
  if not url:raise ValueError('No direct manufacturer datasheet URL assigned')
  if not out.exists() or not out.read_bytes().startswith(b'%PDF'):
   request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
   payload=urllib.request.urlopen(request,timeout=15).read()
   if not payload.startswith(b'%PDF'):raise ValueError('Manufacturer response is not a PDF')
   out.write_bytes(payload)
  payload=out.read_bytes()
  entry.update(file=out.name,sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),status='downloaded')
 except Exception as e:entry.update(status='failed',reason=str(e))
 return mpn,entry
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 results=dict(pool.map(fetch,parts.items()))
(ROOT/'datasheets/selected_sources.json').write_text(json.dumps(results,indent=2))
print('Selected PDFs:',sum(x['status']=='downloaded' for x in results.values()),'/',len(results))
for mpn,x in results.items():
 if x['status']!='downloaded':print(mpn,x['reason'])
