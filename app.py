import requests, os, psutil, sys, jwt, pickle, json, binascii, time, urllib3, xKEys, base64, datetime, re, socket, threading
import asyncio
from protobuf_decoder.protobuf_decoder import Parser
from byte import *
from byte import xSEndMsg
from byte import Auth_Chat
from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from flask import Flask, request, jsonify, render_template_string
from black9 import openroom, spmroom

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

# ==================== গ্লোবাল ভেরিয়েবল ====================
connected_clients = {}
connected_clients_lock = threading.Lock()
active_spam_targets = {}
active_spam_lock = threading.Lock()

# গিটহাব কনফিগ
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')
GITHUB_FILE = 'unlimited_targets.txt'
GITHUB_API_URL = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}'

app = Flask(__name__)

# ==================== গিটহাব ফাংশন ====================
def get_github_content():
    if not GITHUB_TOKEN or not GITHUB_REPO:
        return [], None
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(GITHUB_API_URL, headers=headers)
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            targets = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            return targets, data['sha']
        return [], None
    except Exception as e:
        print(f"GitHub read error: {e}")
        return [], None

def update_github_content(content, sha):
    if not GITHUB_TOKEN:
        return False
    try:
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        data = {
            'message': 'Update unlimited targets from web panel',
            'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            'sha': sha
        }
        response = requests.put(GITHUB_API_URL, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"GitHub update error: {e}")
        return False

def add_unlimited_target(target_id):
    targets, sha = get_github_content()
    if not sha:
        return False, "GitHub file not found! Create unlimited_targets.txt first"
    if target_id in targets:
        return False, "UID already exists!"
    targets.append(target_id)
    if update_github_content('\n'.join(targets), sha):
        return True, "✅ UID added successfully!"
    return False, "Failed to update GitHub!"

def remove_unlimited_target(target_id):
    targets, sha = get_github_content()
    if not sha:
        return False, "GitHub file not found!"
    if target_id not in targets:
        return False, "UID not found!"
    targets.remove(target_id)
    if update_github_content('\n'.join(targets), sha):
        return True, "✅ UID removed successfully!"
    return False, "Failed to update GitHub!"

def load_and_start_unlimited_targets():
    targets, _ = get_github_content()
    for target in targets:
        if target not in active_spam_targets:
            with active_spam_lock:
                active_spam_targets[target] = {'active': True, 'start_time': datetime.now()}
                threading.Thread(target=spam_worker, args=(target, None), daemon=True).start()
    print(f"🔄 Loaded {len(targets)} unlimited targets from GitHub")

# ==================== স্প্যাম ফাংশন ====================
def send_spam_from_all_accounts(target_id):
    with connected_clients_lock:
        for account_id, client in connected_clients.items():
            try:
                if (hasattr(client, 'CliEnts2') and client.CliEnts2 and 
                    hasattr(client, 'key') and client.key and 
                    hasattr(client, 'iv') and client.iv):
                    
                    try:
                        client.CliEnts2.send(openroom(client.key, client.iv))
                    except Exception:
                        pass
                    
                    for i in range(10):
                        try:
                            client.CliEnts2.send(spmroom(client.key, client.iv, target_id))
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            break
                        except Exception:
                            break
            except Exception:
                pass

def spam_worker(target_id, duration_minutes=None):
    print(f"🎯 SPAM STARTED: {target_id}")
    start_time = datetime.now()
    
    while True:
        with active_spam_lock:
            if target_id not in active_spam_targets:
                print(f"🛑 SPAM STOPPED: {target_id}")
                break
            
            if duration_minutes:
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() >= duration_minutes * 60:
                    print(f"⏰ SPAM TIME FINISHED: {target_id}")
                    del active_spam_targets[target_id]
                    break
        
        try:
            send_spam_from_all_accounts(target_id)
            time.sleep(0.1)
        except Exception as e:
            print(f"⚠️ SPAM ERROR {target_id}: {e}")
            time.sleep(1)

# ==================== API ক্লাস ====================
class SimpleAPI:
    def process_spam_command(self, target_id, duration_minutes=None):
        try:
            if not ChEck_Commande(target_id):
                return {"status": "error", "message": "Invalid User ID"}
            with active_spam_lock:
                if target_id not in active_spam_targets:
                    active_spam_targets[target_id] = {'active': True, 'start_time': datetime.now(), 'duration': duration_minutes}
                    threading.Thread(target=spam_worker, args=(target_id, duration_minutes), daemon=True).start()
                    return {"status": "success", "message": f"✅ SPAM STARTED ON: {target_id}"}
                else:
                    return {"status": "error", "message": f"⚠️ SPAM ALREADY RUNNING ON: {target_id}"}
        except Exception as e:
            return {"status": "error", "message": f"❌ ERROR: {str(e)}"}
            
    def process_stop_command(self, target_id):
        try:
            with active_spam_lock:
                if target_id in active_spam_targets:
                    del active_spam_targets[target_id]
                    return {"status": "success", "message": f"🛑 SPAM STOPPED ON: {target_id}"}
                else:
                    return {"status": "error", "message": f"⚠️ NO ACTIVE SPAM ON: {target_id}"}
        except Exception as e:
            return {"status": "error", "message": f"❌ ERROR: {str(e)}"}
    
    def get_status(self):
        try:
            with active_spam_lock:
                active_targets = list(active_spam_targets.keys())
            with connected_clients_lock:
                accounts_count = len(connected_clients)
                accounts_list = list(connected_clients.keys())
            unlimited_targets, _ = get_github_content()
            return {"status": "success", "data": {
                "active_targets": active_targets,
                "active_targets_count": len(active_targets),
                "connected_accounts_count": accounts_count,
                "connected_accounts": accounts_list,
                "unlimited_targets": unlimited_targets,
                "unlimited_targets_count": len(unlimited_targets)
            }}
        except Exception as e:
            return {"status": "error", "message": f"STATUS ERROR: {str(e)}"}

