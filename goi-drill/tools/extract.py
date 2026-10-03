"""対策プリントPDFから問題と解答を抜き出して JSON にする。
  python3 tools/extract.py 対策プリント.pdf raw.json
要: pip install pymupdf。ページ範囲は下の表を PDF に合わせて変える。"""
import pymupdf, re, json, sys
d=pymupdf.open(sys.argv[1])
DIG='０１２３４５６７８９0123456789'
def chars_of(pno):
    p=d[pno]; chars=[]
    for b in p.get_text('rawdict')['blocks']:
        for l in b.get('lines',[]):
            for sp in l['spans']:
                for c in sp['chars']:
                    if not c['c'].strip(): continue
                    x0,y0,x1,y1=c['bbox']
                    chars.append(dict(c=c['c'],x0=x0,y0=y0,x1=x1,y1=y1,xc=(x0+x1)/2,yc=(y0+y1)/2,size=sp['size']))
    lines=[dr['rect'] for dr in p.get_drawings() if dr['rect'].width<3 and dr['rect'].height>5]
    return chars,lines
def segments(pno,gap=8):
    chars,lines=chars_of(pno)
    ruby=[c for c in chars if c['size']<9]
    body=[c for c in chars if c['size']>=9]
    body.sort(key=lambda c:-c['xc'])
    cols=[]
    for c in body:
        for col in cols:
            if abs(col['x']-c['xc'])<4 and abs(col['w']-(c['x1']-c['x0']))<4:
                col['ch'].append(c);break
        else: cols.append(dict(x=c['xc'],w=c['x1']-c['x0'],ch=[c]))
    # attach ruby to nearest body char to the left
    for r in ruby:
        best=min(body,key=lambda c:abs(c['x1']-r['x0'])*3+abs(c['yc']-r['yc']))
        best.setdefault('ruby','')
        best['ruby']+=r['c']
    segs=[]
    for col in cols:
        col['ch'].sort(key=lambda c:c['yc'])
        cur=[]
        groups=[]
        for c in col['ch']:
            if cur and c['y0']-cur[-1]['y1']>gap: groups.append(cur);cur=[]
            cur.append(c)
        if cur: groups.append(cur)
        for g in groups:
            s=''
            for c in g:
                ul=any(abs(r.x0-c['x1'])<3 and r.y0<c['yc']<r.y1 for r in lines)
                t=c['c']
                if ul: t='['+t+']'
                if c.get('ruby'): t+='{'+c['ruby']+'}'
                s+=t
            s=s.replace('][','')
            segs.append(dict(x=col['x'],y=g[0]['y0'],t=s))
    return segs
def stream(pages, half=False, gap=8):
    toks=[]
    for p in pages:
        ss=[s for s in segments(p,gap) if not all(ch in DIG+'〔〕-' for ch in s['t'])]
        if half: ss.sort(key=lambda s:(s['y']>=300,-s['x'],s['y']))
        else: ss.sort(key=lambda s:(-round(s['x']),s['y']))
        toks+= [s['t'] for s in ss]
    return toks
def strip_num(t): return re.sub('^[０-９0-9]+','',t)
def answers(pages):
    s=''.join(stream(pages,half=True))
    return re.findall(r'〔([^〕Ｐ]+)〕〔Ｐ([０-９]+)・([０-９]+)〕',s)
def z2h(s): return s.translate(str.maketrans('０１２３４５６７８９','0123456789'))
def written(qpages,apages):
    qs=[strip_num(t) for t in stream(qpages,gap=30) if '[' in t]
    ans=answers(apages)
    return qs,ans
def meaning(qpages,apages):
    toks=stream(qpages)
    # drop headers
    items=[];cur=None
    for i,t in enumerate(toks):
        nxt=toks[i+1] if i+1<len(toks) else ''
        if t.endswith('〔') : continue
        if nxt.startswith('①') and not t.startswith(('①','②','③','④')):
            cur=dict(word=strip_num(t),opts=[]); items.append(cur); continue
        if cur is None: continue
        m=re.match('^([①②③④])(.*)',t)
        if m: cur['opts'].append(m.group(2))
        elif cur['opts'] and len(cur['opts'])<=4 and not re.search('問|【',t): cur['opts'][-1]+=t
    ans=answers(apages)
    return items,ans
out={}
for key,q,a in [('yomi',range(0,6),[6,7]),('kaki1',range(28,36),[36,37]),('kaki2',range(38,47),[47,48])]:
    qs,ans=written(q,a)
    print(key,len(qs),len(ans))
    out[key]=[dict(q=x,a=y[0],ref='P'+z2h(y[1])+'-'+z2h(y[2])) for x,y in zip(qs,ans)]
for key,q,a in [('imi1',range(8,13),[13]),('kata',range(14,19),[19]),('imi2',range(21,27),[27])]:
    items,ans=meaning(q,a)
    print(key,len(items),len(ans),[len(i['opts']) for i in items if len(i['opts'])!=4])
    out[key]=[dict(word=i['word'],opts=i['opts'],a='①②③④'.index(y[0])+1 if y[0] in '①②③④' else y[0],ref='P'+z2h(y[1])+'-'+z2h(y[2])) for i,y in zip(items,ans)]
json.dump(out,open(sys.argv[2],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
