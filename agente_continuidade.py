import requests
import json
import os
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES (SUBSTITUA SUA CHAVE AQUI)
# ==========================================
SUA_CHAVE_OPENROUTER = "xxxxxxxxxxxxxxxx"  # COLE SUA CHAVE VERDADEIRA AQUI
ARQUIVO_CONTINUIDADE = "continuidade_conversa.json"
ARQUIVO_RESUMO_ULTIMO = "resumo_ultimo.txt"

# ==========================================
# PERGUNTA INICIAL: QUER COMEÇAR UMA NOVA CONVERSA?
# ==========================================
print("\n📋 O que você deseja fazer?")
print("1 - Continuar a conversa atual")
print("2 - 🗑️ COMEÇAR UMA NOVA CONVERSA (apaga o histórico atual)")

opcao_inicial = input("Digite 1 ou 2: ")

if opcao_inicial == "2":
    confirmacao = input("⚠️ Tem certeza que quer apagar TODO o histórico e começar do zero? (digite 's' para confirmar): ")
    if confirmacao.lower() == "s":
        if os.path.exists(ARQUIVO_CONTINUIDADE):
            os.remove(ARQUIVO_CONTINUIDADE)
            print("🗑️ Histórico antigo apagado! Nova conversa iniciada.")
    else:
        print("✅ Operação cancelada. Continuando com o histórico atual.")

# ==========================================
# MENU PARA ESCOLHER A IA
# ==========================================
print("\n🤖 ESCOLHA A INTELIGÊNCIA ARTIFICIAL PARA CONVERSAR:")
print("1 - DeepSeek (Raciocínio profundo)")
print("2 - Qwen 2.5 (Rápida e gratuita)")
print("3 - Kimi K2.5 (Raciocínio explícito)")

opcao_ia = input("Digite 1, 2 ou 3: ")

if opcao_ia == "1":
    modelo_escolhido = "deepseek/deepseek-chat"
    nome_ia = "DeepSeek"
    raciocinio_ativado = False
elif opcao_ia == "2":
    modelo_escolhido = "qwen/qwen-2.5-72b-instruct"
    nome_ia = "Qwen 2.5"
    raciocinio_ativado = False
elif opcao_ia == "3":
    modelo_escolhido = "moonshotai/kimi-k2.5"
    nome_ia = "Kimi K2.5"
    raciocinio_ativado = True
else:
    modelo_escolhido = "qwen/qwen-2.5-72b-instruct"
    nome_ia = "Qwen 2.5 (padrão)"
    raciocinio_ativado = False
    print("⚠️ Opção inválida! Usando Qwen como padrão.")

print(f"\n✅ Conectado ao modelo: {nome_ia}")
if raciocinio_ativado:
    print("🧠 Modo raciocínio explícito ATIVADO")
print("-" * 50)

# ==========================================
# FUNÇÕES DE HISTÓRICO E RESUMO
# ==========================================
def carregar_historico():
    if os.path.exists(ARQUIVO_CONTINUIDADE):
        with open(ARQUIVO_CONTINUIDADE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"mensagens": [], "tokens_gastos": 0}

def salvar_historico(historico):
    with open(ARQUIVO_CONTINUIDADE, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=4, ensure_ascii=False)

