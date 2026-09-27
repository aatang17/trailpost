import math,os,subprocess,concurrent.futures as cf
def tiles(z,lon0,lon1,lat0,lat1):
    n=2**z;tx=lambda lon:int((lon+180)/360*n);ty=lambda lat:int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
    return tx(lon0),tx(lon1),ty(lat1),ty(lat0)
L=(113.50,114.07,22.08,22.38)
jobs=[]
x0,x1,y0,y1=tiles(13,*L);open('far/img_range.txt','w').write(f'13 {x0} {x1} {y0} {y1}')
os.makedirs('far/img',exist_ok=True);os.makedirs('far/ter',exist_ok=True)
for x in range(x0,x1+1):
    for y in range(y0,y1+1): jobs.append((f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/13/{x}/{y}.png',f'far/img/{x}_{y}.png'))
tx0,tx1,ty0,ty1=tiles(12,*L);open('far/ter_range.txt','w').write(f'12 {tx0} {tx1} {ty0} {ty1}')
for x in range(tx0,tx1+1):
    for y in range(ty0,ty1+1): jobs.append((f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/12/{x}/{y}.png',f'far/ter/{x}_{y}.png'))
def get(j):
    u,f=j
    if os.path.exists(f) and os.path.getsize(f)>200:return 0
    for _ in range(3):
        r=subprocess.run(['curl','-s','-m','40','-o',f,'-w','%{http_code}',u],capture_output=True,text=True)
        if r.stdout=='200':return 0
    return 1
with cf.ThreadPoolExecutor(10) as ex: print(len(jobs),'fails',sum(ex.map(get,jobs)))
