"""把「製作教學.md」裡的程式碼區塊更新成目前的程式。

教學的文字直接寫在 製作教學.md 裡；這支腳本只負責程式碼：
- 3-1～3-3：icon.svg、manifest.json、sw.js 整份
- 4-1～4-15：index.html 依區段標記切成 15 段（依序貼回就是完整檔案）
- Firebase 設定值換成「貼上你的 xxx」，不會把真正的專案設定寫進教學

用法（在 expense-tracker 資料夾執行）：python tools/build_tutorial.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / '製作教學.md'
CR, LF = '\r', '\n'
FENCE = '```'


def read(path):
    text = path.read_text(encoding='utf-8')
    return text.replace(CR + LF, LF)


html = read(ROOT / 'index.html')
lines = html.split(LF)

# ---- 依區段標記切開 index.html ----
MARKERS = [
    r'^<script>$',
    r'^/\* -+ 資料 -+ \*/$',
    r'^/\* -+ 日期 -+ \*/$',
    r'^/\* -+ 定期收支 -+ \*/$',
    r'^/\* -+ 畫面骨架 -+ \*/$',
    r'^/\* -+ 記帳 -+ \*/$',
    r'^/\* -+ 明細 -+ \*/$',
    r'^/\* -+ 統計與預算 -+ \*/$',
    r'^/\* -+ 帳戶 -+ \*/$',
    r'^/\* -+ 設定 -+ \*/$',
    r'^/\* -+ 定期收支設定 -+ \*/$',
    r'^/\* -+ 匯出匯入 -+ \*/$',
    r'^/\* 提供給雲端同步模組使用 \*/$',
    r'^<script type="module">$',
]
cuts = [0]
for m in MARKERS:
    hits = [i for i, l in enumerate(lines) if re.match(m, l)]
    if len(hits) != 1:
        sys.exit(f'區段標記找不到或重複：{m}')
    cuts.append(hits[0])
cuts.append(len(lines))
if cuts != sorted(cuts):
    sys.exit('區段標記順序不對')
pieces = [LF.join(lines[cuts[i]:cuts[i + 1]]) for i in range(len(cuts) - 1)]

# ---- Firebase 設定值換成佔位字串 ----
KEYS = ['apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId']
real = {}


def placeholder(s):
    for k in KEYS:
        m = re.search(rf'(  {k}: )"([^"]*)"', s)
        if not m:
            sys.exit(f'找不到 Firebase 設定：{k}')
        real[k] = m.group(2)
        s = s[:m.start()] + f'{m.group(1)}"貼上你的 {k}"' + s[m.end():]
    return s


pieces[-1] = placeholder(pieces[-1])

# 驗證：還原佔位字串後依序串回去，必須和原檔一樣
restored = LF.join(pieces)
for k in KEYS:
    restored = restored.replace(f'"貼上你的 {k}"', f'"{real[k]}"', 1)
if restored != html:
    sys.exit('切出來的區段串不回原本的 index.html')

# ---- 把程式碼放進教學 ----
raw_doc = DOC.read_text(encoding='utf-8')
crlf = CR + LF in raw_doc
doc = raw_doc.replace(CR + LF, LF)


def put_block(doc, heading, code):
    """把 heading 之後第一個程式碼區塊的內容換成 code。"""
    h = doc.find(LF + heading)
    if h < 0:
        sys.exit(f'教學裡找不到標題：{heading}')
    start = doc.find(LF + FENCE, h)
    body = doc.find(LF, start + 1) + 1
    end = doc.find(LF + FENCE + LF, body)
    nxt = doc.find(LF + '### ', h + 1)
    if start < 0 or end < 0 or (0 <= nxt < start):
        sys.exit(f'{heading} 底下找不到程式碼區塊')
    return doc[:body] + code.rstrip(LF) + doc[end:]


doc = put_block(doc, '### 3-1', read(ROOT / 'icon.svg'))
doc = put_block(doc, '### 3-2', read(ROOT / 'manifest.json'))
doc = put_block(doc, '### 3-3', read(ROOT / 'sw.js'))
for n, code in enumerate(pieces, 1):
    doc = put_block(doc, f'### 4-{n}　', code)

# 驗證：教學裡 4-1～4-15 的程式碼串起來（不計空行）要和 index.html 一樣
section = doc[doc.index(LF + '### 4-1　'):doc.index(LF + '## 5.')]
blocks = re.findall(r'```(?:html|js)\n(.*?)\n```', section, flags=re.S)
joined = LF.join(blocks)
for k in KEYS:
    joined = joined.replace(f'"貼上你的 {k}"', f'"{real[k]}"', 1)
norm = lambda s: [l for l in s.split(LF) if l.strip()]
if len(blocks) != 15 or norm(joined) != norm(html):
    sys.exit(f'驗證失敗：區塊數 {len(blocks)}')
for k, v in real.items():
    if v in doc:
        sys.exit(f'教學裡出現真正的 Firebase 設定值（{k}）')

if crlf:
    doc = doc.replace(LF, CR + LF)
if doc == raw_doc:
    print('教學已是最新，沒有變動')
else:
    DOC.write_text(doc, encoding='utf-8', newline='')
    print(f'已更新 {DOC.name}：{len(doc.splitlines())} 行，15 段程式碼與 index.html 一致')
