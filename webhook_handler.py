#!/usr/bin/env python3
import os
import subprocess
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

APP_DIR = "/home/ilya/catty-app"                    # путь до приложения
REPO_URL = "https://github.com/ilyanikoniko/catty-reminders-app.git" 

def deploy():
    """Обновление кода и перезапуск приложения"""
    if not os.path.exists(APP_DIR):
        subprocess.run(["git", "clone", REPO_URL, APP_DIR], check=True)
    else:
        subprocess.run(["git", "-C", APP_DIR, "pull"], check=True)

    req_file = os.path.join(APP_DIR, "requirements.txt")
    if os.path.exists(req_file):
        subprocess.run(["pip3", "install", "-r", req_file], check=True)

    subprocess.run(["sudo", "systemctl", "restart", "catty"], check=True)

@app.route('/', methods=['POST'])
def webhook():
    event = request.headers.get('X-GitHub-Event')
    if event != 'push':
        return jsonify({'msg': 'ignored'}), 200

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

