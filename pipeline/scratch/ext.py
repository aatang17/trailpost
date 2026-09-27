import re,html,sys
t=open(sys.argv[1],encoding='utf-8',errors='ignore').read()
t=re.sub(r'<script.*?</script>','',t,flags=re.S);t=re.sub(r'<style.*?</style>','',t,flags=re.S)
t=html.unescape(re.sub(r'<[^>]+>','\n',t));t=re.sub(r'\n\s*\n+','\n',t)
a=t.find('路徑概要\n長度') if '路徑概要\n長度' in t else t.find('Length')
b=t.find('附近景點') if '附近景點' in t else len(t)
print(t[a:b])
