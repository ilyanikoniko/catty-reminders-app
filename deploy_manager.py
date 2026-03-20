import os
import subprocess
import threading
import logging
from flask import Flask, request, jsonify

# Параметры путей
PROJECT_DIR = "/home/ilya/catty-app"
CONF_FILE = "/etc/catty-app-env"
SERVICE_NAME = "catty"

app = Flask(__name__)

# Настройка логирования в файл пользователя (чтобы не было проблем с правами)
logging.basicConfig(
    filename="/home/ilya/deploy.log",
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

def run_deploy(sha):
    logging.info(f"--- Начинаем процедуру деплоя для SHA: {sha} ---")
    try:
        # Обновление репозитория
        subprocess.run(["git", "-C", PROJECT_DIR, "fetch", "--all"], check=True)
        subprocess.run(["git", "-C", PROJECT_DIR, "reset", "--hard", sha], check=True)
        # Обновление окружения для прохождения проверок GitHub Actions
        with open(CONF_FILE, "w") as f:
            f.write(f"DEPLOY_REF={sha}\n")
        # Перезапуск приложения
        subprocess.run(["sudo", "systemctl", "restart", SERVICE_NAME], check=True)
        logging.info("Деплой успешно завершен.")
    except Exception as e:
        logging.error(f"Ошибка деплоя: {e}")

@app.route('/', methods=['POST'])
def process_webhook():
    event_type = request.headers.get('X-GitHub-Event')
    if event_type == 'ping':
        return jsonify({"message": "pong"}), 200
    if event_type == 'push':
        payload = request.json
        ref_sha = payload.get('after')
        if ref_sha and ref_sha != "0000000000000000000000000000000000000000":
            logging.info(f"Получен пуш. Запускаем обновление до {ref_sha}")
            # Запуск в отдельном потоке, чтобы сразу вернуть ответ GitHub
            task = threading.Thread(target=run_deploy, args=(ref_sha,))
            task.start()
            return jsonify({"status": "triggered", "sha": ref_sha}), 202
    return jsonify({"status": "ignored"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
