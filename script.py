# BACKEND - Python Script (script.py)

import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import re
import datetime
import json
import unicodedata
import io

# CONFIG
KEYWORDS = ["Fagner do Espírito Santo Sá"]
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/Ed_6_2025_STM_Res_Final_Obj_Prov_Discursiva_Analista.pdf",
    "https://ioepa.com.br/pages/2025/",
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/"
]
RESULTS_FILE = "resultados.json"

# === Normalização e busca ===

def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')  # remove acentos
    texto = re.sub(r'[\r\n\f\t]', ' ', texto)  # remove quebras de linha e página
    texto = re.sub(r'\s+', ' ', texto)  # colapsa espaços
    return texto.lower()

def buscar_palavra_chave(texto):
    texto_limpo = normalizar(texto)
    for k in KEYWORDS:
        k_limpo = normalizar(k)
        if re.search(rf"\b{k_limpo}\b", texto_limpo):
            return True
    return False

# === Extração de conteúdo ===

def extrair_texto_html(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        texto = soup.get_text(separator=' ', strip=True)
        return texto
    except Exception as e:
        print(f"[Erro HTML] {url}: {e}")
        return ""

def extrair_texto_pdf(url):
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with io.BytesIO(resp.content) as f:
                doc = fitz.open(stream=f, filetype="pdf")
                texto = ""
                for page in doc:
                    texto += page.get_text()
                return texto
        else:
            print(f"[Erro PDF] {url}: status {resp.status_code}")
            return ""
    except Exception as e:
        print(f"[Erro PDF] {url}: {e}")
        return ""

# === Função principal ===

def verificar_sites():
    registros = []
    data_atual = datetime.datetime.now().isoformat()

    for url in URLS:
        print(f"Verificando {url}...")

        if url.lower().endswith(".pdf"):
            texto = extrair_texto_pdf(url)
        else:
            texto = extrair_texto_html(url)

        if buscar_palavra_chave(texto):
            registros.append({
                "url": url,
                "data": data_atual,
                "trecho": texto[:300] + "..."
            })

    # Carrega histórico
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            dados_anteriores = json.load(f)
    except:
        dados_anteriores = []

    # Adiciona novos registros
    dados_anteriores.extend(registros)
    dados_anteriores.sort(key=lambda x: x["data"], reverse=True)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_anteriores, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    verificar_sites()
