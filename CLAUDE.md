# Contexto do Projeto — Dashboard de Portfólio Jonas J

## Quem é o usuário

**Nome:** Jonas J  
**Email:** jcjplanner@gmail.com  
**GitHub:** jjaeger84  
**Perfil de investidor:** Moderado-agressivo — aceita risco em busca de crescimento, mas mantém base em renda fixa  
**Objetivo principal:** Crescimento patrimonial de longo prazo com exposição a temas de alta convicção (IA, quantum, energia nuclear, cripto)  
**Horizonte:** Longo prazo, com aportes regulares  
**Experiência:** Investidor ativo, não especialista técnico — prefere explicações didáticas, sem jargão desnecessário  

---

## Portfólio completo

### Brasil (B3)
| Ativo | Corretora | Qtd | PM |
|-------|-----------|-----|----|
| GOLD11 | Santander | 187 cotas | R$ 27,14 |
| PETR4 | Santander | 53 cotas | R$ 47,13 |
| PETR4 | Ion | 68 cotas | R$ 32,10 |
| PETR4 combinado | — | 121 cotas | R$ 38,68 (PM ponderado) |

### Renda Fixa
| Ativo | Corretora | Valor atual |
|-------|-----------|-------------|
| CDB-DI | Santander | R$ 124.765,20 |
| CDB-DI | Ion | R$ 152.593,89 |
| **Total RF** | | **R$ 277.359,09** |

### Criptomoedas (Santander)
| Ativo | Qtd |
|-------|-----|
| Bitcoin (BTC) | 0,01414331 |
| Ethereum (ETH) | 0,18939318 |

### Avenue — Ações EUA
| Ticker | Nome | Qtd | PM (USD) |
|--------|------|-----|----------|
| NVDA | NVIDIA | 11,66481 | 201,20 |
| IONQ | IonQ | 10,03232 | 47,95 |
| CCJ | Cameco (urânio) | 4,71142 | 106,13 |
| XOM | Exxon Mobil | 2,98665 | 150,67 |
| UEC | Uranium Energy | 34,99905 | 13,28 |

### Avenue — ETFs EUA
| Ticker | Nome | Qtd | PM (USD) |
|--------|------|-----|----------|
| VOO | Vanguard S&P 500 | 15,54018 | 654,11 |
| SCHD | Schwab Dividendos | 198,43784 | 31,34 |
| SCHF | Schwab Intl Equity | 200,42367 | 26,85 |
| QQQ | Invesco NASDAQ 100 | 7,11070 | 660,97 |
| REMX | VanEck Rare Earth | 15,39732 | 101,12 |
| AIQ | Global X AI & Tech | 20,89714 | 53,74 |
| XLE | Energy Select SPDR | 21,28300 | 58,14 |
| SHLD | Global X Defense Tech | 11,50269 | 73,41 |
| IBIT | iShares Bitcoin Trust | 15,87141 | 45,55 |
| VWO | Vanguard Emerging Mkts | 10,18891 | 58,89 |
| VNQ | Vanguard Real Estate | 5,25928 | 95,07 |
| ICLN | iShares Clean Energy | 13,43803 | 22,32 |
| QQQM | Invesco NASDAQ 100 | 0,43647 | 292,11 |

---

## Projeto técnico

**Dashboard ao vivo:** https://jjaeger84.github.io/portfolio-dashboard/  
**Repositório:** https://github.com/jjaeger84/portfolio-dashboard  
**Arquivos locais:** `/Users/jj/Desktop/portfolio-dashboard/`  

### Arquitetura
- `index.html` — dashboard single-page, dark theme, Chart.js, auto-refresh 60s
- `monitor.py` — monitoramento horário com alertas RSI, variação diária, analistas
- `prices.json` — preços gerados pelo GitHub Actions via yfinance (sem CORS proxy)
- `.github/workflows/monitor.yml` — cron Mon-Fri 12h-22h UTC, gera prices.json e envia alertas
- Alertas: ntfy.sh tópico `jj-portfolio-k7x9m2` + email jcjplanner@gmail.com (opcional)

### Fontes de dados
- Ações/ETFs BR e EUA → yfinance via GitHub Actions → prices.json
- Cripto → CoinGecko (browser, tempo real)
- USD/BRL → AwesomeAPI (browser, tempo real)

---

## Como me comportar neste projeto

### Análises financeiras
- Sempre usar dados reais de mercado antes de recomendar (WebSearch, yfinance)
- Citar fontes e preços-alvo de analistas quando disponíveis
- Verificar RSI, momentum, tendência de analistas (strong buy / buy / hold)
- Comparar com o portfólio atual — evitar recomendar o que o usuário já tem
- Sinalizar claramente o nível de risco: conservador / moderado / agressivo / especulativo
- Sempre incluir aviso de que não é recomendação formal de investimento

### Atualizações de portfólio
- Quando o usuário comprar novos ativos: atualizar `index.html` (DATA) e `monitor.py` (US_ASSETS ou BR_ASSETS)
- Calcular novo PM ponderado automaticamente: `(qtd_antiga × pm_antigo + qtd_nova × preco_compra) / total`
- Após editar: `git add . && git commit -m "msg" && git push`

### Comunicação
- Linguagem clara, didática, sem jargão desnecessário
- O usuário não é técnico — explicar conceitos financeiros quando necessário
- Respostas diretas e objetivas
- Quando houver múltiplas opções, indicar claramente a recomendação preferida e o motivo
