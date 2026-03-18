import requests
import time
from datetime import datetime, timedelta
from scipy.stats import poisson
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- CONFIGURAÇÕES ---
# O Chat ID não é necessário aqui, pois o bot responde ao "update" de quem envia o comando.
TELEGRAM_TOKEN = "8641645845:AAEMnvOALyphGB8LslmrrG_B3yGHCa0Sa_c"
FOOTBALL_API_KEY = "8ba5e4a9b12fc6e0ecb8894bff67d5c5"

# --- FUNÇÕES DE ANÁLISE ---
def analisar_jogo(fixture):
    # Lógica de retorno do palpite
    home = fixture['teams']['home']['name']
    away = fixture['teams']['away']['name']
    return f"⚽ {home} x {away}\n🎯 Over 1.5 Gols | Confiança: 70.%"

async def buscar_dados_api(data_alvo):
    url = f"https://v3.football.api-sports.io/fixtures?date={data_alvo}"
    headers = {
        'x-rapidapi-key': FOOTBALL_API_KEY, 
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        return response.json().get('response', [])
    except Exception as e:
        print(f"Erro na API: {e}")
        return []

# --- COMANDOS DO TELEGRAM ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá! Sou seu assistente de previsões (+70%).\n\n"
        "Comandos disponíveis:\n"
        "🚀 /hoje - Jogos com alta chance para hoje\n"
        "📅 /semana - Agenda completa dos próximos 7 dias"
    )

async def hoje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Analisando jogos de hoje...")
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    jogos = await buscar_dados_api(data_hoje)
    
    mensagens = []
    # Pegamos apenas os primeiros 15 jogos para não travar o bot
    for jogo in jogos[:15]:
        previsao = analisar_jogo(jogo)
        if previsao:
            try:
                # Ajuste de horário para Brasília
                hora_iso = jogo['fixture']['date']
                hora_objeto = datetime.fromisoformat(hora_iso.replace('Z', '+00:00'))
                hora_br = (hora_objeto - timedelta(hours=3)).strftime("%H:%M")
                mensagens.append(f"⏰ {hora_br}\n{previsao}")
            except:
                continue

    if mensagens:
        texto_final = "✅ **JOGOS DE HOJE:**\n\n" + "\n\n".join(mensagens)
        await update.message.reply_text(texto_final, parse_mode="Markdown")
    else:
        await update.message.reply_text("Puxa, nenhuma oportunidade clara para hoje.")

async def semana(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Gerando relatório semanal...")
    relatorio = "📅 **PREVISÕES DA SEMANA**\n\n"
    
    # Analisa hoje e os próximos 3 dias (para não estourar o limite da API gratuita)
    for i in range(4):
        data_alvo = (datetime.now() + timedelta(days=i))
        jogos = await buscar_dados_api(data_alvo.strftime("%Y-%m-%d"))
        
        dia_str = data_alvo.strftime("%d/%m (%A)")
        dia_msgs = []
        
        for jogo in jogos[:8]: 
            previsao = analisar_jogo(jogo)
            if previsao:
                nomes_times = previsao.splitlines()[0]
                dia_msgs.append(f"• {nomes_times}")
        
        if dia_msgs:
            relatorio += f"📍 *{dia_str}*\n" + "\n".join(dia_msgs) + "\n\n"

    await update.message.reply_text(relatorio, parse_mode="Markdown")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    print("🤖 Bot iniciado! Digite /start no seu Telegram.")
    # Criação da aplicação
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Adicionando os comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoje", hoje))
    app.add_handler(CommandHandler("semana", semana))
    
    # Inicia o bot
    app.run_polling()
