# BACKEND - Python Script (script.py)

import requests
from bs4 import BeautifulSoup
import re
import datetime
import json

# CONFIG
KEYWORDS = ["Seu Nome Aqui"]
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/Ed_6_2025_STM_Res_Final_Obj_Prov_Discursiva_Analista.pdf",
    "https://ioepa.com.br/pages/2025/",
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/"
]
RESULTS_FILE = "resultados.json"

# Função para extrair texto de página HTML
def extrair_texto_html(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        texto = soup.get_text(separator=' ', strip=True)
        return texto
    except Exception as e:
        return ""

# Verifica se alguma palavra-chave está no texto
def buscar_palavra_chave(texto):
    for k in KEYWORDS:
        if re.search(rf"\b{k}\b", texto, re.IGNORECASE):
            return True
    return False

# Função principal
def verificar_sites():
    registros = []
    data_atual = datetime.datetime.now().isoformat()

    for url in URLS:
        print(f"Verificando {url}...")
        texto = extrair_texto_html(url)

        if buscar_palavra_chave(texto):
            registros.append({
                "url": url,
                "data": data_atual,
                "trecho": texto[:300] + "..."
            })

    # Carrega dados antigos
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            dados_anteriores = json.load(f)
    except:
        dados_anteriores = []

    # Adiciona novos
    dados_anteriores.extend(registros)
    dados_anteriores.sort(key=lambda x: x["data"], reverse=True)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_anteriores, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    verificar_sites()
