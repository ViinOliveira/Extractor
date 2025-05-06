from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import re

# Caminho para o chromedriver
CHROME_DRIVER_PATH = "caminho/para/seu/chromedriver"

# Lista simulada dos candidatos
candidatos = [
    {
        "nome": "Marcos",
        "telefone": "(11) 91234-5678",
        "empresa": "PAO DE ACUCAR / EXTRA HIPERMERCADOS - Repositor de Mercadoria",
        "periodo": "03/2015 até 08/2024"
    },
    # Adicione mais candidatos aqui
]

def iniciar_whatsapp():
    options = Options()
    options.add_argument("--user-data-dir=./perfil_whatsapp")  # mantém a sessão logada
    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    driver.get("https://web.whatsapp.com")
    print("Escaneie o QR code se ainda não estiver logado.")
    time.sleep(20)  # tempo para login manual
    return driver

def enviar_mensagem(driver, candidato):
    nome = candidato["nome"]
    telefone = candidato["telefone"]
    empresa = candidato["empresa"]
    periodo = candidato["periodo"]

    numero = re.sub(r"[^\d]", "", telefone)
    mensagem = f"""Boa tarde {nome} tudo bem? Sou o Gabriel, da Batista & Camargo assessoria, o motivo do meu contato é referente a empresa,

{empresa}

Cargo: {empresa.split(' - ')[1]} - {periodo}

Assim que possível me retorne. Grato."""

    link = f"https://wa.me/55{numero}?text={mensagem.replace(' ', '%20')}"
    driver.get(link)
    time.sleep(10)

    try:
        # Espera o botão de enviar aparecer
        botao_enviar = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
        botao_enviar.click()
        print(f"Mensagem enviada para {nome}")
    except Exception as e:
        print(f"Erro ao enviar para {nome}: {e}")

def envio_em_lote(candidatos):
    driver = iniciar_whatsapp()
    for i, c in enumerate(candidatos):
        enviar_mensagem(driver, c)
        if i < len(candidatos) - 1:
            print("Aguardando 7 minutos...")
            time.sleep(420)
    driver.quit()

# Executar envio
envio_em_lote(candidatos)
