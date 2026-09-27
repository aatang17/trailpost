import re,html,sys
n=sys.argv[1]
t=open(f'afcd/{n}.html',encoding='utf8').read()
t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>','\n',t)); t=re.sub(r'[ \t]+',' ',t); t=re.sub(r'\n\s*\n+','\n',t)
open(f'afcd/{n}.txt','w').write(t)
