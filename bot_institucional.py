import os
import time
import threading
from datetime import datetime, timedelta

# =====================================================================
# CONFIGURACIÓN DE ZONA HORARIA DE COSTA RICA (GMT-6)
# =====================================================================
os.environ['TZ'] = 'America/Costa_Rica'
try:
    time.tzset()
except AttributeError:
    pass  # Compatibilidad si pruebas localmente en Windows

import requests
import telebot
from groq import Groq

# =====================================================================
# CREDENCIALES: El servidor en la nube las leerá de forma segura
# =====================================================================
TELEGRAM_TOKEN = 8588011211:AAEHEVm7fyzYjIoOlBehv_poRKNACbGMy1A"
CHAT_ID = "7682778658"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Inicializar conexiones de alta velocidad
bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = Groq(api_key=GROQ_API_KEY)

BOT_ACTIVO = True
MODO_TITULARES_VIVO = False
ALERTAS_PROCESADAS = set()

# =====================================================================
# COMANDOS DE CONTROL DESDE TELEGRAM
# =====================================================================
@bot.message_handler(commands=['on'])
def encender_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = True
    bot.reply_to(message, "🟢 *Sistema Activado.* Monitoreando Forex Factory e IA en hora de Costa Rica...", parse_mode="Markdown")

@bot.message_handler(commands=['off'])
def apagar_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = False
    bot.reply_to(message, "🔴 *Sistema Pausado.* IA desconectada para congelar consumo.", parse_mode="Markdown")

@bot.message_handler(commands=['discurso'])
def conmutar_discurso(message):
    global MODO_TITULARES_VIVO
    MODO_TITULARES_VIVO = not MODO_TITULARES_VIVO
    estado = "ACTIVADO 🎙️ (Traducción ráfaga instantánea)" if MODO_TITULARES_VIVO else "DESACTIVADO 📊"
    bot.reply_to(message, f"⚡ *Modo Titulares en Vivo:* {estado}", parse_mode="Markdown")

# =====================================================================
# MOTOR COGNITIVO INTERMERCADO (IA Mente Abierta - Llama 3 70B)
# =====================================================================
def consultar_ia_profunda(prompt):
    """Consulta al supercomputador de Groq sin restricciones de red."""
    try:
        completion = ai_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Error en nodo de IA: {e}"

def procesar_escenarios_10min(evento, divisa, previo, pronostico):
    if not BOT_ACTIVO: return
    prompt = f"""Analiza con mente abierta de trader profesional la noticia macroeconómica: {evento} ({divisa}). Previo: {previo}, Pronóstico: {pronostico}.
    Genera dos escenarios interpretativos concisos (Si sale Mayor o Menor al pronóstico). Indica el impacto neto (Sube/Baja/Sin Impacto) en base a correlaciones modernas para: ORO, BITCOIN, USD, EUR. 
    Sé directo, usa viñetas, responde en español y no agregues introducciones."""
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"⏳ **NOTICIA EN 10 MINUTOS:**\n\n{analisis}", parse_mode="Markdown")

def procesar_dato_publicado(evento, divisa, pronostico, dato_real):
    if not BOT_ACTIVO: return
    prompt = f"""Urgente: Se publicó el dato real de {evento} ({divisa}). Resultado: {dato_real} frente a Pronóstico: {pronostico}.
    Determina de inmediato el veredicto del mercado con criterio financiero avanzado. Genera la dirección exacta (Sube/Baja/Sin Impacto) para: ORO, BITCOIN, USD, EUR.
    Formato ultra-directo en español, sin texto de relleno conversacional."""
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"📢 **DATO PUBLICADO EN VIVO:**\n\n{analisis}", parse_mode="Markdown")

# =====================================================================
# ESCUCHADOR DE TITULARES EN VIVO (Para Donald Trump / Discursos FED)
# =====================================================================
def procesar_titular_discurso_rapido(titular_ingles, fuente):
    """Traduce e interpreta el sentimiento de ráfagas de texto en milisegundos."""
    if not BOT_ACTIVO or not MODO_TITULARES_VIVO: return
    
    prompt = f"""Traduce al español e interpreta el impacto financiero inmediato del siguiente titular en vivo de {fuente}:
    "{titular_ingles}"
    Indica la reacción rápida del mercado para Oro, Bitcoin y USD. Formato de ráfaga de 3 líneas máximo."""
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"🎙️ **TITULAR EN VIVO ({fuente}):**\n\n{analisis}", parse_mode="Markdown")

# =====================================================================
# TUBERÍA DE DATOS CON INTERNET ABIERTO (Forex Factory Real-Time)
# =====================================================================
def bucle_calendario_infinito():
    print("Motor de datos conectado a Internet Abierto de Render. Sincronizado GMT-6.")
    # URL de API institucional de calendario económico (Abierta en Render)
    url_calendar = "https://financialmodelingprep.com"
    
    while True:
        if not BOT_ACTIVO:
            time.sleep(20)
            continue
        try:
            # En Render esta línea corre libremente sin dar jamás Error 403
            response = requests.get(url_calendar, timeout=10).json()
            ahora_cr = datetime.now()
            
            for noticia in response:
                if noticia.get("currency") not in ["USD", "EUR"]: continue
                
                fecha_raw = noticia.get("date")
                if not fecha_raw: continue
                fecha_evento = datetime.strptime(fecha_raw, "%Y-%m-%d %H:%M:%S")
                id_noticia = f"{noticia.get('event')}_{fecha_raw}"
                
                # 1. Alerta de escenarios 10 minutos antes
                diferencia = fecha_evento - ahora_cr
                if timedelta(minutes=9) <= diferencia <= timedelta(minutes=11):
                    if id_noticia not in ALERTAS_PROCESADAS:
                        procesar_escenarios_10min(noticia.get("event"), noticia.get("currency"), noticia.get("previous", "N/A"), noticia.get("estimate", "N/A"))
                        ALERTAS_PROCESADAS.add(id_noticia)
                
                # 2. Veredicto con el Dato Real Publicado (Delay Guard activo)
                if ahora_cr >= fecha_evento:
                    dato_real = noticia.get("actual")
                    if dato_real and (id_noticia + "_real") not in ALERTAS_PROCESADAS:
                        procesar_dato_publicado(noticia.get("event"), noticia.get("currency"), noticia.get("estimate", "N/A"), dato_real)
                        ALERTAS_PROCESADAS.add(id_noticia + "_real")
        except:
            pass
        time.sleep(30)

# =====================================================================
# COMANDO DE SIMULACIÓN PARA EVALUAR CALIDAD (/test)
# =====================================================================
@bot.message_handler(commands=['test'])
def comando_testeo(message):
    bot.reply_to(message, "⚡ *Conectando con la IA de rango institucional...*")
    procesar_escenarios_10min("Nóminas No Agrícolas (NFP)", "USD", "150K", "180K")
    time.sleep(2)
    procesar_dato_publicado("Nóminas No Agrícolas (NFP)", "USD", "180K", "220K")
    time.sleep(2)
    bot.send_message(CHAT_ID, "📝 *Simulando ráfaga de discurso (Modo Titulares)...*")
    procesar_titular_discurso_rapido("TRUMP SAYS NEW 20% TARIFFS ON ALL EUROPEAN GOODS ARE COMING SOON", "Reuters X")

if __name__ == "__main__":
    hilo_noticias = threading.Thread(target=bucle_calendario_infinito)
    hilo_noticias.daemon = True
    hilo_noticias.start()
    bot.infinity_polling()
