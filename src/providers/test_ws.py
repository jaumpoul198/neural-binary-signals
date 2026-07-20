"""
Teste WebSocket Bull-Ex - Active_id correto
"""

import websocket
import json
import time
import threading

# ACTIVE_ID CORRETO para EUR/USD
ACTIVE_IDS = [1]  # EUR/USD
PRICES = {}

def on_message(ws, message):
    try:
        data = json.loads(message)
        
        # Verifica autenticacao
        if data.get('name') == 'authenticated':
            print(f'[OK] Autenticado!')
            return
        
        # Verifica inscricao
        if data.get('name') == 'subscribe':
            print(f'[OK] Inscricao confirmada: {data}')
            return
        
        # Processa candles-generated (preco)
        if data.get('name') == 'candles-generated':
            msg = data.get('msg', {})
            active_id = msg.get('active_id')
            
            if active_id in ACTIVE_IDS:
                # Pega o preco atual (value)
                price = msg.get('value')
                ask = msg.get('ask')
                bid = msg.get('bid')
                
                # Pega o candle de 1 minuto
                candles = msg.get('candles', {})
                candle_1m = candles.get('1', {})
                
                if price:
                    PRICES[active_id] = {
                        'price': price,
                        'ask': ask,
                        'bid': bid,
                        'open': candle_1m.get('open'),
                        'high': candle_1m.get('max'),
                        'low': candle_1m.get('min'),
                        'volume': candle_1m.get('volume')
                    }
                    
                    print(f'\n[EUR/USD] PRECO: {price:.6f}')
                    print(f'  Ask: {ask:.6f} | Bid: {bid:.6f}')
                    print(f'  Open: {candle_1m.get("open")} | High: {candle_1m.get("max")} | Low: {candle_1m.get("min")}')
                    print(f'  Volume: {candle_1m.get("volume")}')
        
    except Exception as e:
        print(f'[ERRO] {e}')

def on_error(ws, error):
    print(f'[ERRO WS] {error}')

def on_open(ws):
    print('[CONECTADO] WebSocket conectado!')
    
    # Autenticacao
    auth = {
        'name': 'authenticate',
        'msg': {
            'ssid': '7179466275d20f8265ad5aabef05d83t',
            'protocol': 3,
            'client_session_id': ''
        }
    }
    ws.send(json.dumps(auth))
    print('[AUTH] Autenticacao enviada')
    time.sleep(1)
    
    # Inscreve no active_id correto
    for active_id in ACTIVE_IDS:
        subscribe = {
            'name': 'subscribe',
            'msg': {
                'channel': 'candles',
                'active_id': active_id,
                'size': 1
            }
        }
        ws.send(json.dumps(subscribe))
        print(f'[SUB] Inscrito em active_id: {active_id}')
        time.sleep(0.2)

def on_close(ws, close_status_code, close_msg):
    print('[FECHADO] WebSocket fechado')

def test_ws():
    ws_url = 'wss://ws.trade.bull-ex.com/echo/websocket'
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    print(f'[INICIO] Conectando ao WebSocket...')
    print(f'[INICIO] Monitorando active_ids: {ACTIVE_IDS}')
    print('[INICIO] (CTRL+C para sair)\n')
    
    ws.run_forever()

if __name__ == '__main__':
    test_ws()