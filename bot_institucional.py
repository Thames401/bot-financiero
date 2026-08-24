import os
import time
import threading
from datetime import datetime, timedelta

# =====================================================================
# FORCE COSTA RICA TIME ZONE (GMT-6)
# =====================================================================
os.environ['TZ'] = 'America/Costa_Rica'
try:
    time.tzset()
except AttributeError:
    pass

import requests
import telebot
from groq import Groq

# =====================================================================
# CONFIGURATION
# =====================================================================
TELEGRAM_TOKEN = "8588011211:AAF8PokOcIiPQhcz-d4yvkM7k-jCwpYgjMk"
CHAT_ID = "7682778658"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
ai_client = Groq(api_key=GROQ_API_KEY)

BOT_ACTIVO = True
MODO_TITULARES_VIVO = False
ALERTAS_PROCESADAS = set()

# =====================================================================
# TELEGRAM BOT CONTROLS
# =====================================================================
@bot.message_handler(commands=['on'])
def encender_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = True
    bot.reply_to(message, "🟢 Sistema Activado. Monitoreando Forex Factory de forma segura en hora de Costa Rica...")

@bot.message_handler(commands=['off'])
def apagar_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = False
    bot.reply_to(message, "🔴 Sistema Pausado. IA desconectada de forma correcta.")

@bot.message_handler(commands=['discurso'])
def conmutar_discurso(message):
    global MODO_TITULARES_VIVO
    MODO_TITULARES_VIVO = not MODO_TITULARES_VIVO
    estado = "ACTIVADO (Traducción ráfaga instantánea)" if MODO_TITULARES_VIVO else "DESACTIVADO"
    bot.reply_to(message, f"⚡ Modo Titulares en Vivo: {estado}")

# =====================================================================
# MOTOR COGNITIVO INTERMERCADO (Llama 3 70B - Blindado sin Markdown)
# =====================================================================
def consultar_ia_profunda(prompt):
    try:
        completion = ai_client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return completion.choices.message.content
    except Exception as e:
        return f"⚠️ Error en nodo de IA: {e}"

def procesar_escenarios_10min(evento, divisa, previo, pronostico):
    if not BOT_ACTIVO: return
    prompt = f"Analiza la noticia macroeconómica: {evento} ({divisa}). Previo: {previo}, Pronóstico: {pronostico}. Genera dos escenarios interpretativos muy breves (Si sale Mayor o Menor al pronóstico). Indica el impacto neto (Sube/Baja/Sin Impacto) para: ORO, BITCOIN, USD, EUR. Sé muy directo, usa viñetas simples en español y no uses asteriscos ni formatos especiales de texto."
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"⏳ NOTICIA EN 10 MINUTOS:\n\n{analisis}")

def procesar_dato_publicado(evento, divisa, pronostico, dato_real):
    if not BOT_ACTIVO: return
    prompt = f"Se publicó el dato real de {evento} ({divisa}). Resultado: {dato_real} frente a Pronóstico: {pronostico}. Determina la dirección exacta de impacto (Sube/Baja/Sin Impacto) para: ORO, BITCOIN, USD, EUR. Formato ultra-directo en español, usa viñetas simples y no uses asteriscos ni formatos especiales de texto."
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"📢 DATO PUBLICADO EN VIVO:\n\n{analisis}")

def procesar_titular_discurso_rapido(titular_ingles, fuente):
    if not BOT_ACTIVO or not MODO_TITULARES_VIVO: return
    prompt = f"Traduce al español e interpreta el impacto financiero rápido para Oro, Bitcoin y USD del siguiente titular de {fuente}: '{titular_ingles}'. Máximo 3 líneas directas, sin usar asteriscos ni formatos especiales de texto."
    
    analisis = consultar_ia_profunda(prompt)
    bot.send_message(CHAT_ID, f"🎙️ TITULAR EN VIVO ({fuente}):\n\n{analisis}")

# =====================================================================
# TUBERÍA DE DATOS CON INTERNET ABIERTO (Forex Factory)
# =====================================================================
def bucle_calendario_infinito():
    print("Motor de datos conectado a Internet Abierto de Render. Sincronizado GMT-6.")
    url_calendar = "https://financialmodelingprep.com"
    
    while True:
        if not BOT_ACTIVO:
            time.sleep(20)
            continue
        try:
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
    bot.reply_to(message, "⏳ Procesando matrices analíticas de la IA...")
    procesar_escenarios_10min("Nóminas No Agrícolas (NFP)", "USD", "150K", "180K")
    time.sleep(2)
    procesar_dato_publicado("Nóminas No Agrícolas (NFP)", "USD", "180K", "220K")

# =====================================================================
# SISTEMA DE COMPATIBILIDAD DE PUERTOS WEB PARA RENDER FREE
# =====================================================================
def abrir_puerto_falso_render():
    """Abre un puerto HTTP básico en el hilo principal para obligar a Render a dar luz verde."""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class ServidorFalso(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Financiero Activo de Forma Correcta")
        def log_message(self, format, *args):
            return  # Silenciar registros de red innecesarios
            
    puerto = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', puerto), ServidorFalso)
    server.serve_forever()

if __name__ == "__main__":
    # Arrancar la tubería macroeconómica en segundo plano
    hilo_noticias = threading.Thread(target=bucle_calendario_infinito)
    hilo_noticias.daemon = True
    hilo_noticias.start()
    
    # Arrancar el servidor HTTP falso en un hilo paralelo para calmar a Render
    hilo_puerto = threading.Thread(target=abrir_puerto_falso_render)
    hilo_puerto.daemon = True
    hilo_puerto.start()
    
    # Iniciar la escucha permanente de comandos de Telegram
    bot.infinity_polling()
