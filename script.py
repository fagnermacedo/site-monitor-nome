# IMPORTAÇÕES
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import re
import datetime
import json
import unicodedata
import io
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import tempfile
import time

# CONFIGURAÇÕES
KEYWORDS = ["Fagner do Espírito Santo Sá"]
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/",
    "https://www.cebraspe.org.br/concursos/STM_25",
    "https://www.cebraspe.org.br/concursos/cpnuje_24",
    "https://cdn.cebraspe.org.br/concursos/cpnuje_24/arquivos/",
    "https://ioepa.com.br/pages/2025/"
]
RESULTS_FILE = "resultados.json"
CACHE_FILE = "verificados.json"

# === FUNÇÕES DE NORMALIZAÇÃO E BUSCA ===

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

# === EXTRAÇÃO DE CONTEÚDO ===

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

def extrair_texto_html(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.get_text(separator=' ', strip=True)
    except Exception as e:
        print(f"[Erro HTML] {url}: {e}")
        return ""

# === FUNÇÃO PARA LISTAR PDFs USANDO SELENIUM ===

def listar_arquivos_com_selenium(url):
    print(f"🧭 Buscando arquivos na página (Selenium): {url}")
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")

        # SOLUÇÃO: diretório de usuário temporário
        temp_dir = tempfile.mkdtemp()
        options.add_argument(f"--user-data-dir={temp_dir}")

        # Chrome em ambiente Linux do GitHub Actions
        options.binary_location = "/usr/bin/chromium-browser"
        driver = webdriver.Chrome(options=options)

        driver.get(url)
        import time
        time.sleep(5)

        html = driver.page_source
        driver.quit()

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)
                 if a['href'].lower().endswith(('.pdf', '.txt'))]

        # Corrigir links relativos
        final_links = []
        for link in links:
            if link.startswith("http"):
                final_links.append(link)
            elif link.startswith("/"):
                import re
                base = re.match(r"^(https?://[^/]+)", url).group(1)
                final_links.append(base + link)
            else:
                final_links.append(url.rstrip("/") + "/" + link)

        return final_links
    except Exception as e:
        print(f"[Erro Selenium] {url}: {e}")
        return []

# === VERIFICAÇÃO PRINCIPAL ===

def verificar_sites():
    data_atual = datetime.datetime.now().isoformat()
    registros = []

    # Carregar cache de arquivos verificados
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            verificados = set(json.load(f))
    except:
        verificados = set()

    for url in URLS:
        print(f"\n🔍 Verificando URL: {url}")

        arquivos = []
        if url.lower().endswith(('.pdf', '.txt')):
            arquivos = [url]
        elif "cebraspe.org.br" in url:
            arquivos = listar_arquivos_com_selenium(url)
        else:
            arquivos = []  # futura melhoria: tratar diretórios HTML simples

        for arq in arquivos:
            if arq in verificados:
                print(f"✔️ Já verificado: {arq}")
                continue

            print(f"📄 Lendo arquivo: {arq}")
            texto = extrair_texto_pdf(arq) if arq.endswith(".pdf") else extrair_texto_html(arq)

            if buscar_palavra_chave(texto):
                print(f"🔎 Palavra-chave encontrada em: {arq}")
                registros.append({
                    "url": arq,
                    "data": data_atual,
                    "trecho": texto[:300] + "..."
                })

            verificados.add(arq)

    # Salva resultados
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            dados_anteriores = json.load(f)
    except:
        dados_anteriores = []

    dados_anteriores.extend(registros)
    dados_anteriores.sort(key=lambda x: x["data"], reverse=True)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_anteriores, f, indent=2, ensure_ascii=False)

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(verificados), f, indent=2, ensure_ascii=False)

# === EXECUÇÃO ===

if __name__ == '__main__':
    verificar_sites()
