"""
Portfolio Monitor - Jonas J
Roda via GitHub Actions a cada hora (dias úteis, horário de mercado).
Envia alertas via ntfy.sh (push no celular) e email (opcional).
"""

import os
import json
import smtplib
import requests
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIG ────────────────────────────────────────────────────────────────────
NTFY_TOPIC  = os.getenv('NTFY_TOPIC', 'jj-portfolio-k7x9m2')
GMAIL_USER  = os.getenv('GMAIL_USER', '')
GMAIL_PASS  = os.getenv('GMAIL_PASS', '')
EMAIL_TO    = 'jcjplanner@gmail.com'
DASHBOARD   = 'https://jjaeger84.github.io/portfolio-dashboard/'

NOW_UTC  = datetime.utcnow()
IS_OPEN  = NOW_UTC.weekday() < 5  # Mon-Fri

# ── PORTFÓLIO ─────────────────────────────────────────────────────────────────
# Ações e ETFs EUA (Avenue) — yfinance
US_ASSETS = {
    'NVDA': {'nome': 'NVIDIA',              'qtd': 11.66481,  'pm': 201.20, 'tipo': 'Ação'},
    'IONQ': {'nome': 'IonQ',                'qtd': 10.03232,  'pm': 47.95,  'tipo': 'Ação'},
    'CCJ':  {'nome': 'Cameco (Urânio)',      'qtd': 4.71142,   'pm': 106.13, 'tipo': 'Ação'},
    'XOM':  {'nome': 'Exxon Mobil',          'qtd': 2.98665,   'pm': 150.67, 'tipo': 'Ação'},
    'UEC':  {'nome': 'Uranium Energy',       'qtd': 34.99905,  'pm': 13.28,  'tipo': 'Ação'},
    'VOO':  {'nome': 'VOO — S&P 500',        'qtd': 15.54018,  'pm': 654.11, 'tipo': 'ETF'},
    'SCHD': {'nome': 'SCHD — Dividendos',    'qtd': 198.43784, 'pm': 31.34,  'tipo': 'ETF'},
    'SCHF': {'nome': 'SCHF — Intl Equity',   'qtd': 200.42367, 'pm': 26.85,  'tipo': 'ETF'},
    'QQQ':  {'nome': 'QQQ — NASDAQ 100',     'qtd': 7.11070,   'pm': 660.97, 'tipo': 'ETF'},
    'REMX': {'nome': 'REMX — Metais Raros',  'qtd': 15.39732,  'pm': 101.12, 'tipo': 'ETF'},
    'AIQ':  {'nome': 'AIQ — IA & Tech',      'qtd': 20.89714,  'pm': 53.74,  'tipo': 'ETF'},
    'XLE':  {'nome': 'XLE — Energia',        'qtd': 21.28300,  'pm': 58.14,  'tipo': 'ETF'},
    'SHLD': {'nome': 'SHLD — Defesa',        'qtd': 11.50269,  'pm': 73.41,  'tipo': 'ETF'},
    'IBIT': {'nome': 'IBIT — Bitcoin ETF',   'qtd': 15.87141,  'pm': 45.55,  'tipo': 'ETF'},
    'VWO':  {'nome': 'VWO — Emergentes',     'qtd': 10.18891,  'pm': 58.89,  'tipo': 'ETF'},
    'VNQ':  {'nome': 'VNQ — Real Estate',    'qtd': 5.25928,   'pm': 95.07,  'tipo': 'ETF'},
    'ICLN': {'nome': 'ICLN — Energia Limpa', 'qtd': 13.43803,  'pm': 22.32,  'tipo': 'ETF'},
    'QQQM': {'nome': 'QQQM — NASDAQ 100',    'qtd': 0.43647,   'pm': 292.11, 'tipo': 'ETF'},
}

# Brasil — brapi.dev (PM combinado PETR4: 53@47.13 + 68@32.10 = 121@38.68)
BR_ASSETS = {
    'GOLD11': {'nome': 'GOLD11 — Ouro',      'qtd': 187,  'pm': 27.14},
    'PETR4':  {'nome': 'PETR4 — Petrobras',  'qtd': 121,  'pm': 38.68},
}

# Crypto — coingecko
CRYPTO = {
    'bitcoin':  {'ticker': 'BTC', 'nome': 'Bitcoin',  'qtd': 0.01414331},
    'ethereum': {'ticker': 'ETH', 'nome': 'Ethereum', 'qtd': 0.18939318},
}

