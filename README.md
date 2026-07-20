# 🧠 Neural Binary Signals

> **Sistema Inteligente de Sinais para Opções Binárias**
> 
> Memória Fotográfica Neural + Análise Preditiva Multi-Indicador
> 
> Operação Manual com Inteligência Artificial

---

## 📸 Visão Geral

O **Neural Binary Signals** é um sistema avançado de geração de sinais para opções binárias que combina:

- **🧠 Memória Fotográfica Neural**: Armazena e reconhece padrões de candles, formando uma "memória fotográfica" de configurações vencedoras e perdedoras
- **📊 Análise Multi-Indicador**: RSI, MACD, Bollinger Bands, VWAP, Stochastic, Volume Profile, ATR e mais
- **🔮 Previsão Preditiva**: Algoritmos de similaridade que comparam o cenário atual com padrões históricos
- **⚡ Operação Manual Inteligente**: Você opera, a IA analisa — sem automação de execução

## 🚀 Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| `core` | Motor central de processamento de dados |
| `indicators` | 15+ indicadores técnicos otimizados para M1/M5 |
| `memory` | Sistema de memória fotográfica com similaridade neural |
| `signals` | Gerador de sinais com scoring de confiança |
| `connectors` | Conectores para dados de mercado (Yahoo, WebSocket) |
| `gui` | Dashboard visual em PyQt6 com alertas sonoros |

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/neural-binary-signals.git
cd neural-binary-signals

# Crie o ambiente virtual
python -m venv venv

# Ative (Windows)
venv\Scripts\activate
# Ative (Linux/Mac)
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

## ▶️ Uso

### Modo Dashboard (Recomendado)
```bash
python main.py --mode dashboard
```

### Modo Terminal
```bash
python main.py --mode terminal --pair EURUSD --timeframe M5
```

### Modo Análise
```bash
python main.py --mode analyze --pair EURUSD --timeframe M5 --lookback 100
```

## ⚙️ Configuração

Edite `config/settings.json` para personalizar:

```json
{
  "pairs": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
  "timeframes": ["M1", "M5", "M15"],
  "indicators": {
    "rsi": {"period": 14, "overbought": 70, "oversold": 30},
    "macd": {"fast": 12, "slow": 26, "signal": 9},
    "bollinger": {"period": 20, "std": 2.0}
  },
  "signal_threshold": 75,
  "memory_similarity_threshold": 0.85
}
```

## 🧠 Como Funciona a Memória Fotográfica

1. **Captura**: O sistema captura snapshots do mercado (preço + indicadores + volume)
2. **Armazenamento**: Cada snapshot é vetorizado e armazenado com o resultado (WIN/LOSS)
3. **Reconhecimento**: Quando um novo cenário aparece, o sistema busca os padrões mais similares
4. **Predição**: Com base nos resultados dos padrões similares, calcula a probabilidade de sucesso

## ⚠️ Aviso Importante

> **Este sistema é para ANÁLISE e GERAÇÃO DE SINAIS apenas.**
> 
> - Não executa trades automaticamente
> - A operação é sempre MANUAL
> - Opções binárias são de alto risco
> - Gerencie seu capital e risco adequadamente
> - Não há garantia de lucro

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes.

---

**Desenvolvido por traders, para traders.** 🎯
