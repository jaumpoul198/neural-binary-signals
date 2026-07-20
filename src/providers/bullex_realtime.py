"""
Conector em tempo real para Bull-Ex
Usa WebSocket para receber dados de preço (exchange-rate)
"""

import websocket
import json
import threading
import time
import logging
from typing import Dict, List, Callable, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BullExRealtime:
    """Conector em tempo real para Bull-Ex"""
    
    def __init__(self, ssid: str = "7179466275d20f8265ad5aabef05d83t"):
        self.ssid = ssid
        self.ws = None
        self.is_connected = False
        self.is_authenticated = False
        self.prices: Dict[str, Dict] = {}
        self.callbacks: List[Callable] = []
        self.running = False
        
    def connect(self):
        """Conecta ao WebSocket"""
        ws_url = "wss://ws.trade.bull-ex.com/echo/websocket"
        
        headers = {
            'Origin': 'https://trade.bull-ex.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        logger.info(f"Conectando ao WebSocket...")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            header=headers,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )
        
        self.running = True
        thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        thread.start()
        
    def _on_open(self, ws):
        logger.info("WebSocket conectado!")
        self.is_connected = True
        
        # Autenticação
        auth = {
            "name": "authenticate",
            "msg": {
                "ssid": self.ssid,
                "protocol": 3,
                "client_session_id": ""
            }
        }
        ws.send(json.dumps(auth))
        logger.info("Autenticação enviada")
    
    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            
            # Verifica autenticação
            if data.get('name') == 'authenticated':
                self.is_authenticated = data.get('msg', False)
                logger.info(f"Autenticado: {self.is_authenticated}")
                return
            
            # Processa exchange-rate-generated (preço)
            if data.get('name') == 'exchange-rate-generated':
                msg = data.get('msg', {})
                base = msg.get('base_currency')
                quote = msg.get('quote_currency')
                ask = float(msg.get('ask', 0))
                bid = float(msg.get('bid', 0))
                
                if base and quote:
                    symbol = f"{base}/{quote}"
                    price = (ask + bid) / 2  # Preço médio
                    
                    self.prices[symbol] = {
                        'price': price,
                        'ask': ask,
                        'bid': bid,
                        'base': base,
                        'quote': quote,
                        'timestamp': time.time()
                    }
                    
                    print(f"\n[{symbol}] Preço: {price:.6f} | Ask: {ask:.6f} | Bid: {bid:.6f}")
                    
                    # Notifica callbacks
                    for callback in self.callbacks:
                        try:
                            callback(symbol, self.prices[symbol])
                        except Exception as e:
                            logger.error(f"Erro no callback: {e}")
        
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
    
    def _on_error(self, ws, error):
        logger.error(f"Erro no WebSocket: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket fechado")
        self.is_connected = False
        self.running = False
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Retorna o último preço de um símbolo"""
        if symbol in self.prices:
            return self.prices[symbol].get('price')
        return None
    
    def get_all_prices(self) -> Dict:
        """Retorna todos os preços"""
        return self.prices
    
    def on_update(self, callback: Callable):
        """Registra um callback para atualizações de preço"""
        self.callbacks.append(callback)
    
    def close(self):
        """Fecha a conexão"""
        self.running = False
        if self.ws:
            self.ws.close()


# Função para teste
def test_realtime():
    """Testa o conector em tempo real"""
    connector = BullExRealtime()
    
    def on_price(symbol, data):
        print(f"[{symbol}] Preço: {data['price']:.6f} | Ask: {data['ask']:.6f} | Bid: {data['bid']:.6f}")
    
    connector.on_update(on_price)
    connector.connect()
    
    print("\nAguardando dados... (CTRL+C para sair)\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nEncerrando...")
        connector.close()


if __name__ == "__main__":
    test_realtime()