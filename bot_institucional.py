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

# =====================================================================
# CONFIGURATION: Conexión nativa con OpenAI y Telegram
# =====================================================================
TELEGRAM_TOKEN = "8588011211:AAF8PokOcIiPQhcz-d4yvkM7k-jCwpYgjMk"
CHAT_ID = "7682778658"
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

BOT_ACTIVO = True
ALERTAS_PROCESADAS = set()

# =====================================================================
# TELEGRAM BOT CONTROLS
# =====================================================================
@bot.message_handler(commands=['on'])
def encender_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = True
    bot.reply_to(message, "🟢 Sistema Activado. Monitoreando Forex Factory e IA de OpenAI (GPT-4o-mini) de forma ultra-compacta...")

@bot.message_handler(commands=['off'])
def apagar_bot(message):
    global BOT_ACTIVO
    BOT_ACTIVO = False
    bot.reply_to(message, "🔴 Sistema Pausado. IA desconectada.")

# =====================================================================
# MOTOR COGNITIVO INTERMERCADO (OpenAI - Con Límite Estricto de Texto)
# =====================================================================
def consultar_openai(prompt):
    if not OPENAI_API_KEY:
        return "⚠️ Error: Falta la variable OPENAI_API_KEY en Render."
        
    url = "https://openai.com"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system", 
                "content": "Eres un bot de trading institucional. Responde de forma ultra-corta, directa y resumida. Usa únicamente viñetas directas. Prohibido saludar, prohibido agregar preámbulos, conclusiones o párrafos explicativos. Sé breve."
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 300  # LIMITACIÓN FÍSICA: Corta el mensaje si la IA intenta escribir de más
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            return response.json()['choices']['message']['content']
        else:
            return f"⚠️ Error de OpenAI: {response.status_code}\nDetalles: {response.text}"
    except Exception as e:
        return f"⚠️ Error de red con OpenAI: {e}"

def procesar_escenarios_10min(evento, divisa, previo, pronostico):
    if not BOT_ACTIVO: return
    prompt = f"Noticia: {evento} ({divisa}). Previo: {previo}, Pronóstico: {pronostico}. Genera Escenario A (Si el dato sale Mayor al pronóstico) y Escenario B (Si sale Menor). Indica la dirección neta (Sube/Baja/Sin Impacto) para: ORO, BITCOIN, USD, EUR. Usa solo viñetas simples, sin asteriscos ni negritas."
    
    analisis = consultar_openai(prompt)
    bot.send_message(CHAT_ID, f"⏳ NOTICIA EN 10 MINUTOS:\n\n{analisis}")

def procesar_dato_publicado(evento, divisa, pronostico, dato_real):
    if not BOT_ACTIVO: return
    prompt = f"Publicado: {evento} ({divisa}). Real: {dato_real} frente a Pronóstico: {pronostico}. Determina el impacto inmediato (Sube/Baja/Sin Impacto) para: ORO, BITCOIN, USD, EUR. Usa solo viñetas simples, sin asteriscos ni negritas."
    
    analisis = consultar_openai(prompt)
    bot.send_message(CHAT_ID, f"📢 DATO PUBLICADO EN VIVO:\n\n{analisis}")

# =====================================================================
# TUBERÍA DE DATOS CON INTERNET ABIERTO (Forex Factory)
# =====================================================================
def bucle_calendario_infinito():
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
                
                # 2. Veredicto con el Dato Real Publicado
                if ahora_cr >= fecha_evento:
                    dato_real = noticia.get("actual")
                    if dato_real and (id_noticia + "_real") not in ALERTAS_PROCESADAS:
                        procesar_dato_publicado(noticia.get("event"), noticia.get("currency"), noticia.get("estimate", "N/A"), dato_real)
                        ALERTAS_PROCESADAS.add(id_noticia + "_real")
        except:
            pass
        time.sleep(30)

# =====================================================================
# COMANDO DE SIMULACIÓN (/test)
# =====================================================================
@bot.message_handler(commands=['test'])
def comando_testeo(message):
    bot.reply_to(message, "⏳ Procesando matrices analíticas compactas con OpenAI...")
    procesar_escenarios_10min("Nóminas No Agrícolas (NFP)", "USD", "150K", "180K")
    time.sleep(2)
    procesar_dato_publicado("Nóminas No Agrícolas (NFP)", "USD", "180K", "220K")

# =====================================================================
# SISTEMA DE COMPATIBILIDAD DE PUERTOS WEB PARA RENDER FREE
# =====================================================================
def abrir_puerto_falso_render():
    from http.server import BaseHTTPRequestHandler, HTTPServer
    class ServidorFalso(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot Financiero con OpenAI Activo")
        def log_message(self, format, *args):
            return
            
    puerto = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', puerto), ServidorFalso)
    server.serve_forever()

if __name__ == "__main__":
    hilo_noticias = threading.Thread(target=bucle_calendario_infinito)
    hilo_noticias.daemon = True
    hilo_noticias.start()
    
    hilo_puerto = threading.Thread(target=abrir_puerto_falso_render)
    hilo_puerto.daemon = True
    hilo_puerto.start()
    
    bot.infinity_polling()