api = SimpleAPI()

# ==================== ওয়েব এপি রাউট ====================
@app.route('/spam', methods=['GET'])
def start_spam():
    target_id = request.args.get('user_id')
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    result = api.process_spam_command(target_id)
    return jsonify(result)

@app.route('/stop', methods=['GET'])
def stop_spam():
    target_id = request.args.get('user_id')
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    result = api.process_stop_command(target_id)
    return jsonify(result)

@app.route('/add_unlimited', methods=['GET'])
def add_unlimited():
    target_id = request.args.get('user_id')
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    success, message = add_unlimited_target(target_id)
    if success:
        api.process_spam_command(target_id)
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/remove_unlimited', methods=['GET'])
def remove_unlimited():
    target_id = request.args.get('user_id')
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    success, message = remove_unlimited_target(target_id)
    if success:
        api.process_stop_command(target_id)
    return jsonify({"status": "success" if success else "error", "message": message})

@app.route('/status', methods=['GET'])
def get_status():
    result = api.get_status()
    return jsonify(result)

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# ==================== প্রিমিয়াম HTML টেমপ্লেট (লাইটিং + অ্যানিমেশন সহ) ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>✨ SHAFIQ SPAM PRO | PREMIUM LIGHTING ✨</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: radial-gradient(circle at 20% 30%, #0a0a0a, #050510);
            min-height: 100vh;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }

        /* ========== লাইটিং ইফেক্ট ========== */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 50% 50%, rgba(255,107,107,0.08), transparent 70%);
            pointer-events: none;
            z-index: 0;
            animation: lightingPulse 4s infinite alternate;
        }

        @keyframes lightingPulse {
            0% { opacity: 0.3; background: radial-gradient(circle at 30% 40%, rgba(255,107,107,0.05), transparent 70%); }
            100% { opacity: 0.8; background: radial-gradient(circle at 70% 60%, rgba(255,217,61,0.1), transparent 70%); }
        }

        /* ========== গ্লাসমর্ফিজম ব্লক ব্যাকগ্রাউন্ড ========== */
        .block-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 0;
            overflow: hidden;
            pointer-events: none;
        }

        .block {
            position: absolute;
            background: rgba(255,107,107,0.08);
            backdrop-filter: blur(3px);
            border: 1px solid rgba(255,107,107,0.2);
            animation: floatBlock 18s infinite linear;
            border-radius: 12px;
            box-shadow: 0 0 20px rgba(255,107,107,0.1);
        }

        @keyframes floatBlock {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 0.5; }
            90% { opacity: 0.5; }
            100% { transform: translateY(-100vh) rotate(360deg); opacity: 0; }
        }

        .block:nth-child(1) { width: 70px; height: 70px; left: 5%; animation-duration: 15s; background: rgba(255,107,107,0.12); }
        .block:nth-child(2) { width: 100px; height: 100px; left: 15%; animation-duration: 20s; animation-delay: 2s; background: rgba(56,239,125,0.08); border-color: rgba(56,239,125,0.2); }
        .block:nth-child(3) { width: 50px; height: 50px; left: 28%; animation-duration: 13s; animation-delay: 1s; background: rgba(255,217,61,0.1); }
        .block:nth-child(4) { width: 130px; height: 130px; left: 45%; animation-duration: 22s; animation-delay: 4s; background: rgba(255,107,107,0.06); }
        .block:nth-child(5) { width: 80px; height: 80px; left: 65%; animation-duration: 17s; animation-delay: 0.5s; background: rgba(56,239,125,0.1); }
        .block:nth-child(6) { width: 55px; height: 55px; left: 82%; animation-duration: 12s; animation-delay: 3s; background: rgba(255,107,107,0.15); }
        .block:nth-child(7) { width: 110px; height: 110px; left: 92%; animation-duration: 24s; animation-delay: 1.5s; background: rgba(255,217,61,0.08); }
        .block:nth-child(8) { width: 40px; height: 40px; left: 38%; animation-duration: 10s; animation-delay: 2.5s; background: rgba(56,239,125,0.12); }

        .container {
            max-width: 620px;
            margin: 0 auto;
            position: relative;
            z-index: 2;
        }

        /* ========== প্রিমিয়াম হেডার ========== */
        .header {
            text-align: center;
            margin-bottom: 30px;
            animation: premiumGlow 0.8s ease-out;
        }

        @keyframes premiumGlow {
            0% { opacity: 0; transform: scale(0.9); filter: blur(10px); }
            100% { opacity: 1; transform: scale(1); filter: blur(0); }
        }

        .logo {
            font-size: 70px;
            margin-bottom: 10px;
            display: inline-block;
            animation: logoPulse 2s infinite, logoSpin 1s ease-out;
            filter: drop-shadow(0 0 25px #ff6b6b);
        }

        @keyframes logoSpin {
            0% { transform: rotate(0deg) scale(0); }
            50% { transform: rotate(180deg) scale(1.2); }
            100% { transform: rotate(360deg) scale(1); }
        }

        @keyframes logoPulse {
            0%, 100% { filter: drop-shadow(0 0 15px #ff6b6b); }
            50% { filter: drop-shadow(0 0 35px #ffd93d); }
        }

        .header h1 {
            font-size: 36px;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d, #38ef7d, #ff6b6b);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 3s infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .premium-badge {
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            padding: 4px 14px;
            border-radius: 30px;
            font-size: 10px;
            font-weight: bold;
            color: #0a0a0a;
            display: inline-block;
            margin-top: 8px;
            animation: badgeGlow 2s infinite;
        }

        @keyframes badgeGlow {
            0%, 100% { box-shadow: 0 0 5px #ff6b6b; }
            50% { box-shadow: 0 0 20px #ffd93d; }
        }

        .ip-info {
            background: rgba(26, 26, 46, 0.8);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            padding: 10px 22px;
            margin-top: 15px;
            font-size: 12px;
            font-weight: bold;
            color: #ffd93d;
            text-align: center;
            display: inline-block;
            border: 1px solid rgba(255,107,107,0.4);
            box-shadow: 0 0 25px rgba(255,107,107,0.2);
            animation: borderPulse 2s infinite;
        }

        @keyframes borderPulse {
            0%, 100% { border-color: rgba(255,107,107,0.4); box-shadow: 0 0 15px rgba(255,107,107,0.2); }
            50% { border-color: rgba(255,217,61,0.6); box-shadow: 0 0 30px rgba(255,217,61,0.3); }
        }

        /* ========== স্ট্যাটস কার্ড ========== */
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 25px;
        }

        .stat-box {
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.9), rgba(22, 30, 62, 0.9));
            backdrop-filter: blur(10px);
            border-radius: 22px;
            padding: 18px 12px;
            text-align: center;
            border: 1px solid rgba(255,107,107,0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            animation: statFade 0.6s ease-out backwards;
        }

        .stat-box:nth-child(1) { animation-delay: 0.1s; }
        .stat-box:nth-child(2) { animation-delay: 0.2s; }
        .stat-box:nth-child(3) { animation-delay: 0.3s; }

        @keyframes statFade {
            from { opacity: 0; transform: translateY(30px) scale(0.9); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .stat-box:hover {
            transform: translateY(-8px) scale(1.02);
            border-color: #ff6b6b;
            box-shadow: 0 15px 35px rgba(255,107,107,0.25);
        }

        .stat-box h4 {
            font-size: 11px;
            color: #ccc;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }

        .stat-box .number {
            font-size: 34px;
            font-weight: 800;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: numberPop 0.5s ease;
        }

        @keyframes numberPop {
            0% { transform: scale(0.5); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }

        /* ========== কার্ড ========== */
        .card {
            background: rgba(15, 15, 30, 0.85);
            backdrop-filter: blur(12px);
            border-radius: 28px;
            padding: 25px;
            margin-bottom: 22px;
            border: 1px solid rgba(255,107,107,0.2);
            transition: all 0.4s;
            animation: cardSlide 0.7s ease-out backwards;
        }

        .card:nth-child(1) { animation-delay: 0.1s; }
        .card:nth-child(2) { animation-delay: 0.2s; }
        .card:nth-child(3) { animation-delay: 0.3s; }
        .card:nth-child(4) { animation-delay: 0.4s; }
        .card:nth-child(5) { animation-delay: 0.5s; }

        @keyframes cardSlide {
            from { opacity: 0; transform: translateX(-40px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .card:hover {
            transform: translateY(-6px);
            border-color: rgba(255,107,107,0.5);
            box-shadow: 0 20px 40px rgba(0,0,0,0.4), 0 0 20px rgba(255,107,107,0.1);
        }

        .card-title {
            font-size: 20px;
            font-weight: bold;
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
            border-left: 4px solid #ff6b6b;
            padding-left: 15px;
        }

        /* ========== ইনপুট ========== */
        .input-group {
            margin-bottom: 18px;
        }

        .input-group input {
            width: 100%;
            padding: 15px;
            border: 2px solid #2a2a4a;
            border-radius: 18px;
            font-size: 15px;
            transition: all 0.3s;
            background: #0a0a15;
            color: white;
        }

        .input-group input:focus {
            outline: none;
            border-color: #ff6b6b;
            box-shadow: 0 0 15px rgba(255,107,107,0.3);
            transform: scale(1.01);
        }

        /* ========== বাটন ========== */
        .btn {
            width: 100%;
            padding: 14px;
            font-size: 15px;
            font-weight: bold;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            color: white;
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }

        .btn::after {
            content: '';
            position: absolute;
            top: -50%;
            left: -60%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.3), transparent);
            transform: rotate(45deg);
            transition: 0.5s;
            opacity: 0;
        }

        .btn:hover::after {
            opacity: 1;
            transform: rotate(45deg) translate(30%, 30%);
        }

        .btn-add {
            background: linear-gradient(135deg, #11998e, #38ef7d);
            box-shadow: 0 5px 20px rgba(56,239,125,0.3);
        }

        .btn-add:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(56,239,125,0.5);
        }

        .btn-start {
            background: linear-gradient(135deg, #667eea, #764ba2);
            box-shadow: 0 5px 20px rgba(102,126,234,0.3);
        }

        .btn-start:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102,126,234,0.5);
        }

        .btn-stop {
            background: linear-gradient(135deg, #eb3349, #f45c43);
            box-shadow: 0 5px 20px rgba(235,51,73,0.3);
        }

        .btn-stop:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(235,51,73,0.5);
        }

        /* ========== টার্গেট লিস্ট ========== */
        .target-list {
            max-height: 260px;
            overflow-y: auto;
        }

        .target-list::-webkit-scrollbar {
            width: 5px;
        }

        .target-list::-webkit-scrollbar-track {
            background: #1a1a2e;
            border-radius: 10px;
        }

        .target-list::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #ff6b6b, #ffd93d);
            border-radius: 10px;
        }

        .target-item {
            background: linear-gradient(95deg, #0a0a15, #0f0f1a);
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #ff6b6b;
            transition: all 0.3s;
            animation: itemSlide 0.3s ease;
        }

        @keyframes itemSlide {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }

        .target-item:hover {
            transform: translateX(5px);
            background: linear-gradient(95deg, #121225, #151530);
            border-left-color: #ffd93d;
        }

        .target-item span {
            font-family: monospace;
            font-size: 14px;
            font-weight: bold;
            color: #ffd93d;
        }

        .badge {
            background: linear-gradient(135deg, #38ef7d, #11998e);
            color: #0a0a0a;
            font-size: 9px;
            padding: 2px 10px;
            border-radius: 20px;
            margin-left: 10px;
            font-weight: bold;
        }

        .small-btn {
            padding: 5px 14px;
            font-size: 11px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: 0.2s;
        }

        .small-stop {
            background: linear-gradient(135deg, #eb3349, #f45c43);
            color: white;
        }

        .small-stop:hover {
            transform: scale(1.05);
            box-shadow: 0 0 10px #eb3349;
        }

        .small-remove {
            background: linear-gradient(135deg, #f45c43, #eb3349);
            color: white;
        }

        .small-remove:hover {
            transform: scale(1.05);
            box-shadow: 0 0 10px #f45c43;
        }

        /* ========== অ্যালার্ট ========== */
        .alert {
            padding: 12px 18px;
            border-radius: 50px;
            margin-bottom: 20px;
            display: none;
            font-size: 13px;
            font-weight: 600;
            text-align: center;
            animation: alertShake 0.5s ease;
        }

        @keyframes alertShake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }

        .alert-success {
            background: #0f2e1a;
            color: #38ef7d;
            border-left: 5px solid #38ef7d;
            box-shadow: 0 0 15px rgba(56,239,125,0.2);
        }

        .alert-error {
            background: #2e1a1a;
            color: #ff6b6b;
            border-left: 5px solid #ff6b6b;
            box-shadow: 0 0 15px rgba(255,107,107,0.2);
        }

        /* ========== ফুটার ========== */
        .footer {
            text-align: center;
            padding: 18px;
            background: rgba(20, 20, 40, 0.7);
            backdrop-filter: blur(10px);
            border-radius: 28px;
            margin-top: 22px;
            border: 1px solid rgba(255,107,107,0.2);
            animation: footerFade 0.8s ease-out;
        }

        @keyframes footerFade {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .footer p {
            color: #aaa;
            font-size: 11px;
        }

        .glow-text {
            color: #ffd93d;
            font-weight: bold;
            text-shadow: 0 0 5px #ffd93d;
        }
    </style>
</head>
<body>
    <div class="block-bg">
        <div class="block"></div><div class="block"></div><div class="block"></div>
        <div class="block"></div><div class="block"></div><div class="block"></div>
        <div class="block"></div><div class="block"></div>
    </div>

    <div class="container">
        <div class="header">
            <div class="logo">✨🔥✨</div>
            <h1>SHAFIQ SPAM PRO</h1>
            <div class="premium-badge">PREMIUM LIGHTING EDITION</div>
            <div class="ip-info">⚡ SERVER ACTIVE | 💾 GITHUB SYNC | 🔄 AUTO RESTART</div>
        </div>

        <div id="alert" class="alert"></div>

        <div class="stats">
            <div class="stat-box"><h4>🎯 ACTIVE SPAM</h4><div class="number" id="activeCount">0</div></div>
            <div class="stat-box"><h4>👥 CONNECTED</h4><div class="number" id="accountCount">0</div></div>
            <div class="stat-box"><h4>📁 UNLIMITED</h4><div class="number" id="unlimitedCount">0</div></div>
        </div>

        <div class="card">
            <div class="card-title">➕ ADD UNLIMITED UID</div>
            <div class="input-group"><input type="text" id="addUid" placeholder="Enter UID (e.g., 3020431227)" /></div>
            <button class="btn btn-add" onclick="addUID()">✨ ADD TO UNLIMITED</button>
            <div class="input-group" style="margin-top: 18px;"><input type="text" id="manualUid" placeholder="Manual Spam UID" /></div>
            <button class="btn btn-start" onclick="startManual()">⚡ START MANUAL SPAM</button>
        </div>

        <div class="card">
            <div class="card-title">🛑 STOP SPAM BY UID</div>
            <div class="input-group"><input type="text" id="stopUid" placeholder="Enter UID to stop" /></div>
            <button class="btn btn-stop" onclick="stopByUid()">⏹ STOP SPAM</button>
        </div>

        <div class="card">
            <div class="card-title">📋 UNLIMITED TARGETS <span class="badge">GITHUB SAVED</span></div>
            <div id="unlimitedList" class="target-list"><div style="text-align:center; color:#666; padding:20px;">✨ Loading... ✨</div></div>
            <p style="font-size: 10px; color: #555; margin-top: 10px; text-align: center;">💾 Data saved to GitHub | Auto-start on restart</p>
        </div>

        <div class="card">
            <div class="card-title">⚡ ACTIVE SPAM TARGETS</div>
            <div id="activeList" class="target-list"><div style="text-align:center; color:#666; padding:20px;">✨ No active spam ✨</div></div>
            <p style="font-size: 10px; color: #555; margin-top: 10px; text-align: center;">👉 Click STOP button to stop individual spam</p>
        </div>

        <div class="footer">
            <p>🔒 <span class="glow-text">SHAFIQ SPAM PRO</span> | Premium Lighting | No Data Loss</p>
            <p>✅ One by one stop | Stop by UID | Auto restart spam</p>
        </div>
    </div>

    <script>
        function showAlert(msg, type) {
            let div = document.getElementById('alert');
            div.textContent = msg;
            div.className = `alert alert-${type}`;
            div.style.display = 'block';
            setTimeout(() => div.style.display = 'none', 3500);
        }

        async function addUID() {
            let uid = document.getElementById('addUid').value.trim();
            if (!uid) return showAlert('❌ Please enter UID!', 'error');
            showAlert('⏳ Adding to GitHub...', 'success');
            try {
                let res = await fetch(`/add_unlimited?user_id=${uid}`);
                let data = await res.json();
                showAlert(data.message, data.status);
                if (data.status == 'success') {
                    document.getElementById('addUid').value = '';
                    refreshStatus();
                }
            } catch(e) { showAlert('❌ Connection error!', 'error'); }
        }

        async function startManual() {
            let uid = document.getElementById('manualUid').value.trim();
            if (!uid) return showAlert('❌ Please enter UID!', 'error');
            showAlert('⏳ Starting spam...', 'success');
            try {
                let res = await fetch(`/spam?user_id=${uid}`);
                let data = await res.json();
                showAlert(data.message, data.status);
                document.getElementById('manualUid').value = '';
                refreshStatus();
            } catch(e) { showAlert('❌ Error!', 'error'); }
        }

        async function stopByUid() {
            let uid = document.getElementById('stopUid').value.trim();
            if (!uid) return showAlert('❌ Please enter UID to stop!', 'error');
            try {
                let res = await fetch(`/stop?user_id=${uid}`);
                let data = await res.json();
                showAlert(data.message, data.status);
                document.getElementById('stopUid').value = '';
                refreshStatus();
            } catch(e) { showAlert('❌ Error!', 'error'); }
        }

        async function removeUID(uid) {
            if (!confirm(`⚠️ Remove ${uid} from unlimited targets?`)) return;
            try {
                let res = await fetch(`/remove_unlimited?user_id=${uid}`);
                let data = await res.json();
                showAlert(data.message, data.status);
                refreshStatus();
            } catch(e) { showAlert('❌ Error!', 'error'); }
        }

        async function stopSingle(uid) {
            try {
                let res = await fetch(`/stop?user_id=${uid}`);
                let data = await res.json();
                showAlert(data.message, data.status);
                refreshStatus();
            } catch(e) { showAlert('❌ Error!', 'error'); }
        }

        async function refreshStatus() {
            try {
                let res = await fetch('/status');
                let data = await res.json();
                if (data.status == 'success') {
                    document.getElementById('activeCount').innerText = data.data.active_targets_count || 0;
                    document.getElementById('accountCount').innerText = data.data.connected_accounts_count || 0;
                    document.getElementById('unlimitedCount').innerText = data.data.unlimited_targets_count || 0;

                    let activeHtml = '';
                    data.data.active_targets.forEach(uid => {
                        activeHtml += `<div class="target-item"><span>⚡ ${uid}</span><button class="small-btn small-stop" onclick="stopSingle('${uid}')">STOP</button></div>`;
                    });
                    document.getElementById('activeList').innerHTML = activeHtml || '<div style="text-align:center; color:#666; padding:20px;">✨ No active spam ✨</div>';

                    let unlimitedHtml = '';
                    data.data.unlimited_targets.forEach(uid => {
                        unlimitedHtml += `<div class="target-item"><span>📁 ${uid} <span class="badge">AUTO</span></span><button class="small-btn small-remove" onclick="removeUID('${uid}')">REMOVE</button></div>`;
                    });
                    document.getElementById('unlimitedList').innerHTML = unlimitedHtml || '<div style="text-align:center; color:#666; padding:20px;">✨ No unlimited targets ✨</div>';
                }
            } catch(e) { console.log(e); }
        }

        setInterval(refreshStatus, 3000);
        refreshStatus();
    </script>
</body>
</html>
'''

# ==================== সিস্টেম ফাংশন ====================
def run_api():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def AuTo_ResTartinG():
    time.sleep(6 * 60 * 60)
    print('\n🔄 AUTO RESTARTING...')
    p = psutil.Process(os.getpid())
    for handler in p.open_files():
        try:
            os.close(handler.fd)
        except Exception:
            pass
    for conn in p.net_connections():
        try:
            if hasattr(conn, 'fd'):
                os.close(conn.fd)
        except Exception:
            pass
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    python = sys.executable
    os.execl(python, python, *sys.argv)

Thread(target=AuTo_ResTartinG, daemon=True).start()

# ==================== অ্যাকাউন্ট লোড ====================
ACCOUNTS = []

def load_accounts_from_file(filename="accs.txt"):
    accounts = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):
                    if ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            account_id = parts[0].strip()
                            password = parts[1].strip()
                            accounts.append({'id': account_id, 'password': password})
                    else:
                        accounts.append({'id': line.strip(), 'password': ''})
        print(f"📁 Loaded {len(accounts)} accounts from {filename}")
    except FileNotFoundError:
        print(f"⚠️ {filename} not found! Please create accs.txt")
    return accounts

ACCOUNTS = load_accounts_from_file()

# ==================== ক্লায়েন্ট ক্লাস ====================
class FF_CLient():
    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.key = None
        self.iv = None
        self.Get_FiNal_ToKen_0115()     
            
    def Connect_SerVer_OnLine(self, Token, tok, host, port, key, iv, host2, port2):
        try:
            self.AutH_ToKen_0115 = tok    
            self.CliEnts2 = socket.create_connection((host2, int(port2)))
            self.CliEnts2.send(bytes.fromhex(self.AutH_ToKen_0115))                  
        except:
            pass        
        while True:
            try:
                self.DaTa2 = self.CliEnts2.recv(99999)
                if '0500' in self.DaTa2.hex()[0:4] and len(self.DaTa2.hex()) > 30:
                    self.packet = json.loads(DeCode_PackEt(f'08{self.DaTa2.hex().split("08", 1)[1]}'))
                    self.AutH = self.packet['5']['data']['7']['data']
            except:
                pass    	
                                                            
    def Connect_SerVer(self, Token, tok, host, port, key, iv, host2, port2):
        self.AutH_ToKen_0115 = tok    
        self.CliEnts = socket.create_connection((host, int(port)))
        self.CliEnts.send(bytes.fromhex(self.AutH_ToKen_0115))  
        self.DaTa = self.CliEnts.recv(1024)          	        
        threading.Thread(target=self.Connect_SerVer_OnLine, args=(Token, tok, host, port, key, iv, host2, port2)).start()
        self.Exemple = xMsGFixinG('12345678')
        self.key = key
        self.iv = iv
        with connected_clients_lock:
            connected_clients[self.id] = self
            print(f"✅ Account connected: {self.id} (Total: {len(connected_clients)})")
        while True:      
            try:
                self.DaTa = self.CliEnts.recv(1024)   
                if len(self.DaTa) == 0 or (hasattr(self, 'DaTa2') and len(self.DaTa2) == 0):
                    try:
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                        self.Connect_SerVer(Token, tok, host, port, key, iv, host2, port2)                    		                    
                    except:
                        try:
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token, tok, host, port, key, iv, host2, port2)
                        except:
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            ResTarT_BoT()	            
            except Exception as e:
                print(f"❌ Connection error {self.id}: {e}")
                try:
                    self.CliEnts.close()
                    if hasattr(self, 'CliEnts2'):
                        self.CliEnts2.close()
                except:
                    pass
                self.Connect_SerVer(Token, tok, host, port, key, iv, host2, port2)
                                    
    def GeT_Key_Iv(self, serialized_data):
        my_message = xKEys.MyMessage()
        my_message.ParseFromString(serialized_data)
        timestamp, key, iv = my_message.field21, my_message.field22, my_message.field23
        timestamp_obj = Timestamp()
        timestamp_obj.FromNanoseconds(timestamp)
        timestamp_seconds = timestamp_obj.seconds
        timestamp_nanos = timestamp_obj.nanos
        return timestamp_seconds * 1_000_000_000 + timestamp_nanos, key, iv    

    def Guest_GeneRaTe(self, uid, password):
        self.url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        self.headers = {"Host": "100067.connect.garena.com","User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)","Content-Type": "application/x-www-form-urlencoded","Accept-Encoding": "gzip, deflate, br","Connection": "close"}
        self.dataa = {"uid": f"{uid}","password": f"{password}","response_type": "token","client_type": "2","client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3","client_id": "100067"}
        try:
            self.response = requests.post(self.url, headers=self.headers, data=self.dataa).json()
            self.Access_ToKen, self.Access_Uid = self.response['access_token'], self.response['open_id']
            time.sleep(0.2)
            print(f'🔐 Login: {uid}')
            return self.ToKen_GeneRaTe(self.Access_ToKen, self.Access_Uid)
        except Exception as e: 
            print(f"❌ Login error {uid}: {e}")
            time.sleep(10)
            return self.Guest_GeneRaTe(uid, password)
                                        
    def GeT_LoGin_PorTs(self, JwT_ToKen, PayLoad):
        self.UrL = 'https://clientbp.ggblueshark.com/GetLoginData'
        self.HeadErs = {
            'Expect': '100-continue',
            'Authorization': f'Bearer {JwT_ToKen}',
            'X-Unity-Version': '2022.3.47f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': 'OB53',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Connection': 'close',
            'Accept-Encoding': 'deflate, gzip'
        }        
        try:
            self.Res = requests.post(self.UrL, headers=self.HeadErs, data=PayLoad, verify=False)
            self.BesTo_data = json.loads(DeCode_PackEt(self.Res.content.hex()))  
            address, address2 = self.BesTo_data['32']['data'], self.BesTo_data['14']['data'] 
            ip, ip2 = address[:len(address) - 6], address2[:len(address2) - 6]
            port, port2 = address[len(address) - 5:], address2[len(address2) - 5:]             
            return ip, port, ip2, port2          
        except:
            return None, None, None, None
        
    def ToKen_GeneRaTe(self, Access_ToKen, Access_Uid):
        self.UrL = "https://loginbp.ggwhitehawk.com/MajorLogin"
        self.HeadErs = {
            'X-Unity-Version': '2022.3.47f1',
            'ReleaseVersion': 'OB53',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-GA': 'v1 1',
            'Content-Length': '928',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Host': 'loginbp.ggwhitehawk.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'deflate, gzip'
        }   
        self.dT = bytes.fromhex('1a13323032352d31312d32362030313a35313a3238220966726565206669726528013a07312e3132332e314232416e64726f6964204f532039202f204150492d3238202850492f72656c2e636a772e32303232303531382e313134313333294a0848616e6468656c64520c4d544e2f537061636574656c5a045749464960800a68d00572033234307a2d7838362d3634205353453320535345342e3120535345342e32204156582041565832207c2032343030207c20348001e61e8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e329a012b476f6f676c657c36323566373136662d393161372d343935622d396631362d303866653964336336353333a2010e3137362e32382e3133392e313835aa01026172b201203433303632343537393364653836646134323561353263616164663231656564ba010134c2010848616e6468656c64ca010d4f6e65506c7573204135303130ea014063363961653230386661643732373338623637346232383437623530613361316466613235643161313966616537343566633736616334613065343134633934f00101ca020c4d544e2f537061636574656cd2020457494649ca03203161633462383065636630343738613434323033626638666163363132306635e003b5ee02e8039a8002f003af13f80384078004a78f028804b5ee029004a78f029804b5ee02b00404c80401d2043d2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f6c69622f61726de00401ea045f65363261623933353464386662356662303831646233333861636233333439317c2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f626173652e61706bf00406f804018a050233329a050a32303139313139303236a80503b205094f70656e474c455332b805ff01c00504e005be7eea05093372645f7061727479f205704b717348543857393347646347335a6f7a454e6646775648746d377171316552554e6149444e67526f626f7a4942744c4f695943633459367a767670634943787a514632734f453463627974774c7334785a62526e70524d706d5752514b6d654f35766373386e51594268777148374bf805e7e4068806019006019a060134a2060134b2062213521146500e590349510e460900115843395f005b510f685b560a6107576d0f0366')
        self.dT = self.dT.replace(b'2025-07-30 14:11:20', str(datetime.now())[:-7].encode())        
        self.dT = self.dT.replace(b'c69ae208fad72738b674b2847b50a3a1dfa25d1a19fae745fc76ac4a0e414c94', Access_ToKen.encode())
        self.dT = self.dT.replace(b'4306245793de86da425a52caadf21eed', Access_Uid.encode())
        try:
            hex_data = self.dT.hex()
            encoded_data = EnC_AEs(hex_data)
            if not all(c in '0123456789abcdefABCDEF' for c in encoded_data):
                encoded_data = hex_data
            self.PaYload = bytes.fromhex(encoded_data)
        except:
            self.PaYload = self.dT
        self.ResPonse = requests.post(self.UrL, headers=self.HeadErs, data=self.PaYload, verify=False)        
        if self.ResPonse.status_code == 200 and len(self.ResPonse.text) > 10:
            try:
                self.BesTo_data = json.loads(DeCode_PackEt(self.ResPonse.content.hex()))
                self.JwT_ToKen = self.BesTo_data['8']['data']           
                self.combined_timestamp, self.key, self.iv = self.GeT_Key_Iv(self.ResPonse.content)
                ip, port, ip2, port2 = self.GeT_LoGin_PorTs(self.JwT_ToKen, self.PaYload)            
                return self.JwT_ToKen, self.key, self.iv, self.combined_timestamp, ip, port, ip2, port2
            except:
                time.sleep(5)
                return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
        else:
            time.sleep(5)
            return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
      
    def Get_FiNal_ToKen_0115(self):
        try:
            result = self.Guest_GeneRaTe(self.id, self.password)
            if not result:
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
            token, key, iv, Timestamp, ip, port, ip2, port2 = result
            if not all([ip, port, ip2, port2]):
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
            self.JwT_ToKen = token        
            try:
                self.AfTer_DeC_JwT = jwt.decode(token, options={"verify_signature": False})
                self.AccounT_Uid = self.AfTer_DeC_JwT.get('account_id')
                self.EncoDed_AccounT = hex(self.AccounT_Uid)[2:]
                self.HeX_VaLue = DecodE_HeX(Timestamp)
                self.TimE_HEx = self.HeX_VaLue
                self.JwT_ToKen_ = token.encode().hex()
                print(f'🆔 Account UID: {self.AccounT_Uid}')
            except:
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
            try:
                self.Header = hex(len(EnC_PacKeT(self.JwT_ToKen_, key, iv)) // 2)[2:]
                length = len(self.EncoDed_AccounT)
                self.__ = '00000000'
                if length == 9: self.__ = '0000000'
                elif length == 8: self.__ = '00000000'
                elif length == 10: self.__ = '000000'
                elif length == 7: self.__ = '000000000'
                self.Header = f'0115{self.__}{self.EncoDed_AccounT}{self.TimE_HEx}00000{self.Header}'
                self.FiNal_ToKen_0115 = self.Header + EnC_PacKeT(self.JwT_ToKen_, key, iv)
            except:
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
            self.AutH_ToKen = self.FiNal_ToKen_0115
            self.Connect_SerVer(self.JwT_ToKen, self.AutH_ToKen, ip, port, key, iv, ip2, port2)        
            return self.AutH_ToKen, key, iv
        except:
            time.sleep(10)
            return self.Get_FiNal_ToKen_0115()

def start_account(account):
    try:
        print(f"🚀 Starting account: {account['id']}")
        FF_CLient(account['id'], account['password'])
    except:
        time.sleep(5)
        start_account(account)

def ResTarT_BoT():
    print('\n🔄 RESTARTING...')
    p = psutil.Process(os.getpid())
    for handler in p.open_files():
        try:
            os.close(handler.fd)
        except:
            pass           
    for conn in p.net_connections():
        try:
            conn.close()
        except:
            pass
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    python = sys.executable
    os.execl(python, python, *sys.argv)

def StarT_SerVer():
    print("🔄 Loading unlimited targets from GitHub...")
    load_and_start_unlimited_targets()
    
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    for account in ACCOUNTS:
        threading.Thread(target=start_account, args=(account,), daemon=True).start()
        time.sleep(3)
    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     ✨🔥 SHAFIQ SPAM PRO - PREMIUM LIGHTING EDITION 🔥✨         ║
    ║     💾 GitHub Sync | No Data Loss | Auto Restart                 ║
    ║     🌐 Web Panel: http://127.0.0.1:5000                          ║
    ║                                                                  ║
    ║  ✅ Connected accounts count visible                             ║
    ║  ✅ One by one stop | Stop by UID                                ║
    ║  ✅ Premium lighting effects + animations                        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    StarT_SerVer()