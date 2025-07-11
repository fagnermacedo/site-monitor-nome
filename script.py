import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import re
import datetime
import json
import unicodedata
import io
from urllib.parse import urljoin

# CONFIG
KEYWORDS = ["Fagner do Espírito Santo Sá"]
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/",
    #"https://ioepa.com.br/pages/2025/"
]
TIPOS_ARQUIVOS = [".pdf", ".txt"]
RESULTS_FILE = "resultados.json"
CACHE_VERIFICADOS = "verificados.json"

# === Normalização e busca ===

def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[\r\n\f\t]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
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

# === Função para descobrir links de arquivos em uma página ===

def listar_arquivos_na_pagina(url_base):
    arquivos_encontrados = []
    try:
        resp = requests.get(url_base, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(href.lower().endswith(tipo) for tipo in TIPOS_ARQUIVOS):
                full_url = urljoin(url_base, href)
                arquivos_encontrados.append(full_url)
    except Exception as e:
        print(f"[Erro ao listar arquivos em {url_base}]: {e}")
    return arquivos_encontrados

# === Função principal ===

def verificar_sites():
    registros = []
    data_atual = datetime.datetime.now().isoformat()

    # Carrega cache de arquivos já verificados
    try:
        with open(CACHE_VERIFICADOS, 'r', encoding='utf-8') as f:
            verificados = set(json.load(f))
    except:
        verificados = set()

    for url in URLS:
        print(f"\n🔍 Verificando {url}...")

        if url.lower().endswith(tuple(TIPOS_ARQUIVOS)):
            urls_para_verificar = [url]
        else:
            urls_para_verificar = listar_arquivos_na_pagina(url)

        for arquivo_url in urls_para_verificar:
            if arquivo_url in verificados:
                print(f"⏩ Pulando (já verificado): {arquivo_url}")
                continue

            print(f"➡️ Analisando: {arquivo_url}")
            if arquivo_url.endswith(".pdf"):
                texto = extrair_texto_pdf(arquivo_url)
            else:
                texto = extrair_texto_html(arquivo_url)

            if buscar_palavra_chave(texto):
                print(f"✅ Palavra-chave encontrada em: {arquivo_url}")
                registros.append({
                    "url": arquivo_url,
                    "data": data_atual,
                    "trecho": texto[:300] + "..."
                })

            # Marca como verificado, independente do resultado
            verificados.add(arquivo_url)

    # Salva histórico de resultados encontrados
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            dados_anteriores = json.load(f)
    except:
        dados_anteriores = []

    dados_anteriores.extend(registros)
    dados_anteriores.sort(key=lambda x: x["data"], reverse=True)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_anteriores, f, indent=2, ensure_ascii=False)

    # Salva cache atualizado
    with open(CACHE_VERIFICADOS, 'w', encoding='utf-8') as f:
        json.dump(list(verificados), f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    verificar_sites()
