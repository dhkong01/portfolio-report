"""
Portfolio Daily Report - GitHub Actions
주가 수집 후 latest_report.txt 를 repo에 커밋
"""
import os, json, subprocess
from datetime import date
import yfinance as yf

PF = [
    {'t':'TSLA','sh':160,'ac':183.6738},
    {'t':'PLTR','sh':60,'ac':168.19},
    {'t':'MSTR','sh':160,'ac':150.6961},
    {'t':'ASTS','sh':100,'ac':105.01},
    {'t':'RKLB','sh':132,'ac':87.8286},
    {'t':'VKTX','sh':350,'ac':33.4824},
    {'t':'META','sh':15,'ac':637.28},
    {'t':'VRT','sh':20,'ac':316.06},
]
NEXT_RB = '2026-08-21'

def fetch():
    tickers = [p['t'] for p in PF] + ['^VIX', '^TNX']
    data = yf.download(tickers, period='2d', auto_adjust=True, progress=False)
    return data['Close'].iloc[-1].to_dict()

def build(closes):
    today = date.today().strftime('%Y-%m-%d')
    dow   = ['월','화','수','목','금','토','일'][date.today().weekday()]
    vix   = closes.get('^VIX')
    tny   = closes.get('^TNX')

    phase = ('🟢 안정' if vix and vix < 15 else
             '🟡 주의' if vix and vix < 25 else '🔴 위험')

    lines = [
        '📊 포트폴리오 일일 리포트',
        '━'*22,
        f'📅 {today} ({dow})',
        '',
        f'[시장 국면] {phase}',
        f'  VIX  {vix:.2f}' if vix else '  VIX  N/A',
        f'  금리  {tny:.2f}%' if tny else '  금리  N/A%',
        '',
        '[내 포트폴리오]',
    ]

    tv = tc = 0
    for p in PF:
        price = closes.get(p['t'])
        if price and price > 0:
            val  = price * p['sh']
            ret  = (price - p['ac']) / p['ac'] * 100
            tv  += val
            tc  += p['ac'] * p['sh']
            sgn  = '+' if ret >= 0 else ''
            ico  = '🟢' if ret >= 0 else '🔴'
            lines.append(f"{ico}{p['t']:<5} ${price:>8.2f}  {sgn}{ret:.1f}%")
        else:
            lines.append(f"❓{p['t']:<5}  N/A")

    tr = (tv - tc) / tc * 100 if tc else 0
    dl = (date.fromisoformat(NEXT_RB) - date.today()).days
    sgn = '+' if tr >= 0 else ''

    lines += [
        '─'*22,
        f'총평가  ${tv:>10,.0f}',
        f'총수익  {sgn}{tr:.2f}%',
        '',
        f'📆 리밸런싱 D-{dl} ({NEXT_RB})',
        '─'*22,
        '🤖 by GitHub Actions',
    ]
    return '\n'.join(lines)

def git_push(msg_text):
    with open('latest_report.txt', 'w', encoding='utf-8') as f:
        f.write(msg_text)
    subprocess.run(['git', 'config', 'user.email', 'github-actions@github.com'], check=True)
    subprocess.run(['git', 'config', 'user.name', 'github-actions'], check=True)
    subprocess.run(['git', 'add', 'latest_report.txt'], check=True)
    subprocess.run(['git', 'commit', '-m', f'report: {date.today()}'], check=True)
    subprocess.run(['git', 'push'], check=True)
    print("Pushed latest_report.txt")

if __name__ == '__main__':
    closes = fetch()
    msg = build(closes)
    print(msg)
    git_push(msg)
