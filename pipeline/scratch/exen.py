import re,html,sys
n=sys.argv[1]
t=open(f'afcd_en/{n}.html',encoding='utf8').read()
t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>','\n',t)); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t)
i=t.find('\nLength\n'); j=t.find('Trail Map',i)
s=t[i:j]
s=re.sub(r'To facilitate the public.*?Download[^\n]*GPX','',s,flags=re.S)
s=re.sub(r'The transport information provided.*','',s,flags=re.S)
print(s)
