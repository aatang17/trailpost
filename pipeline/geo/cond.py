import json,datetime
def L(f): return json.load(open(f))
ws=L('hko_warnsum.json');wi=L('hko_warningInfo.json');wit=L('hko_warningInfo_tc.json')
rh=L('hko_rhrread.json');fe=L('hko_fnd.json');ft=L('hko_fnd_tc.json');le=L('hko_flw.json');lt=L('hko_flw_tc.json')
warn=[]
for k,v in ws.items():
    code=v.get('code') or k
    if v.get('actionCode')=='CANCEL': continue
    warn.append(code)
det_en=[' '.join(d.get('contents',[])) for d in wi.get('details',[])]
det_zh=[' '.join(d.get('contents',[])) for d in wit.get('details',[])]
temps={x['place']:x['value'] for x in rh['temperature']['data']}
uv=None
try: uv=rh['uvindex']['data'][0]['value']
except Exception: pass
fc=[]
for a,b in zip(fe['weatherForecast'][:3],ft['weatherForecast'][:3]):
    fc.append({'date':a['forecastDate'],'max':a['forecastMaxtemp']['value'],'min':a['forecastMintemp']['value'],'rhmax':a['forecastMaxrh']['value'],'psr':a['PSR'],'wx_en':a['forecastWeather'],'wx_zh':b['forecastWeather'],'wind_en':a['forecastWind'],'wind_zh':b['forecastWind']})
out={'fetchedAt':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='minutes'),
 'obsTime':rh['updateTime'],'warnings':warn,'detail_en':det_en,'detail_zh':det_zh,
 'temps':temps,'humidity':rh['humidity']['data'][0]['value'],'uv':uv,
 'today_en':le['forecastDesc'],'today_zh':lt['forecastDesc'],'outlook_en':le.get('outlook',''),'outlook_zh':lt.get('outlook',''),
 'situation_en':fe['generalSituation'],'situation_zh':ft['generalSituation'],'forecast':fc,'source':'Hong Kong Observatory open data'}
json.dump(out,open('conditions.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False)[:1500])
