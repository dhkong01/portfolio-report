"""Portfolio Daily Report - GitHub Actions version"""
import os, requests, yfinance as yf
from datetime import datetime, date

# ── 포트폴리오 ──────────────────────────────────────────────
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

# ── 환경변수 ─────────────────────────────────────────────────
KAKAO_KEY   = os.environ['KAKAO_REST_API_KEY']
KAKAO_RFTK  = os.environ['KAKAO_REFRESH_TOKEN']

# ── KakaoTalk ────────────────────────────────────────────────
def get_access_token():
    r = requests.post('https://kauth.kakao.com/oauth/token', data={
        'grant_type':'refresh_token',
        'client_id': KAKAO_KEY,
        'refresh_token': KAKAO_RFTK,
    }, timeout=10)
    r.raise_for_status()
    return r.json()['access_token']

def send_kakao(msg: str):
    token = get_access_token()
    r = requests.post(
        'https://kapi.kakao.com/v2/api/talk/memo/default/send',
        headers={'Authorization': f'Bearer {token}'},
        data={'template_object': f'{{"object_type":"text","text":{repr(msg)},"link":{{"web_url":"","mobile_web_url":""}}}}'},
        timeout=10,
    )
    print(f"KakaoTalk: {r.status_code}")
    r.raise_for_status()

# ── 주가 수집 ────────────────────────────────────────────────
def fetch_prices():
    tickers = [p['t'] for p in PF] + ['^VIX', '^TNX']
    data = yf.download(tickers, period='2d', auto_adjust=True, progress=False)
    closes = data['Close'].iloc[-1]
    return closes

def pct(a, b):
    if a and b and b != 0:
        return (a - b) / b * 100
    return None

# ── 메시지 생성 ───────────────────────────────────────────────
def build_msg(closes):
    today = date.today().strftime('%Y-%m-%d')
    dow   = ['월','화','수','목','금','토','일'][date.today().weekday()]

    vix = closes.get('^VIX')
    tny = closes.get('^TNX')

    # 시장 국면
    if vix and vix < 15:   phase = '🟢 안정'
    elif vix and vix < 25: phase = '🟡 주의'
    else:                  phase = '🔴 위험'

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

    total_val = total_cost = 0
    for p in PF:
        price = closes.get(p['t'])
        if price:
            val  = price * p['sh']
            cost = p['ac'] * p['sh']
            ret  = (price - p['ac']) / p['ac'] * 100
            total_val  += val
            total_cost += cost
            sign = '+' if ret >= 0 else ''
            emoji = '🟢' if ret >= 0 else '🔴'
            lines.append(f"{emoji}{p['t']:<5} ${price:>8.2f}  {sign}{ret:.1f}%")
        else:
            lines.append(f"❓{p['t']:<5}  N/A")

    total_ret = (total_val - total_cost) / total_cost * 100 if total_cost else 0
    total_sign = '+' if total_ret >= 0 else ''

    days_left = (date.fromisoformat(NEXT_RB) - date.today()).days

    lines += [
        '─'*22,
        f'총평가  ${total_val:>10,.0f}',
        f'총수익  {total_sign}{total_ret:.2f}%',
        '',
        f'📆 리밸런싱 D-{days_left} ({NEXT_RB})',
        '─'*22,
        '🤖 by GitHub Actions',
    ]
    return '\n'.join(lines)

# ── 메인 ─────────────────────────────────────────────────────
def main():
    closes = fetch_prices()
    closes_dict = closes.to_dict()
    msg = build_msg(closes_dict)
    print(msg)
    send_kakao(msg)

if __name__ == '__main__':
    main()
