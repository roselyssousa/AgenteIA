# ==========================================
# AGENTE COMPLETO - Monitoramento + Continuidade
# ==========================================

import json
import requests
from datetime import datetime

# 1. CONFIGURAÇÃO
API_KEY = "sk-or-v1-27dXXXXXXXXXXXXXXXX"  # <-- SUA CHAVE AQUI
MODELO = "qwen/qwen-2.5-72b-instruct"
LIMITE_CONTEXTO = 128000
THRESHOLD_ALERTA = 0.75
ARQUIVO_CONTINUIDADE = "continuidade_conversa.json"

class AgenteContinuidade:
    def __init__(self):
        self.mensagens = []
        self.total_tokens = 0
        self.historico_completo = []
    
    def carregar_continuidade(self, arquivo=ARQUIVO_CONTINUIDADE):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                dados = json.load(f)
            print(f"✅ Carregando continuidade de: {dados['data_geracao']}")
            self.mensagens.append({
                "role": "system", 
                "content": f"CONTEXTO DA CONVERSA ANTERIOR:\n{dados['resumo_estruturado']}\n\nContinue a conversa de onde parou."
            })
            self.total_tokens = dados['tokens_usados']
            return True
        except FileNotFoundError:
            print("🆕 Nova conversa iniciada\n")
            return False
    
    def enviar_para_llm(self, pergunta: str):
        self.mensagens.append({"role": "user", "content": pergunta})
        self.historico_completo.append({"papel": "usuário", "texto": pergunta})
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://openrouter.ai",
        }
        
        dados = {
            "model": MODELO,
            "messages": self.mensagens
        }
        
        print("🔄 Consultando Qwen...")
        
        resposta = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=dados
        )
        
        if resposta.status_code != 200:
            print(f"❌ Erro na API: {resposta.status_code}")
            print(resposta.text)
            return None
        
        resultado = resposta.json()
        mensagem = resultado["choices"][0]["message"]
        uso = resultado.get("usage", {})
        
        tokens_input = uso.get("prompt_tokens", 0)
        tokens_output = uso.get("completion_tokens", 0)
        tokens_chamada = tokens_input + tokens_output
        self.total_tokens += tokens_chamada
        
        print(f" Tokens: {tokens_chamada} | Total: {self.total_tokens}")
        
        percentual = self.total_tokens / LIMITE_CONTEXTO
        print(f"⚠️ Uso do contexto: {percentual*100:.1f}%\n")
        
        self.mensagens.append(mensagem)
        self.historico_completo.append({"papel": "agente", "texto": mensagem["content"]})
        
        if percentual >= THRESHOLD_ALERTA:
            print("🚨 ATENÇÃO: Limite de contexto se aproximando!")
            print("🔄 Gerando prompt de continuação automaticamente...\n")
            self.gerar_e_salvar_continuidade()
        
        return mensagem["content"]
    
    def gerar_e_salvar_continuidade(self):
        prompt_resumo = """
        Resuma esta conversa de forma estruturada para continuação futura.
        Inclua:
        1. OBJETIVO: Qual o propósito da conversa?
        2. CONTEXTO: Informações importantes estabelecidas
        3. PROGRESSO: O que já foi feito/concluído
        4. PENDÊNCIAS: O que falta fazer
        5. DECISÕES: Escolhas importantes tomadas
        
        Formato: texto corrido em português, seja conciso.
        """
        
        self.mensagens.append({"role": "user", "content": prompt_resumo})
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        }
        
        resposta = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={"model": MODELO, "messages": self.mensagens}
        )
        
        if resposta.status_code == 200:
            resumo = resposta.json()["choices"][0]["message"]["content"]
            
            dados_continuidade = {
                "data_geracao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tokens_usados": self.total_tokens,
                "percentual_contexto": f"{(self.total_tokens/LIMITE_CONTEXTO)*100:.1f}%",
                "modelo_usado": MODELO,
                "resumo_estruturado": resumo,
                "historico_mensagens": self.historico_completo,
                "instrucoes_proxima_conversa": "Para continuar: carregue este arquivo no início da nova conversa."
            }
            
            with open(ARQUIVO_CONTINUIDADE, "w", encoding="utf-8") as f:
                json.dump(dados_continuidade, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Continuidade salva em: {ARQUIVO_CONTINUIDADE}")
            print(f"📄 Resumo gerado:\n{resumo}\n")


if __name__ == "__main__":
    print(" AGENTE COM CONTINUIDADE INICIADO")
    print("=" * 60)
    
    agente = AgenteContinuidade()
    agente.carregar_continuidade()
    
    print("Digite suas mensagens (ou 'sair' para encerrar)\n")
    
    while True:
        try:
            pergunta = input("👤 Você: ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit']:
                print("\n💾 Salvando estado atual antes de sair...")
                agente.gerar_e_salvar_continuidade()
                print("👋 Até a próxima!")
                break
            
            if not pergunta:
                continue
            
            resposta = agente.enviar_para_llm(pergunta)
            
            if resposta:
                print(f"\n🤖 Agente: {resposta}\n")
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupção detectada. Salvando...")
            agente.gerar_e_salvar_continuidade()
            break
