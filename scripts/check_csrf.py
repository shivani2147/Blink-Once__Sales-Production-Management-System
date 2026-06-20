import glob, re, os
root = os.path.dirname(os.path.dirname(__file__))
paths = glob.glob(os.path.join(root, 'app', 'templates', '**', '*.html'), recursive=True)
missing = []
for path in paths:
    t = open(path, encoding='utf-8').read()
    found = False
    for m in re.finditer(r'<form[^>]*action=["\']([^"\']*delete[^"\']*)["\'][^>]*>', t, re.IGNORECASE):
        # extract snippet until </form>
        start = m.start()
        end = t.find('</form>', start)
        snippet = t[start:end] if end != -1 else t[start:]
        if 'csrf_token' not in snippet:
            missing.append((path, snippet.strip()))
print('checked', len(paths), 'templates')
print('missing csrf in', len(missing), 'forms')
for p, s in missing:
    print('---', p)
    print(s.replace('\n','\\n')[:400])
