import math,os,subprocess,concurrent.futures as cf
z=15;n=2**z
def tx(lon):return int((lon+180)/360*n)
def ty(lat):return int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
x0,x1=tx(113.880),tx(114.000);y0,y1=ty(22.295),ty(22.221)
U='https://tiles.arcgis.com/tiles/6j1KwZfY2fZrfNMR/arcgis/rest/services'
jobs=[(s,x,y) for s in ('DSM','DTM') for x in range(x0,x1+1) for y in range(y0,y1+1)]
os.makedirs('tiles',exist_ok=True)
def get(j):
    s,x,y=j;f=f'tiles/{s}_{x}_{y}.lerc'
    if os.path.exists(f) and os.path.getsize(f)>100:return 0
    for _ in range(3):
        r=subprocess.run(['curl','-s','-m','40','-o',f,'-w','%{http_code}',f'{U}/{s}_2020_5m_WEL/ImageServer/tile/{z}/{y}/{x}'],capture_output=True,text=True)
        if r.stdout=='200':return 0
        if r.stdout=='404':
            open(f,'wb').close();return 0
    return 1
with cf.ThreadPoolExecutor(10) as ex: fails=sum(ex.map(get,jobs))
open('range.txt','w').write(f'{z} {x0} {x1} {y0} {y1}');print(len(jobs),'fails',fails)
