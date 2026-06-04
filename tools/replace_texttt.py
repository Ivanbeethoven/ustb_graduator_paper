import re
from pathlib import Path
root = Path(r'd:\\论文\\latex\\contents')
pattern = re.compile(r'\\\\texttt\{([^}]*)\}')
changed = []
for p in root.rglob('*.tex'):
    s = p.read_text(encoding='utf-8')
    new = pattern.sub(r"\1", s)
    if new != s:
        p.write_text(new, encoding='utf-8')
        changed.append(str(p))
if changed:
    print('Modified files:')
    for c in changed:
        print(c)
else:
    print('No changes')
