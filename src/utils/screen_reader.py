"""
Leitor de tela para capturar preço da Bull-Ex
Detecta automaticamente se é tela clara ou escura
"""

import pytesseract
from PIL import ImageGrab, ImageOps, ImageEnhance, ImageStat
import re
import time
import logging
import os
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScreenReader:
    """Captura preço da tela da corretora"""
    
    def __init__(self):
        self.tesseract_ready = False
        self._setup_tesseract()
    
    def _setup_tesseract(self):
        """Configura o Tesseract OCR"""
        try:
            possible_paths = [
                r'C:\tesseract\tesseract.exe',
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
            ]
            
            try:
                result = subprocess.run(['where', 'tesseract'], capture_output=True, text=True)
                if result.returncode == 0:
                    tesseract_path = result.stdout.strip().split('\n')[0]
                    if os.path.exists(tesseract_path):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        self.tesseract_ready = True
                        logger.info(f"Tesseract encontrado em: {tesseract_path}")
                        return
            except:
                pass
            
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    self.tesseract_ready = True
                    logger.info(f"Tesseract encontrado em: {path}")
                    return
            
            logger.warning("Tesseract nao encontrado.")
            
        except Exception as e:
            logger.error(f"Erro ao configurar Tesseract: {e}")
    
    def _is_dark_background(self, img):
        """Detecta se a imagem tem fundo escuro ou claro"""
        # Converte para escala de cinza
        gray = img.convert('L')
        # Calcula o brilho médio
        stat = ImageStat.Stat(gray)
        mean_brightness = stat.mean[0]
        
        # Se brilho médio < 128, é fundo escuro
        # Se brilho médio >= 128, é fundo claro
        is_dark = mean_brightness < 128
        logger.info(f"Brilho medio: {mean_brightness:.0f} - {'Escuro' if is_dark else 'Claro'}")
        return is_dark
    
    def _preprocess_image(self, img):
        """
        Pré-processa a imagem baseado no fundo
        """
        # Converte para escala de cinza
        img_gray = img.convert('L')
        
        # Aumenta contraste
        enhancer = ImageEnhance.Contrast(img_gray)
        img_enhanced = enhancer.enhance(2.5)
        
        # Detecta se é fundo escuro
        is_dark = self._is_dark_background(img_enhanced)
        
        if is_dark:
            # Fundo escuro: inverte cores
            logger.info("Aplicando inversao de cores (fundo escuro)")
            img_processed = ImageOps.invert(img_enhanced)
        else:
            # Fundo claro: mantém cores
            logger.info("Mantendo cores (fundo claro)")
            img_processed = img_enhanced
        
        # Aumenta brilho
        enhancer = ImageEnhance.Brightness(img_processed)
        img_processed = enhancer.enhance(1.3)
        
        return img_processed
    
    def get_price_from_screen(self, region=None):
        """
        Captura o preco da tela com deteccao automatica de cores
        """
        if not self.tesseract_ready:
            return None
        
        # REGIAO PADRAO - AJUSTE CONFORME SUA TELA
        if region is None:
            region = (850, 300, 250, 100)
        
        try:
            x, y, w, h = region
            if w < 0 or h < 0:
                logger.error(f"Regiao invalida: {region}")
                return None
            
            # Captura a tela
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            
            # Salva para debug
            screenshot.save('ultima_captura.png')
            
            # Pré-processa a imagem
            processed_img = self._preprocess_image(screenshot)
            processed_img.save('ultima_captura_processada.png')
            
            # Tenta com diferentes configurações
            configs = [
                '--psm 6 -c tessedit_char_whitelist=0123456789.,',
                '--psm 8 -c tessedit_char_whitelist=0123456789.,',
                '--psm 7 -c tessedit_char_whitelist=0123456789.,',
                '--psm 13 -c tessedit_char_whitelist=0123456789.,',
            ]
            
            all_text = []
            for config in configs:
                text = pytesseract.image_to_string(
                    processed_img, 
                    lang='eng',
                    config=config
                )
                all_text.append(text)
                
                numbers = re.findall(r'(\d+[.,]\d{2,4})', text)
                if numbers:
                    price_str = numbers[0].replace(',', '.')
                    price = float(price_str)
                    logger.info(f"Preco capturado: {price}")
                    return price
            
            # Se não encontrou, tenta com a imagem original
            logger.info("Tentando com imagem original...")
            text_orig = pytesseract.image_to_string(
                screenshot,
                lang='eng',
                config='--psm 6'
            )
            numbers_orig = re.findall(r'(\d+[.,]\d{2,4})', text_orig)
            if numbers_orig:
                price_str = numbers_orig[0].replace(',', '.')
                price = float(price_str)
                logger.info(f"Preco capturado (original): {price}")
                return price
            
            logger.warning("Nenhum preco encontrado nas imagens")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao ler preco: {e}")
            return None
    
    def test_ocr(self, region=None):
        """Testa o OCR e mostra o que foi lido"""
        if not self.tesseract_ready:
            print("Tesseract nao esta pronto")
            return None
        
        if region is None:
            region = (850, 300, 250, 100)
        
        try:
            x, y, w, h = region
            screenshot = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            screenshot.save('teste_captura.png')
            
            processed = self._preprocess_image(screenshot)
            processed.save('teste_processado.png')
            
            print("Imagens salvas:")
            print(f"  - teste_captura.png (original)")
            print(f"  - teste_processado.png (processado)")
            
            # Detecta o fundo
            is_dark = self._is_dark_background(screenshot)
            print(f"Fundo detectado: {'ESCURO' if is_dark else 'CLARO'}")
            
            # Lê o texto
            text = pytesseract.image_to_string(
                processed,
                lang='eng',
                config='--psm 6'
            )
            
            print(f"\nTexto lido: {text}")
            
            numbers = re.findall(r'(\d+[.,]\d{2,4})', text)
            print(f"Numeros encontrados: {numbers}")
            
            return text
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def analyze_screen(self):
        """Analisa a tela para ajudar a encontrar a região do preço"""
        print("Analisando tela...")
        
        # Captura a tela inteira
        img = ImageGrab.grab()
        img.save('tela_analise.png')
        
        # Tenta encontrar números na tela toda
        is_dark = self._is_dark_background(img)
        print(f"Fundo da tela: {'ESCURO' if is_dark else 'CLARO'}")
        
        if is_dark:
            img_proc = ImageOps.invert(img.convert('L'))
        else:
            img_proc = img.convert('L')
        
        text = pytesseract.image_to_string(img_proc, lang='eng', config='--psm 6')
        
        # Procura números com formato de preço
        numbers = re.findall(r'(\d+[.,]\d{2,4})', text)
        
        if numbers:
            print(f"\nNumeros encontrados na tela: {numbers}")
            print("\nTente ajustar a regiao para capturar apenas a area do preco.")
        else:
            print("\nNenhum numero encontrado. Verifique se a Bull-Ex esta visivel.")
            print("A Bull-Ex pode estar minimizada ou em outra tela.")


def get_price(region=None):
    """Funcao rapida para capturar preco"""
    reader = ScreenReader()
    return reader.get_price_from_screen(region)


def test_ocr(region=None):
    """Funcao para testar o OCR"""
    reader = ScreenReader()
    return reader.test_ocr(region)


def analyze_screen():
    """Analisa a tela para encontrar o preco"""
    reader = ScreenReader()
    return reader.analyze_screen()


if __name__ == "__main__":
    print("Testando OCR com deteccao automatica de cores...")
    reader = ScreenReader()
    
    if reader.tesseract_ready:
        print("Tesseract OK. Capturando preco...")
        price = reader.get_price_from_screen()
        if price:
            print(f"PRECO CAPTURADO: {price}")
        else:
            print("Nenhum preco encontrado.")
            print("")
            print("Analisando a tela para ajudar...")
            reader.analyze_screen()
    else:
        print("Tesseract nao configurado.")