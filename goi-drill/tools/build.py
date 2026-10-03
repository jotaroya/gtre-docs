"""app.html と data/questions.json を合体して配布用ファイルを作る。
  python3 tools/build.py            -> index.html（GitHub Pages などにそのまま置ける完全なHTML）
  python3 tools/build.py frag OUT   -> <head>なしの断片（Artifact 公開用）"""
import sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
app = (root / 'app.html').read_text(encoding='utf-8')
data = (root / 'data' / 'questions.json').read_text(encoding='utf-8').replace('</', '<\\/')
body = app.replace('/*DATA*/', data)
if len(sys.argv) > 2 and sys.argv[1] == 'frag':
    pathlib.Path(sys.argv[2]).write_text(body, encoding='utf-8')
else:
    head, sep, rest = body.partition('</style>')
    html = ('<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + head + sep + '\n</head>\n<body>\n' + rest + '\n</body>\n</html>\n')
    (root / 'index.html').write_text(html, encoding='utf-8')
print('ok')
