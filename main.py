import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import time
import threading
import pdfplumber
import pandas as pd
import re
import webbrowser
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import requests
import zipfile
import shutil
import subprocess
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import uuid
import hashlib
import ctypes

# Impede o Windows de suspender ou apagar a tela enquanto o app estiver rodando
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

ctypes.windll.kernel32.SetThreadExecutionState(
    ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
)

CACHE_LICENCA = "licenca_cache.json"


def gerar_id_unico():
    mac = uuid.getnode()
    mac_str = ':'.join(['{:02x}'.format((mac >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1])
    return hashlib.sha256(mac_str.encode()).hexdigest()

def verificar_licenca_remota():
    id_usuario = gerar_id_unico()
    verificar_atualizacao()

    # Verifica cache local
    if os.path.exists(CACHE_LICENCA):
        with open(CACHE_LICENCA, "r") as f:
            dados = json.load(f)
            if dados.get("id") == id_usuario and time.time() - dados.get("timestamp", 0) < 86400:
                return  # Licença ainda válida pelo cache

    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ_ilzA0n_pOBaudL3zGdv7t7qF9vWSvDPBU3UNBB65LMZA_94F_cT3-62ZjfYPi3VUEFDSiWAMC61O/pub?output=csv"
        conteudo = requests.get(url, timeout=5).text
        if id_usuario in conteudo:
            # Salva no cache por 24h
            with open(CACHE_LICENCA, "w") as f:
                json.dump({"id": id_usuario, "timestamp": time.time()}, f)
            return
        else:
            raise Exception("ID não autorizado")
    except Exception as e:
        messagebox.showerror("Licença revogada",
                             f"Licença não válida ou não autorizada.\n\nID: {id_usuario}\n\n"
                             f"Entre em contato pelo e-mail: innotehconsulting@gmail.com")
        sys.exit()

VERSAO_ATUAL = "1.0.0"

def verificar_atualizacao():
    try:
        url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vXXXXXX/pub?output=csv"  # substitua pelo seu link real
        conteudo = requests.get(url, timeout=5).text.strip()
        if conteudo and conteudo != VERSAO_ATUAL:
            messagebox.showinfo("Atualização disponível",
                                f"Você está usando a versão {VERSAO_ATUAL}.\n"
                                f"A nova versão disponível é {conteudo}.\n\nAcesse o site para baixar a atualização.")
    except Exception as e:
        print(f"Falha ao verificar atualização: {e}")


parar_envio = False

def extrair_candidatos(pdf_path):
    import pdfplumber
    import re

    candidatos = []

    with pdfplumber.open(pdf_path) as pdf:
        texto = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())

    blocos = re.split(r"(\d{2}\s+anos[,;.\s])", texto)
    blocos = ["".join(blocos[i:i+2]) for i in range(0, len(blocos), 2)]

    for bloco in blocos:
        bloco = bloco.strip()
        linhas = bloco.splitlines()

        # Nome
        nome = "Nome não identificado"
        nome_match = re.search(r"Nome:\s*(.*)", bloco)
        if nome_match:
            nome = nome_match.group(1).strip()
        else:
            for i, linha in enumerate(linhas):
                if re.search(r"\d{2}\s+anos", linha):
                    if i > 0:
                        nome = linhas[i - 1].strip()
                    break

        # Telefone
        telefones = re.findall(r"\(?\d{2}\)?\s*\d{4,5}-\d{4}", bloco)
        telefone = telefones[0] if telefones else "Não informado"

        # Experiência Profissional
        experiencias = re.findall(
            r"Cargo:\s*(.*?)\s*-\s*(\d{2}/\d{4}) até (\d{2}/\d{4})", bloco, re.IGNORECASE
        )
        if not experiencias:
            continue

        for cargo, inicio, fim in experiencias:
            try:
                mes_fim, ano_fim = map(int, fim.split("/"))
                if ano_fim > 2023 or (ano_fim == 2023 and mes_fim >= 5):
                    empresa_match = re.search(r"Experiência Profissional\s*\n*(.*?)\n*Cargo:", bloco, re.DOTALL)
                    empresa = empresa_match.group(1).strip() if empresa_match else "Empresa não identificada"

                    # ⛔️ Se nome ou telefone estiverem incompletos, ignora
                    if nome == "Nome não identificado" or telefone == "Não informado":
                        break

                    candidatos.append({
                        "nome": nome,
                        "telefone": telefone,
                        "empresa": f"{empresa} - {cargo}",
                        "periodo": f"{inicio} até {fim}"
                    })
                    break
            except:
                continue

    return candidatos


ARQUIVO_ENVIADOS = "enviados.json"

def carregar_enviados():
    if os.path.exists(ARQUIVO_ENVIADOS):
        with open(ARQUIVO_ENVIADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salvar_enviados(lista):
    with open(ARQUIVO_ENVIADOS, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)

# Interface gráfica (sem alterações)
def selecionar_pdf():
    caminhos = filedialog.askopenfilenames(filetypes=[("Arquivos PDF", "*.pdf")])
    if not caminhos:
        return

    todos_candidatos = []
    for caminho in caminhos:
        candidatos = extrair_candidatos(caminho)
        todos_candidatos.extend(candidatos)

    if not todos_candidatos:
        messagebox.showinfo("Aviso", "Nenhum candidato encontrado nos PDFs selecionados.")
        return

    tabela.delete(*tabela.get_children())
    for c in todos_candidatos:
        tabela.insert("", "end", values=(c["nome"], c["telefone"], c["empresa"], c["periodo"]))

    global dados_extraidos
    dados_extraidos = todos_candidatos
    messagebox.showinfo("Sucesso", f"{len(todos_candidatos)} candidatos encontrados em {len(caminhos)} arquivo(s).")

def exportar_csv():
    if not dados_extraidos:
        messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
        return
    caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if caminho:
        df = pd.DataFrame(dados_extraidos)
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        messagebox.showinfo("Exportado", "Arquivo salvo com sucesso!")

def excluir_candidato():
    itens_selecionados = tabela.selection()
    if not itens_selecionados:
        messagebox.showwarning("Aviso", "Selecione um ou mais candidatos para excluir.")
        return

    resposta = messagebox.askyesno("Confirmação", f"Deseja realmente excluir {len(itens_selecionados)} candidato(s)?")
    if not resposta:
        return

    global dados_extraidos, parar_envio
    excluidos = []

    for item in itens_selecionados:
        valores = tabela.item(item, "values")
        nome, telefone = valores[0], valores[1]
        excluidos.append((nome, telefone))
        tabela.delete(item)

    # Remove os candidatos da lista
    dados_extraidos = [c for c in dados_extraidos if (c["nome"], c["telefone"]) not in excluidos]
    parar_envio = False

def parar_envio_func():
    global parar_envio
    parar_envio = True
    messagebox.showinfo("Parado", "Envio em lote será interrompido após o atual.")


def enviar_whatsapp_em_lote():
    if not dados_extraidos:
        messagebox.showwarning("Aviso", "Nenhum candidato para enviar mensagem.")
        return

    def processo_envio():
        global parar_envio
        parar_envio = False
        btn_lote.config(state="disabled")

        enviados = carregar_enviados()
        enviados_set = {(c["nome"], c["telefone"]) for c in enviados}

        candidatos_para_enviar = [c for c in dados_extraidos if (c["nome"], c["telefone"]) not in enviados_set]

        if not candidatos_para_enviar:
            messagebox.showinfo("Aviso", "Todos os candidatos já foram contatados.")
            return

        try:
            base_path = os.path.dirname(sys.executable)
            chromedriver_path = os.path.join(base_path, "chromedriver.exe")
            perfil_path = os.path.join(base_path, "perfil_whatsapp")

            if not os.path.exists(chromedriver_path):
                messagebox.showerror("Erro", "chromedriver.exe não encontrado.\nColoque o ChromeDriver na mesma pasta do aplicativo.")
                return

            os.makedirs(perfil_path, exist_ok=True)

            options = Options()
            options.add_argument(f"--user-data-dir={perfil_path}")

            driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
            driver.get("https://web.whatsapp.com")
            time.sleep(30)

            for idx, c in enumerate(candidatos_para_enviar):
                if parar_envio:
                    print("🚫 Envio interrompido pelo usuário.")
                    break

                nome = c["nome"]
                telefone = c["telefone"]
                empresa = c["empresa"]
                periodo = c["periodo"]

                if telefone == "Não informado" or nome == "Nome não identificado":
                    continue

                numero = re.sub(r"[^\d]", "", telefone)
                if len(numero) < 10:
                    continue

                mensagem = f"""Boa tarde {nome} tudo bem? Sou o Gabriel, da Batista & Camargo assessoria, o motivo do meu contato é referente a empresa,

            {empresa}

            Cargo: {empresa.split(' - ')[1]} - {periodo}

            Assim que possível me retorne. Grato."""

                link = f"https://web.whatsapp.com/send?phone=55{numero}&text={quote(mensagem)}"
                driver.get(link)
                time.sleep(8)

                conversa_existente = False
                try:
                    driver.find_element(By.XPATH, '//div[@data-testid="conversation-info-header"]')
                    conversa_existente = True
                except:
                    pass

                if conversa_existente:
                    print(f"[{idx+1}/{len(candidatos_para_enviar)}] ❌ Já existe conversa com {nome}. Pulando.")
                    continue

                try:
                    seletores_envio = [
                        (By.XPATH, '//span[@data-icon="wds-ic-send-filled"]/ancestor::button'),
                        (By.CSS_SELECTOR, 'span[data-icon="send"]'),
                        (By.XPATH, '//span[@aria-hidden="true"]//svg[@title="send"]/ancestor::button'),
                        (By.XPATH, '//button[@data-testid="compose-btn-send"]'),
                        (By.XPATH, '//button[contains(@class, "send") or @aria-label="Send"]'),
                    ]

                    enviar_btn = None
                    for by, seletor in seletores_envio:
                        try:
                            enviar_btn = WebDriverWait(driver, 10).until(
                                EC.element_to_be_clickable((by, seletor))
                            )
                            if enviar_btn:
                                break
                        except:
                            continue

                    if enviar_btn:
                        enviar_btn.click()
                        print(f"[{idx+1}/{len(candidatos_para_enviar)}] ✅ Mensagem enviada para {nome}")
                        enviados.append(c)
                        salvar_enviados(enviados)
                    else:
                        raise Exception("Botão de envio não encontrado com nenhum seletor.")

                except Exception as e:
                    print(f"[{idx+1}/{len(candidatos_para_enviar)}] ⚠️ Botão de envio não encontrado para {nome}. Pulando.")
                    print(f"Erro: {e}")

                percentual = ((idx+1) / len(candidatos_para_enviar)) * 100
                progress['value'] = percentual
                status_label.config(text=f"Mensagem enviada para {nome}")
                janela.update_idletasks()

                if idx < len(candidatos_para_enviar) - 1:
                    print("Aguardando 5 minutos...")
                    time.sleep(300)


        except Exception as erro:
                messagebox.showerror("Erro crítico", f"Falha ao iniciar o Chrome:\n\n{erro}")
        finally:
            btn_lote.config(state="normal")
            try:
                if driver:
                    driver.quit()
            except:
                pass

    threading.Thread(target=processo_envio, daemon=True).start()

verificar_licenca_remota()

# Janela principal
janela = tk.Tk()
janela.title("Catho Extractor - Envio via WhatsApp")
janela.geometry("800x500")
janela.minsize(800, 500)
janela.configure(bg="#f2f2f2")

# Título no topo
lbl_titulo = tk.Label(janela, text="Catho Extractor", font=("Arial", 18, "bold"), bg="#f2f2f2", fg="#333")
lbl_titulo.pack(pady=10)

# Barra de progresso
progress = ttk.Progressbar(janela, orient='horizontal', length=400, mode='determinate')
progress.pack(pady=10)

# Texto de status
status_label = tk.Label(janela, text="Aguardando início...", font=('Arial', 12), bg="#f2f2f2")
status_label.pack(pady=5)

# Frame dos botões
frame_botoes = tk.Frame(janela, bg="#f2f2f2")
frame_botoes.pack(pady=10)

btn_pdf = tk.Button(frame_botoes, text="Selecionar PDF", command=selecionar_pdf, width=20)
btn_pdf.grid(row=0, column=0, padx=10)

btn_exportar = tk.Button(frame_botoes, text="Exportar CSV", command=exportar_csv, width=20)
btn_exportar.grid(row=0, column=1, padx=10)

btn_lote = tk.Button(frame_botoes, text="WhatsApp em Lote", command=enviar_whatsapp_em_lote, width=20)
btn_lote.grid(row=0, column=2, padx=10)

btn_excluir = tk.Button(frame_botoes, text="Excluir Selecionado", command=excluir_candidato, width=20)
btn_excluir.grid(row=0, column=3, padx=10)

btn_parar = tk.Button(frame_botoes, text="Parar Envio", command=parar_envio_func, width=20)
btn_parar.grid(row=0, column=4, padx=10)

# Tabela de candidatos
colunas = ("nome", "telefone", "empresa", "periodo")
tabela = ttk.Treeview(janela, columns=colunas, show="headings", height=12)
for col in colunas:
    tabela.heading(col, text=col.capitalize())
    tabela.column(col, width=180 if col != "telefone" else 120)

tabela.pack(padx=10, pady=10, fill="both", expand=True)
dados_extraidos = []

# Estilos visuais
style = ttk.Style(janela)
style.theme_use("clam")
style.configure("TButton", font=("Arial", 10), padding=6)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#4a90e2", foreground="white")
style.configure("Treeview", font=("Arial", 10), rowheight=26)

# Execução
def ao_fechar():
    # Restaura o comportamento padrão de energia
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    janela.destroy()

# Garante que o sistema volte ao normal ao fechar
janela.protocol("WM_DELETE_WINDOW", ao_fechar)

# Estilos visuais
style = ttk.Style(janela)
style.theme_use("clam")
style.configure("TButton", font=("Arial", 10), padding=6)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#4a90e2", foreground="white")
style.configure("Treeview", font=("Arial", 10), rowheight=26)

# Restaura o modo de energia ao fechar
def ao_fechar():
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    janela.destroy()

janela.protocol("WM_DELETE_WINDOW", ao_fechar)

# Execução
janela.mainloop()

