import os
import re
import json
import datetime
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from urllib.parse import urljoin
from io import BytesIO
from shutil import copyfile

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


def carregar_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()


def salvar_resultados(resultados):
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            dados_existentes = json.load(f)
    else:
        dados_existentes = []

    dados_existentes.extend(resultados)

    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados_existentes, f, indent=2, ensure_ascii=False)


def extrair_texto_pdf(conteudo):
    try:
        leitor = PdfReader(BytesIO(conteudo))
        texto = ""
        for pagina in leitor.pages:
            texto += pagina.extract_text() or ""
        return texto
    except Exception as e:
        print(f"⚠️ Erro ao ler PDF: {e}")
        return ""


def extrair_texto_txt(conteudo):
    try:
        return conteudo.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ Erro ao ler TXT: {e}")
        return ""


def verificar_sites():
    verificados = carregar_cache()
    novos_resultados = []
    erros = []
    total_verificados = 0
    novos_analisados = 0

    for url_base in URLS:
        try:
            resposta = requests.get(url_base)
            resposta.raise_for_status()
            soup = BeautifulSoup(resposta.text, 'html.parser')

            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href.endswith(('.pdf', '.txt')):
                    url_completa = urljoin(url_base, href)
                    total_verificados += 1

                    if url_completa in verificados:
                        print(f"✔️ Já verificado: {url_completa}")
                        continue

                    try:
                        resp_arquivo = requests.get(url_completa)
                        resp_arquivo.raise_for_status()

                        print(f"📄 Lendo arquivo: {url_completa}")
                        if href.endswith('.pdf'):
                            texto = extrair_texto_pdf(resp_arquivo.content)
                        else:
                            texto = extrair_texto_txt(resp_arquivo.content)

                        encontrou = False
                        for palavra in KEYWORDS:
                            if re.search(re.escape(palavra), texto, re.IGNORECASE):
                                print(f"🔍 Palavra-chave encontrada: '{palavra}' em {url_completa}")
                                novos_resultados.append({
                                    "url": url_completa,
                                    "palavra_chave": palavra,
                                    "data_encontrado": datetime.datetime.now().isoformat()
                                })
                                encontrou = True
                                break

                        novos_analisados += 1
                        verificados.add(url_completa)

                    except Exception as e:
                        print(f"❌ Erro ao processar {url_completa}: {e}")
                        erros.append({"url": url_completa, "erro": str(e)})

        except Exception as e:
            print(f"❌ Erro ao acessar {url_base}: {e}")
            erros.append({"url_base": url_base, "erro": str(e)})

    if novos_resultados:
        salvar_resultados(novos_resultados)

    # SALVAMENTO ROBUSTO DO CACHE
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(verificados)), f, indent=2, ensure_ascii=False)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"verificados_backup_{timestamp}.json"
        copyfile(CACHE_FILE, backup_path)

        print(f"💾 Cache salvo com sucesso: {len(verificados)} URLs verificados.")
        print(f"📁 Backup salvo: {backup_path}")

    except Exception as e:
        print(f"❌ Erro ao salvar o cache: {e}")
        erros.append({"etapa": "salvar_cache", "erro": str(e)})

    # DIAGNÓSTICO FINAL
    print("📊 Diagnóstico da execução:")
    print(json.dumps({
        "data_execucao": datetime.datetime.now().isoformat(),
        "total_arquivos_verificados": total_verificados,
        "arquivos_novos_analisados": novos_analisados,
        "ocorrencias_encontradas": len(novos_resultados),
        "erros_ocorridos": erros
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    verificar_sites()
