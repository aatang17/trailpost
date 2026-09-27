import math,os,subprocess,concurrent.futures as cf
z=17;n=2**z
def tx(lon):return int((lon+180)/360*n)
def ty(lat):return int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*n)
x0,x1=tx(113.883),tx(113.997);y0,y1=ty(22.292),ty(22.224)
jobs=[(x,y) for x in range(x0,x1+1) for y in range(y0,y1+1)]
print('tiles',len(jobs),x0,x1,y0,y1)
def get(t):
    x,y=t;f=f'img/{z}/{x}_{y}.png'
    if os.path.exists(f) and os.path.getsize(f)>500: return 0
    for _ in range(3):
        r=subprocess.run(['curl','-s','-m','40','-o',f,'-w','%{http_code}',f'https://mapapi.geodata.gov.hk/gs/api/v1.0.0/xyz/imagery/WGS84/{z}/{x}/{y}.png'],capture_output=True,text=True)
        if r.stdout=='200': return 0
    return 1
with cf.ThreadPoolExecutor(12) as ex: fails=sum(ex.map(get,jobs))
print('fails',fails)
open('img/range.txt','w').write(f'{z} {x0} {x1} {y0} {y1}')
