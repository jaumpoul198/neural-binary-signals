"""
Conector WebSocket para Bull-Ex
Com keep-alive e reconexao
"""

import websocket
import json
import threading
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BullExWebSocket:
    """Conector WebSocket para dados em tempo real da Bull-Ex"""
    
    def __init__(self):
        self.ws = None
        self.last_price = None
        self.last_ask = None
        self.last_bid = None
        self.is_connected = False
        self.active_id = 78
        self.callbacks = []
        self.running = False
        self.authenticated = False
        self.ssid = "7179466275d20f8265ad5aabef05d83t"
        self.message_count = 0
        self.ping_interval = 10
        
    def connect(self):
        ws_url = "wss://ws.trade.bull-ex.com/echo/websocket"
        
        headers = {
            'Origin': 'https://trade.bull-ex.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        }
        
        logger.info(f"Conectando ao WebSocket: {ws_url}")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        self.running = True
        wst = threading.Thread(target=self.ws.run_forever, daemon=True)
        wst.start()
        
    def on_open(self, ws):
        logger.info("WebSocket conectado!")
        self.is_connected = True
        
        # Autenticacao
        auth_msg = {
            "name": "authenticate",
            "msg": {
                "ssid": self.ssid,
                "protocol": 3,
                "client_session_id": ""
            }
        }
        ws.send(json.dumps(auth_msg))
        logger.info("Autenticacao enviada")
        
        # Aguarda autenticacao antes de inscrever
        time.sleep(1)
        
        # Tenta varios formatos de inscricao
        subscribe_msgs = [
            {"name": "subscribe", "msg": {"channel": "candles", "active_id": self.active_id, "size": 1}},
            {"name": "subscribe", "msg": {"channel": "ticker", "active_id": self.active_id}},
            {"event": "subscribe", "channel": f"candles.{self.active_id}"},
            {"type": "subscribe", "data": {"active_id": self.active_id, "channel": "candles"}},
        ]
        
        for msg in subscribe_msgs:
            try:
                ws.send(json.dumps(msg))
                logger.info(f"Inscricao enviada: {msg}")
                time.sleep(0.3)
            except Exception as e:
                logger.error(f"Erro ao enviar inscricao: {e}")
    
    def on_message(self, ws, message):
        self.message_count += 1
        print(f"\n[MENSAGEM BRUTA] {message}")
        print(f"\n[MSG {self.message_count}] {message[:300]}")
        
        try:
            data = json.loads(message)
            
            # Autenticacao
            if data.get('name') == 'authenticate':
                if data.get('msg', {}).get('success'):
                    self.authenticated = True
                    logger.info("Autenticado com sucesso!")
                return
            
            # Resposta de inscricao
            if data.get('name') == 'subscribe':
                logger.info(f"Inscricao confirmada: {data}")
                return
            
            # Candle (preco)
            if data.get('name') == 'candle-generated':
                msg = data.get('msg', {})
                if msg.get('active_id') == self.active_id:
                    close = msg.get('close')
                    ask = msg.get('ask')
                    bid = msg.get('bid')
                    
                    if close:
                        self.last_price = close
                        self.last_ask = ask
                        self.last_bid = bid
                        
                        print(f"\n[PRECO] {close:.6f} | Ask: {ask:.6f} | Bid: {bid:.6f}")
                        
                        for callback in self.callbacks:
                            callback({
                                'price': close,
                                'ask': ask,
                                'bid': bid,
                                'open': msg.get('open'),
                                'high': msg.get('max'),
                                'low': msg.get('min'),
                                'volume': msg.get('volume')
                            })
            
            # Ticker
            if data.get('name') == 'ticker':
                msg = data.get('msg', {})
                if msg.get('active_id') == self.active_id:
                    price = msg.get('price')
                    if price:
                        self.last_price = price
                        print(f"\n[TICKER] {price:.6f}")
            
        except Exception as e:
            print(f"Erro: {e}")
    
    def on_error(self, ws, error):
        logger.error(f"Erro no WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket fechado")
        self.is_connected = False
        self.running = False
        
        # Tenta reconectar
        if self.running:
            logger.info("Tentando reconectar em 5 segundos...")
            time.sleep(5)
            self.connect()
        
    def get_price(self):
        return self.last_price
    
    def get_ask(self):
        return self.last_ask
    
    def get_bid(self):
        return self.last_bid
    
    def subscribe(self, callback):
        self.callbacks.append(callback)
    
    def close(self):
        self.running = False
        if self.ws:
            self.ws.close()


def test_ws():
    ws = BullExWebSocket()
    ws.subscribe(lambda x: None)
    ws.connect()
    
    print("\nAguardando precos... (CTRL+C para sair)")
    print("O WebSocket vai tentar reconectar se cair\n")
    
    try:
        while True:
            time.sleep(2)
            if ws.last_price:
                print(f"Ultimo preco: {ws.last_price:.6f}")
    except KeyboardInterrupt:
        print("\nEncerrando...")
        ws.close()


if __name__ == "__main__":
    test_ws()