# ── HELPERS ───────────────────────────────────────────────────────────────────
def rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).iloc[-1]

def fmt_brl(v): return f'R$ {v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def fmt_usd(v): return f'$ {v:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def fmt_pct(v): return f'{v:+.1f}%'

def get_usd_brl():
    try:
        r = requests.get('https://economia.awesomeapi.com.br/json/last/USD-BRL', timeout=10)
        return float(r.json()['USDBRL']['bid'])
    except:
        return 5.78

# ── NOTIFICATIONS ─────────────────────────────────────────────────────────────
def push(title, body, priority='default', tags='bell'):
    try:
        resp = requests.post(
            f'https://ntfy.sh/{NTFY_TOPIC}',
            data=body.encode('utf-8'),
            headers={
                'Title': title,
                'Priority': priority,
                'Tags': tags,
                'Content-Type': 'text/plain; charset=utf-8',
            },
            timeout=10
        )
        print(f'  📲 Push enviado: {title} [{resp.status_code}]')
    except Exception as e:
        print(f'  ❌ Push erro: {e}')

def send_email(subject, body_html):
    if not GMAIL_USER or not GMAIL_PASS:
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'[Portfolio] {subject}'
        msg['From']    = GMAIL_USER
        msg['To']      = EMAIL_TO
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(GMAIL_USER, GMAIL_PASS)
            s.sendmail(GMAIL_USER, EMAIL_TO, msg.as_string())
        print(f'  📧 Email enviado: {subject}')
    except Exception as e:
        print(f'  ❌ Email erro: {e}')

def alert(title, body, priority='default', tags='bell'):
    push(title, body, priority, tags)
    send_email(title, body.replace('\n', '<br>'))

# ── ANÁLISE EUA ────────────────────────────────────────────────────────────────
def analyze_us(usd_brl):
    print('\n🇺🇸 Analisando ativos EUA...')
    alerts = []

    tickers = list(US_ASSETS.keys())
    try:
        data = yf.download(tickers, period='1y', group_by='ticker', auto_adjust=True, progress=False)
    except Exception as e:
        print(f'  ❌ Erro yfinance bulk: {e}')
        return []

    for ticker, info in US_ASSETS.items():
        try:
            if len(tickers) == 1:
                hist = data['Close']
            else:
                hist = data['Close'][ticker] if ('Close', ticker) in data.columns or ticker in data['Close'].columns else data[ticker]['Close']

            hist = hist.dropna()
            if len(hist) < 15:
                print(f'  ⚠️ {ticker}: dados insuficientes')
                continue

            cur    = float(hist.iloc[-1])
            prev   = float(hist.iloc[-2])
            daily  = ((cur - prev) / prev) * 100
            rsi_v  = rsi(hist)
            ma50   = float(hist.rolling(50).mean().iloc[-1])
            ma200  = float(hist.rolling(min(200, len(hist))).mean().iloc[-1])
            ret_pm = ((cur - info['pm']) / info['pm']) * 100
            val_usd = cur * info['qtd']
            val_brl = val_usd * usd_brl

            # Analyst data from Yahoo Finance
            target = None; rec = ''; num_anal = 0
            try:
                yinfo   = yf.Ticker(ticker).info
                target  = yinfo.get('targetMeanPrice')
                rec     = yinfo.get('recommendationKey', '')
                num_anal = yinfo.get('numberOfAnalystOpinions', 0)
                week52h = yinfo.get('fiftyTwoWeekHigh', cur)
                week52l = yinfo.get('fiftyTwoWeekLow', cur)
            except:
                week52h = cur; week52l = cur

            pct_from_52h = ((cur - week52h) / week52h) * 100
            pct_from_52l = ((cur - week52l) / week52l) * 100

            print(f'  {ticker}: {fmt_usd(cur)} | RSI {rsi_v:.0f} | {fmt_pct(daily)} hoje | {fmt_pct(ret_pm)} do PM')

            nome  = info['nome']
            tipo  = info['tipo']
            linha = f'━━━━━━━━━━━━━━━━━━━━━━━━'

            # ── ALERTAS ──────────────────────────────────────────────────────

            # 1. Queda forte no dia (≥ 4%)
            if daily <= -4:
                body = (
                    f'⚠️ {ticker} caiu {fmt_pct(daily)} hoje\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'Posição atual: {fmt_usd(val_usd)} ({fmt_brl(val_brl)})\n'
                    f'RSI atual:     {rsi_v:.0f}\n\n'
                    f'Mínima 52 sem: {fmt_usd(week52l)} (você está {fmt_pct(pct_from_52l)} acima)\n'
                )
                if target:
                    body += f'Alvo analistas: {fmt_usd(target)} ({num_anal} analistas) — {rec}\n'
                body += f'\nVer portfólio: {DASHBOARD}\n⚠️ Alerta técnico. Não é recomendação de investimento.'
                alert(f'⚠️ {ticker} caiu {fmt_pct(daily)} hoje', body, priority='high', tags='warning')

            # 2. Alta forte no dia (≥ 4%)
            elif daily >= 4:
                body = (
                    f'🚀 {ticker} subiu {fmt_pct(daily)} hoje\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'Posição atual: {fmt_usd(val_usd)} ({fmt_brl(val_brl)})\n'
                    f'RSI atual:     {rsi_v:.0f}\n\n'
                    f'Máxima 52 sem: {fmt_usd(week52h)} (você está {fmt_pct(pct_from_52h)} abaixo)\n'
                )
                body += f'\nVer portfólio: {DASHBOARD}\n⚠️ Alerta técnico. Não é recomendação de investimento.'
                alert(f'🚀 {ticker} subiu {fmt_pct(daily)} hoje', body, priority='high', tags='rocket')

            # 3. RSI baixo — possível oportunidade de compra
            if rsi_v < 32:
                body = (
                    f'📉 {ticker} com RSI em {rsi_v:.0f} — possível sobrevenda\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'RSI {rsi_v:.0f} = abaixo de 30 indica que o ativo pode estar "barato"\n'
                    f'em relação aos preços recentes (sobrevenda técnica).\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'MA50:          {fmt_usd(ma50)}\n'
                    f'MA200:         {fmt_usd(ma200)}\n'
                    f'Mínima 52 sem: {fmt_usd(week52l)}\n'
                )
                if target and num_anal > 0:
                    upside = ((target - cur) / cur) * 100
                    body += f'\nAnalistas ({num_anal}): {rec} | Alvo: {fmt_usd(target)} ({fmt_pct(upside)} upside)\n'
                body += f'\nVer portfólio: {DASHBOARD}\n⚠️ RSI baixo é sinal técnico. Não é recomendação de compra.'
                alert(f'📉 {ticker} — possível sobrevenda (RSI {rsi_v:.0f})', body, tags='eyes')

            # 4. RSI alto — possível sobrecompra
            if rsi_v > 75:
                body = (
                    f'📈 {ticker} com RSI em {rsi_v:.0f} — possível sobrecompra\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'RSI {rsi_v:.0f} = acima de 70 indica que o ativo pode estar "caro"\n'
                    f'em relação aos preços recentes (sobrecompra técnica).\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'Máxima 52 sem: {fmt_usd(week52h)}\n'
                )
                body += f'\nVer portfólio: {DASHBOARD}\n⚠️ RSI alto é sinal técnico. Não é recomendação de venda.'
                alert(f'📈 {ticker} — possível sobrecompra (RSI {rsi_v:.0f})', body, tags='eyes')

            # 5. Oportunidade: analistas recomendam compra + desconto > 15% do target
            if rec in ('strong_buy', 'buy') and target and cur < target * 0.85 and num_anal >= 5:
                upside = ((target - cur) / cur) * 100
                body = (
                    f'⭐ OPORTUNIDADE: {ticker} com {fmt_pct(upside)} de upside potencial\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'Analistas recomendam: {rec.replace("_"," ").upper()} ({num_anal} analistas)\n'
                    f'Preço-alvo médio: {fmt_usd(target)}\n'
                    f'Preço atual:      {fmt_usd(cur)}\n'
                    f'Upside potencial: {fmt_pct(upside)}\n\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Retorno atual: {fmt_pct(ret_pm)}\n'
                    f'RSI:           {rsi_v:.0f}\n'
                    f'MA50:          {fmt_usd(ma50)}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Preço-alvo de analistas é estimativa. Pesquise antes de investir.'
                )
                alert(f'⭐ {ticker} — {fmt_pct(upside)} de upside (analistas)', body, priority='high', tags='star')

            # 6. Perda relevante (> 20% abaixo do PM)
            if ret_pm < -20:
                body = (
                    f'🔴 {ticker} com perda de {fmt_pct(ret_pm)} do seu custo médio\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Perda atual:   {fmt_pct(ret_pm)}\n'
                    f'RSI:           {rsi_v:.0f}\n'
                )
                if target:
                    body += f'Alvo analistas: {fmt_usd(target)} ({num_anal} analistas) — {rec}\n'
                body += f'\nVer portfólio: {DASHBOARD}\n⚠️ Revise se a tese de investimento ainda se mantém.'
                alert(f'🔴 {ticker} — perda de {fmt_pct(ret_pm)} do seu PM', body, priority='high', tags='red_circle')

            # 7. Lucro expressivo (> 50% acima do PM) — considerar realizar parte
            if ret_pm > 50:
                body = (
                    f'💰 {ticker} com lucro de {fmt_pct(ret_pm)} do seu custo médio\n{linha}\n'
                    f'{tipo}: {nome}\n\n'
                    f'Preço atual:   {fmt_usd(cur)}\n'
                    f'Seu PM:        {fmt_usd(info["pm"])}\n'
                    f'Lucro atual:   {fmt_pct(ret_pm)}\n'
                    f'Posição atual: {fmt_usd(val_usd)} ({fmt_brl(val_brl)})\n'
                    f'RSI:           {rsi_v:.0f}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Alerta informativo. Considere sua estratégia de longo prazo.'
                )
                alert(f'💰 {ticker} — lucro de {fmt_pct(ret_pm)} do seu PM', body, tags='moneybag')

        except Exception as e:
            print(f'  ❌ {ticker}: {e}')

    return alerts

# ── ANÁLISE BRASIL ─────────────────────────────────────────────────────────────
def analyze_br():
    print('\n🇧🇷 Analisando ativos Brasil...')
    try:
        r    = requests.get('https://brapi.dev/api/quote/GOLD11,PETR4', timeout=15)
        data = r.json().get('results', [])
        linha = '━━━━━━━━━━━━━━━━━━━━━━━━'

        for item in data:
            ticker = item['symbol']
            if ticker not in BR_ASSETS:
                continue
            info   = BR_ASSETS[ticker]
            cur    = item.get('regularMarketPrice', 0)
            daily  = item.get('regularMarketChangePercent', 0)
            ret_pm = ((cur - info['pm']) / info['pm']) * 100
            nome   = info['nome']
            val    = cur * info['qtd']

            print(f'  {ticker}: {fmt_brl(cur)} | {fmt_pct(daily)} hoje | {fmt_pct(ret_pm)} do PM')

            if daily <= -4:
                body = (
                    f'⚠️ {ticker} caiu {fmt_pct(daily)} hoje\n{linha}\n'
                    f'{nome}\n\n'
                    f'Preço atual:   {fmt_brl(cur)}\n'
                    f'PM médio:      {fmt_brl(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'Posição:       {fmt_brl(val)}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Alerta técnico. Não é recomendação de investimento.'
                )
                alert(f'⚠️ {ticker} caiu {fmt_pct(daily)} hoje', body, priority='high', tags='warning')

            elif daily >= 4:
                body = (
                    f'🚀 {ticker} subiu {fmt_pct(daily)} hoje\n{linha}\n'
                    f'{nome}\n\n'
                    f'Preço atual:   {fmt_brl(cur)}\n'
                    f'PM médio:      {fmt_brl(info["pm"])}\n'
                    f'Retorno total: {fmt_pct(ret_pm)}\n'
                    f'Posição:       {fmt_brl(val)}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Alerta técnico. Não é recomendação de investimento.'
                )
                alert(f'🚀 {ticker} subiu {fmt_pct(daily)} hoje', body, priority='high', tags='rocket')

    except Exception as e:
        print(f'  ❌ Erro BR: {e}')

# ── ANÁLISE CRIPTO ─────────────────────────────────────────────────────────────
def analyze_crypto():
    print('\n₿ Analisando criptomoedas...')
    try:
        ids  = ','.join(CRYPTO.keys())
        r    = requests.get(
            f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=brl,usd&include_24hr_change=true',
            timeout=15
        )
        data  = r.json()
        linha = '━━━━━━━━━━━━━━━━━━━━━━━━'

        for cid, info in CRYPTO.items():
            if cid not in data:
                continue
            cur_brl = data[cid]['brl']
            cur_usd = data[cid]['usd']
            chg     = data[cid].get('brl_24h_change', 0)
            val     = cur_brl * info['qtd']
            ticker  = info['ticker']
            nome    = info['nome']

            print(f'  {ticker}: {fmt_brl(cur_brl)} | {fmt_pct(chg)} 24h')

            if chg <= -6:
                body = (
                    f'⚠️ {ticker} caiu {fmt_pct(chg)} nas últimas 24h\n{linha}\n'
                    f'{nome}\n\n'
                    f'Preço atual: {fmt_brl(cur_brl)} / {fmt_usd(cur_usd)}\n'
                    f'Quantidade:  {info["qtd"]} {ticker}\n'
                    f'Posição:     {fmt_brl(val)}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Cripto tem alta volatilidade. Alerta informativo.'
                )
                alert(f'⚠️ {ticker} caiu {fmt_pct(chg)} em 24h', body, priority='high', tags='warning')

            elif chg >= 6:
                body = (
                    f'🚀 {ticker} subiu {fmt_pct(chg)} nas últimas 24h\n{linha}\n'
                    f'{nome}\n\n'
                    f'Preço atual: {fmt_brl(cur_brl)} / {fmt_usd(cur_usd)}\n'
                    f'Quantidade:  {info["qtd"]} {ticker}\n'
                    f'Posição:     {fmt_brl(val)}\n\n'
                    f'Ver portfólio: {DASHBOARD}\n'
                    f'⚠️ Cripto tem alta volatilidade. Alerta informativo.'
                )
                alert(f'🚀 {ticker} subiu {fmt_pct(chg)} em 24h', body, priority='high', tags='rocket')

    except Exception as e:
        print(f'  ❌ Erro crypto: {e}')

# ── RESUMO MATINAL ─────────────────────────────────────────────────────────────
def morning_summary(usd_brl):
    # Envia às 13h UTC (10h ET / 10h BRL) — abertura da bolsa americana
    if NOW_UTC.hour != 13:
        return
    print('\n🌅 Enviando resumo matinal...')
    try:
        # Cripto
        r    = requests.get(
            'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=brl&include_24hr_change=true',
            timeout=10
        )
        cd   = r.json()
        btc  = cd['bitcoin']['brl']
        eth  = cd['ethereum']['brl']
        btc_c = cd['bitcoin']['brl_24h_change']
        eth_c = cd['ethereum']['brl_24h_change']

        # Mercado BR
        br  = requests.get('https://brapi.dev/api/quote/GOLD11,PETR4', timeout=10).json().get('results', [])
        br_lines = ''
        for item in br:
            chg = item.get('regularMarketChangePercent', 0)
            br_lines += f'{item["symbol"]}: {fmt_brl(item["regularMarketPrice"])} ({fmt_pct(chg)})\n'

        body = (
            f'Bom dia! Mercado americano abrindo agora.\n'
            f'━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
            f'💵 Dólar:    R$ {usd_brl:.2f}\n'
            f'₿ Bitcoin:  {fmt_brl(btc)} ({fmt_pct(btc_c)})\n'
            f'Ethereum:   {fmt_brl(eth)} ({fmt_pct(eth_c)})\n\n'
            f'🇧🇷 Bolsa Brasil:\n{br_lines}\n'
            f'Ver portfólio completo:\n{DASHBOARD}'
        )
        alert('🌅 Resumo Matinal do Portfólio', body, tags='sun')
    except Exception as e:
        print(f'  ❌ Resumo matinal erro: {e}')

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'\n{"="*50}')
    print(f'📊 Monitor de Portfólio — {NOW_UTC.strftime("%Y-%m-%d %H:%M")} UTC')
    print(f'📲 Tópico ntfy: {NTFY_TOPIC}')
    print(f'{"="*50}')

    usd_brl = get_usd_brl()
    print(f'💵 USD/BRL: R$ {usd_brl:.2f}')

    morning_summary(usd_brl)
    analyze_us(usd_brl)
    analyze_br()
    analyze_crypto()

    print(f'\n✅ Monitoramento concluído às {datetime.utcnow().strftime("%H:%M")} UTC\n')