def gerar_resumo_automatico(historico):
    """Gera dois resumos: um com data/hora e um 'ultimo' sempre atualizado."""
    if not historico["mensagens"]:
        print("ℹ️ Nenhuma mensagem para resumir.")
        return
    
    print("\n📝 Gerando resumo automático...")
    
    # Pega as últimas 10 mensagens para resumir
    ultimas_msg = historico["mensagens"][-10:]
    texto_para_resumir = ""
    for msg in ultimas_msg:
        papel = "Usuário" if msg["role"] == "user" else "Assistente"
        texto_para_resumir += f"{papel}: {msg['content'][:300]}...\n"
    
    headers = {
        "Authorization": f"Bearer {SUA_CHAVE_OPENROUTER}",
        "Content-Type": "application/json",
    }
    
    dados = {
        "model": "qwen/qwen-2.5-72b-instruct",
        "messages": [
            {"role": "system", "content": "Você é um assistente que resume conversas de forma clara e objetiva, destacando os assuntos principais, dúvidas e decisões tomadas."},
            {"role": "user", "content": f"Resuma esta conversa em até 10 linhas para que eu possa continuar de onde parei em um novo chat:\n\n{texto_para_resumir}"}
        ],
        "max_tokens": 500,
    }
    
    try:
        resposta = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=dados)
        resposta.raise_for_status()
        resultado = resposta.json()
        resumo = resultado["choices"][0]["message"]["content"]
        
        # 1. Salva o resumo com data/hora (NUNCA sobrescreve)
        agora = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nome_com_data = f"resumo_{agora}.txt"
        with open(nome_com_data, "w", encoding="utf-8") as f:
            f.write(resumo)
        print(f"✅ Resumo com data salvo em: {nome_com_data}")
        
        # 2. Salva o resumo como "ultimo" (sempre sobrescreve)
        with open(ARQUIVO_RESUMO_ULTIMO, "w", encoding="utf-8") as f:
            f.write(resumo)
        print(f"✅ Resumo atualizado em: {ARQUIVO_RESUMO_ULTIMO}")
        
        # 3. Mostra o resumo na tela para copiar
        print("\n📋 Resumo gerado (copie o texto abaixo):\n")
        print("-" * 50)
        print(resumo)
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Erro ao gerar resumo: {e}")

# ==========================================
# FUNÇÃO PARA PERGUNTAR À IA
# ==========================================
def perguntar_ia(historico, pergunta_usuario):
    mensagens = historico["mensagens"].copy()
    mensagens.append({"role": "user", "content": pergunta_usuario})

    headers = {
        "Authorization": f"Bearer {SUA_CHAVE_OPENROUTER}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/roselyssousa/AgenteIA",
        "X-Title": "Agente IA Professora Rosely",
    }

    dados = {
        "model": modelo_escolhido,
        "messages": mensagens,
        "max_tokens": 1000,
    }

    if raciocinio_ativado:
        dados["reasoning"] = {"enabled": True}

    try:
        resposta = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=dados)
        resposta.raise_for_status()
        resultado = resposta.json()
        
        texto_resposta = resultado["choices"][0]["message"]["content"]
        raciocinio = resultado["choices"][0].get("reasoning", "")
        if raciocinio:
            texto_resposta = f"[Raciocínio]\n{raciocinio}\n\n[Resposta final]\n{texto_resposta}"
        
        tokens_usados = resultado.get("usage", {}).get("total_tokens", 0)
        
        historico["mensagens"].append({"role": "user", "content": pergunta_usuario})
        historico["mensagens"].append({"role": "assistant", "content": texto_resposta})
        historico["tokens_gastos"] += tokens_usados
        
        return texto_resposta, historico, tokens_usados

    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na conexão com a API: {e}")
        return None, historico, 0
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return None, historico, 0

# ==========================================
# LOOP PRINCIPAL
# ==========================================
def main():
    historico = carregar_historico()
    print(f"\n📚 Histórico carregado. Tokens gastos até agora: {historico['tokens_gastos']}\n")
    
    limite_alerta = 2000
    
    while True:
        pergunta = input(f"\n🧑‍🏫 Você (para {nome_ia}): ")
        if pergunta.lower() in ["sair", "exit", "fim"]:
            print("👋 Gerando resumo e salvando seu progresso...")
            gerar_resumo_automatico(historico)
            salvar_historico(historico)
            print("Até logo!")
            break
        
        resposta, historico, tokens_uso = perguntar_ia(historico, pergunta)
        
        if resposta:
            print(f"\n🤖 {nome_ia}: {resposta}")
            print(f"\n📊 Tokens usados nesta mensagem: {tokens_uso}")
            print(f"📊 Total de tokens acumulados: {historico['tokens_gastos']}")
            
            salvar_historico(historico)
            
            if historico['tokens_gastos'] > limite_alerta:
                print("\n⚠️ ATENÇÃO: Você passou de 2000 tokens gastos!")
                print("💡 Quando digitar 'sair', o resumo será gerado automaticamente.")
        else:
            print("❌ Não consegui obter resposta. Verifique sua chave e conexão.")

if __name__ == "__main__":
    main()
