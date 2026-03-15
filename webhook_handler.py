#!/usr/bin/env python3
import os
import subprocess
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

APP_DIR = "/home/ilya/catty-app"
REPO_URL = "https://github.com/ilyanikoniko/catty-reminders-app.git"

def deploy():
    """Обновление кода и перезапуск приложения"""
    print("🚀 Начат процесс развёртывания")

    # 1. Обновление кода
    if not os.path.exists(APP_DIR):
        subprocess.run(["git", "clone", REPO_URL, APP_DIR], check=True)
        print("✅ Репозиторий склонирован")
    else:
        subprocess.run(["git", "-C", APP_DIR, "pull"], check=True)
        print("✅ Код обновлён")

    # 2. Запуск тестов (test.sh)
    test_script = os.path.join(APP_DIR, "test.sh")
    if os.path.exists(test_script) and os.access(test_script, os.X_OK):
        try:
            subprocess.run([test_script], cwd=APP_DIR, check=True)
            print("✅ Тесты пройдены")
        except subprocess.CalledProcessError:
            print("❌ Тесты не пройдены")
            return
    else:
        print("ℹ️ Тесты не настроены, продолжаем без тестов")

    # 3. Установка зависимостей
    req_file = os.path.join(APP_DIR, "requirements.txt")
    if os.path.exists(req_file):
        subprocess.run(["pip3", "install", "-r", req_file], check=True)
        print("✅ Зависимости установлены")

    # 4. Перезапуск сервиса
    subprocess.run(["sudo", "systemctl", "restart", "catty"], check=True)
    print("✅ Сервис catty перезапущен")
    print("🎉 Развёртывание завершено успешно")

@app.route('/', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    if event != 'push':
        return jsonify({'msg': 'ignored'}), 200

    print("📩 Получен webhook, запускаем deploy в фоне")
    subprocess.Popen([sys.executable, os.path.abspath(__file__), 'deploy'])
    return jsonify({'status': 'accepted'}), 202

@app.route('/health', methods=['GET'])
def health():
    return "ok"

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'deploy':
        deploy()
    else:
        app.run(host='0.0.0.0', port=8080)
