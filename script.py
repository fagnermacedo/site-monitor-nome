import os
import json
import fitz  # PyMuPDF
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin  # 🔧 IMPORTADO PARA CORREÇÃO

# CONFIGURAÇÕES
KEYWORDS = ["Fagner do Espírito Santo Sá"]
URLS = [
    "https://cdn.cebraspe.org.br/concursos/STM_25/arquivos/",
    "https://www.cebraspe.org.br/concursos/STM_25",
    # "https://www.cebraspe.org.br/concursos/cpnuje_24",
    # "https://cdn.cebraspe.org.br/concursos/cpnuje_24/arquivos/",
    "https://ioepa.com.br/pages/2025/"
]
RESULTS_FILE = "resultados.json"
CACHE_FILE = "verificados.json"

# Funções auxiliares
def carregar_json(caminho, padrao):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return padrao

def salvar_json(dados, caminho):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def extrair_links(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return [link.get("href") for link in soup.find_all("a") if link.get("href", "").endswith((".pdf", ".txt"))]
    except Exception as e:
        print(f"❌ Erro ao acessar {url}: {e}")
        return []

def buscar_ocorrencias_em_pdf(link):
    try:
        response = requests.get(link, timeout=15)
        response.raise_for_status()
        doc = fitz.open("pdf", response.content)
        texto = "\n".join([page.get_text() for page in doc])
        return [kw for kw in KEYWORDS if kw.lower() in texto.lower()]
    except Exception as e:
        print(f"⚠️ Erro ao processar PDF {link}: {e}")
        return []

# Execução
verificados = carregar_json(CACHE_FILE, [])
resultados = carregar_json(RESULTS_FILE, [])

diagnostico = {
    "data_execucao": datetime.now().isoformat(),
    "total_arquivos_verificados": 0,
    "arquivos_novos_analisados": 0,
    "ocorrencias_encontradas": 0,
    "erros_ocorridos": []
}

novos_verificados = []
for base_url in URLS:
    links = extrair_links(base_url)
    for link in links:
        if not link.startswith("http"):
            link = urljoin(base_url + "/", link)  # ✅ CORREÇÃO FEITA AQUI

        if link in verificados or link in novos_verificados:
            print(f"✔️ Já verificado: {link}")
            continue

        print(f"📄 Lendo arquivo: {link}")
        diagnostico["total_arquivos_verificados"] += 1
        ocorrencias = []

        if link.endswith(".pdf"):
            ocorrencias = buscar_ocorrencias_em_pdf(link)

        if ocorrencias:
            print(f"🔎 Palavra-chave encontrada em {link}")
            resultados.append({
                "link": link,
                "ocorrencias": ocorrencias,
                "data_encontrada": datetime.now().isoformat()
            })
            diagnostico["ocorrencias_encontradas"] += 1

        novos_verificados.append(link)
        diagnostico["arquivos_novos_analisados"] += 1

# Atualiza cache e resultados
verificados.extend(novos_verificados)
salvar_json(sorted(set(verificados)), CACHE_FILE)
salvar_json(resultados, RESULTS_FILE)

# Diagnóstico final
print("📊 Diagnóstico da execução:")
print(json.dumps(diagnostico, indent=2, ensure_ascii=False))
