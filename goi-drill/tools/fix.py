"""抽出結果(data.json)に手作業の修正を当て、questions.json を出力する。
PDF のフォント都合で文字化けする字（剥・凋）や重複を直す。"""
import json, sys
src, dst = sys.argv[1], sys.argv[2]
D = json.load(open(src, encoding='utf-8'))
REPL = [('域奪', '剥奪'), ('卯落', '凋落'), ('捧{ささ}捧げる', '捧{ささ}げる'), ('じゅうたい)', 'じゅうたい）')]
def fix(s):
    for a, b in REPL:
        s = s.replace(a, b)
    return s
for items in D.values():
    for it in items:
        for k, v in list(it.items()):
            if isinstance(v, str): it[k] = fix(v)
            elif isinstance(v, list): it[k] = [fix(x) for x in v]
META = [
  ('yomi',  '読み',        '第2回', 'written', 'P84〜P91',   '範囲の読みをすべて練習できます。この中から問題が出ます。'),
  ('kaki1', '書き①',       '第2回', 'written', 'P52〜P75',   '範囲の漢字の半分をランダムで練習できます。'),
  ('kaki2', '書き②',       '第2回', 'written', 'P136〜P159', '範囲の漢字の半分をランダムで練習できます。'),
  ('imi1',  '意味 重要語①', '第3回', 'choice',  'P210〜P219', '範囲の語句の半分をランダムで練習できます。'),
  ('imi2',  '意味 重要語②', '第3回', 'choice',  'P210〜P219', '範囲の語句の半分をランダムで練習できます。'),
  ('kata',  'カタカナ語',   '第3回', 'choice',  'P220〜P231', '範囲の語句の半分をランダムで練習できます。'),
]
out = [dict(id=i, name=n, test=t, kind=k, range=r, note=note, items=D[i]) for i, n, t, k, r, note in META]
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print({s['id']: len(s['items']) for s in out})
