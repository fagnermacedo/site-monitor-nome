# BACKEND - Python Script (script.py)

import requests
from bs4 import BeautifulSoup
import re
import datetime
import json
import unicodedata

# CONFIG
KEYWORDS = ["Fagner do Espírito Santo Sá"]  # Pode usar acento, o código normaliza
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/Ed_6_2025_STM_Res_Final_Obj_Prov_Discursiva_Analista.pdf",
    "https://ioepa.com.br/pages/2025/",
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/"
]
RESULTS_FILE = "resultados.json"

# === Funções auxiliares ===

# Remove acentos, quebra de linha e normaliza para comparação
def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')  # Remove acentos
    texto = re.sub(r'[\r\n\f\t]', ' ', texto)  # Remove quebras
    texto = re.sub(r'\s+', ' ', texto)  # Espaços duplos
    return texto.lower()

# Verifica se alguma palavra-chave normalizada aparece no texto normalizado
def buscar_palavra_chave(texto):
    texto_limpo = normalizar(texto)
    for k in KEYWORDS:
        k_limpo = normalizar(k)
        if re.search(rf"\b{k_limpo}\b", texto_limpo):
            return True
    return False

# Extrai texto de página HTML
def extrair_texto_html(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        texto = soup.get_text(separator=' ', strip=True)
        return texto
    except Exception as e:
        print(f"[Erro HTML] {url}: {e}")
        return ""

# === Função principal ===

def verificar_sites():
    registros = []
    data_atual = datetime.datetime.now().isoformat()

    for url in URLS:
        print(f"Verificando {url}...")

        # Somente páginas HTML são tratadas neste script
        if url.lower().endswith(".pdf"):
            print(f" (PDF ignorado por enquanto: {url})")
            continue

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

    # Adiciona novos e ordena
    dados_anteriores.extend(registros)
    dados_anteriores.sort(key=lambda x: x["data"], reverse=True)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_anteriores, f, indent=2, ensure_ascii=False)

if __name__ == '__main__':
    verificar_sites()
