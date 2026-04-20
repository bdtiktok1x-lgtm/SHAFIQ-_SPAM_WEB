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

app = Flask(__name__)

# ==================== স্প্যাম ক্লাস ====================
class SimpleAPI:
    def __init__(self):
        self.running = True
        
    def process_spam_command(self, target_id, duration_minutes=None):
        try:
            if not ChEck_Commande(target_id):
                return {"status": "error", "message": "Invalid User ID"}
                
            with active_spam_lock:
                if target_id not in active_spam_targets:
                    active_spam_targets[target_id] = {
                        'active': True,
                        'start_time': datetime.now(),
                        'duration': duration_minutes
                    }
                    threading.Thread(target=spam_worker, args=(target_id, duration_minutes), daemon=True).start()
                    message = f"✅ SPAM STARTED ON: {target_id}"
                    if duration_minutes:
                        message += f" FOR {duration_minutes} MINUTES"
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f"⚠️ SPAM ALREADY RUNNING ON: {target_id}"}
                    
        except Exception as e:
            return {"status": "error", "message": f"❌ ERROR: {str(e)}"}
            
    def process_stop_command(self, target_id):
        try:
            with active_spam_lock:
                if target_id in active_spam_targets:
                    del active_spam_targets[target_id]
                    message = f"🛑 SPAM STOPPED ON: {target_id}"
                    return {"status": "success", "message": message}
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
                
            status_data = {
                "active_targets_count": len(active_targets),
                "active_targets": active_targets,
                "connected_accounts_count": accounts_count,
                "connected_accounts": accounts_list
            }
            
            return {"status": "success", "data": status_data}
            
        except Exception as e:
            return {"status": "error", "message": f"STATUS ERROR: {str(e)}"}

# ==================== স্প্যাম ওয়ার্কার ====================
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

api = SimpleAPI()

# ==================== ওয়েব এপি রাউট ====================
@app.route('/spam', methods=['GET'])
def start_spam():
    target_id = request.args.get('user_id')
    duration = request.args.get('duration', type=int)
    
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    
    result = api.process_spam_command(target_id, duration)
    return jsonify(result)

@app.route('/stop', methods=['GET'])
def stop_spam():
    target_id = request.args.get('user_id')
    
    if not target_id:
        return jsonify({"status": "error", "message": "Please provide USER ID"})
    
    result = api.process_stop_command(target_id)
    return jsonify(result)

@app.route('/status', methods=['GET'])
def get_status():
    result = api.get_status()
    return jsonify(result)

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        <title>SHAFIQ SPAM - Ultimate Spam Tool</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Poppins', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 500px;
                margin: 0 auto;
            }

            /* Header */
            .header {
                text-align: center;
                margin-bottom: 30px;
            }

            .logo {
                font-size: 48px;
                margin-bottom: 10px;
            }

            .header h1 {
                font-size: 32px;
                background: linear-gradient(135deg, #ff6b6b, #ffd93d);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                letter-spacing: 2px;
            }

            .header p {
                color: #aaa;
                font-size: 14px;
                margin-top: 5px;
            }

            .ip-info {
                background: rgba(255,255,255,0.1);
                border-radius: 10px;
                padding: 8px;
                margin-top: 15px;
                font-size: 12px;
                color: #ffd93d;
                text-align: center;
            }

            /* Cards */
            .card {
                background: rgba(255,255,255,0.95);
                border-radius: 20px;
                padding: 25px;
                margin-bottom: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }

            .card-title {
                font-size: 22px;
                font-weight: bold;
                color: #302b63;
                margin-bottom: 20px;
                border-left: 4px solid #ff6b6b;
                padding-left: 15px;
            }

            /* Input Groups */
            .input-group {
                margin-bottom: 20px;
            }

            .input-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #333;
                font-size: 14px;
            }

            .input-group input {
                width: 100%;
                padding: 14px;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                font-size: 16px;
                transition: all 0.3s;
                background: #f8f9fa;
            }

            .input-group input:focus {
                outline: none;
                border-color: #ff6b6b;
                background: white;
            }

            .example {
                font-size: 12px;
                color: #888;
                margin-top: 5px;
                display: block;
            }

            /* Buttons */
            .btn {
                width: 100%;
                padding: 14px;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                color: white;
            }

            .btn-start {
                background: linear-gradient(135deg, #11998e, #38ef7d);
                box-shadow: 0 5px 20px rgba(56,239,125,0.3);
            }

            .btn-start:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(56,239,125,0.4);
            }

            .btn-stop {
                background: linear-gradient(135deg, #eb3349, #f45c43);
                box-shadow: 0 5px 20px rgba(235,51,73,0.3);
            }

            .btn-stop:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(235,51,73,0.4);
            }

            /* Stats */
            .stats {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }

            .stat-box {
                background: linear-gradient(135deg, #667eea, #764ba2);
                border-radius: 15px;
                padding: 15px;
                text-align: center;
                color: white;
            }

            .stat-box h4 {
                font-size: 12px;
                opacity: 0.9;
                margin-bottom: 8px;
            }

            .stat-box .number {
                font-size: 28px;
                font-weight: bold;
            }

            /* Active List */
            .active-list {
                max-height: 150px;
                overflow-y: auto;
            }

            .active-item {
                background: #f0f0f0;
                padding: 10px;
                margin: 8px 0;
                border-radius: 10px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .active-item span {
                font-family: monospace;
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }

            .stop-small {
                background: #eb3349;
                color: white;
                border: none;
                padding: 5px 12px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }

            /* Alert */
            .alert {
                padding: 12px;
                border-radius: 12px;
                margin-bottom: 20px;
                display: none;
                font-size: 14px;
                font-weight: 500;
            }

            .alert-success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }

            .alert-error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }

            .alert-info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }

            /* Footer Social */
            .social-footer {
                text-align: center;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                margin-top: 20px;
            }

            .social-footer h4 {
                color: white;
                margin-bottom: 15px;
                font-size: 16px;
            }

            .social-links {
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }

            .social-links a {
                color: white;
                text-decoration: none;
                font-size: 14px;
                padding: 8px 16px;
                background: rgba(255,255,255,0.2);
                border-radius: 25px;
                transition: 0.3s;
            }

            .social-links a:hover {
                background: #ff6b6b;
                transform: translateY(-2px);
            }

            .admin-info {
                text-align: center;
                color: #aaa;
                font-size: 12px;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid rgba(255,255,255,0.1);
            }

            .footer-note {
                text-align: center;
                color: #ffd93d;
                font-size: 12px;
                margin-top: 20px;
            }

            hr {
                margin: 20px 0;
                border-color: rgba(255,255,255,0.1);
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .loading {
                animation: pulse 1s infinite;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="logo">🎯</div>
                <h1>SHAFIQ SPAM</h1>
                <p>Ultimate Spam Tool | Auto Like & Spam System</p>
                <div class="ip-info">
                    🌐 SERVER: 217.154.161.167:12078 | STATUS: ACTIVE
                </div>
            </div>

            <!-- Alert Box -->
            <div id="alert" class="alert"></div>

            <!-- Stats -->
            <div class="stats">
                <div class="stat-box">
                    <h4>🎯 ACTIVE TARGETS</h4>
                    <div class="number" id="activeCount">0</div>
                </div>
                <div class="stat-box">
                    <h4>👥 CONNECTED ACCOUNTS</h4>
                    <div class="number" id="accountCount">0</div>
                </div>
            </div>

            <!-- START SPAM CARD -->
            <div class="card">
                <div class="card-title">🚀 START SPAM</div>
                <div class="input-group">
                    <label>TARGET UID</label>
                    <input type="text" id="startUserId" placeholder="Enter Target UID" />
                    <span class="example">📌 Example: 3020431227</span>
                </div>
                <button class="btn btn-start" onclick="startSpam()">▶ SEND LIKE / START SPAM</button>
            </div>

            <!-- STOP SPAM CARD -->
            <div class="card">
                <div class="card-title">🛑 STOP SPAM</div>
                <div class="input-group">
                    <label>TARGET UID</label>
                    <input type="text" id="stopUserId" placeholder="Enter Target UID to Stop" />
                    <span class="example">📌 Enter the UID you want to stop</span>
                </div>
                <button class="btn btn-stop" onclick="stopSpam()">⏹ STOP SPAM</button>
            </div>

            <!-- ACTIVE SPAM LIST -->
            <div class="card">
                <div class="card-title">📊 ACTIVE SPAM TARGETS</div>
                <div id="activeSpamList" class="active-list">
                    <div style="text-align:center; color:#888; padding:20px;">Loading...</div>
                </div>
            </div>

            <!-- Social Footer -->
            <div class="social-footer">
                <h4>🔗 FOLLOW US</h4>
                <div class="social-links">
                    <a href="#" target="_blank">📷 Instagram</a>
                    <a href="#" target="_blank">🎵 TikTok</a>
                    <a href="#" target="_blank">📨 Telegram</a>
                    <a href="#" target="_blank">💬 WhatsApp</a>
                </div>
                <div class="admin-info">
                    <strong>INSTA/TT:</strong> Emnii_999x | <strong>TG:</strong> Emnii_999x
                </div>
            </div>

            <div class="footer-note">
                ⚡ POWERED BY SHAFIQ SPAM SYSTEM | ALL ACCOUNTS ACTIVE
            </div>
        </div>

        <script>
            function showAlert(message, type) {
                const alertDiv = document.getElementById('alert');
                alertDiv.textContent = message;
                alertDiv.className = `alert alert-${type}`;
                alertDiv.style.display = 'block';
                setTimeout(() => {
                    alertDiv.style.display = 'none';
                }, 4000);
            }

            async function startSpam() {
                const userId = document.getElementById('startUserId').value.trim();
                if (!userId) {
                    showAlert('❌ Please enter TARGET UID!', 'error');
                    return;
                }

                showAlert('⏳ Starting spam on ' + userId + '...', 'info');

                try {
                    const response = await fetch(`/spam?user_id=${userId}`);
                    const data = await response.json();

                    if (data.status === 'success') {
                        showAlert('✅ ' + data.message, 'success');
                        document.getElementById('startUserId').value = '';
                        refreshStatus();
                    } else {
                        showAlert('❌ ' + data.message, 'error');
                    }
                } catch (error) {
                    showAlert('❌ Connection Error! Make sure server is running.', 'error');
                }
            }

            async function stopSpam() {
                const userId = document.getElementById('stopUserId').value.trim();
                if (!userId) {
                    showAlert('❌ Please enter TARGET UID to stop!', 'error');
                    return;
                }

                showAlert('⏳ Stopping spam on ' + userId + '...', 'info');

                try {
                    const response = await fetch(`/stop?user_id=${userId}`);
                    const data = await response.json();

                    if (data.status === 'success') {
                        showAlert('✅ ' + data.message, 'success');
                        document.getElementById('stopUserId').value = '';
                        refreshStatus();
                    } else {
                        showAlert('❌ ' + data.message, 'error');
                    }
                } catch (error) {
                    showAlert('❌ Connection Error!', 'error');
                }
            }

            async function refreshStatus() {
                try {
                    const response = await fetch('/status');
                    const data = await response.json();

                    if (data.status === 'success') {
                        const activeCount = data.data.active_targets_count || 0;
                        const accountCount = data.data.connected_accounts_count || 0;

                        document.getElementById('activeCount').textContent = activeCount;
                        document.getElementById('accountCount').textContent = accountCount;

                        const activeListDiv = document.getElementById('activeSpamList');
                        if (data.data.active_targets && data.data.active_targets.length > 0) {
                            activeListDiv.innerHTML = data.data.active_targets.map(target => 
                                `<div class="active-item">
                                    <span>🎯 ${target}</span>
                                    <button class="stop-small" onclick="stopFromList('${target}')">STOP</button>
                                </div>`
                            ).join('');
                        } else {
                            activeListDiv.innerHTML = '<div style="text-align:center; color:#888; padding:20px;">📭 No active spam targets</div>';
                        }
                    }
                } catch (error) {
                    console.error('Status error:', error);
                }
            }

            async function stopFromList(userId) {
                document.getElementById('stopUserId').value = userId;
                await stopSpam();
            }

            // Auto refresh every 3 seconds
            setInterval(refreshStatus, 3000);
            refreshStatus();

            // Enter key support
            document.getElementById('startUserId').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') startSpam();
            });
            document.getElementById('stopUserId').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') stopSpam();
            });
        </script>
    </body>
    </html>
    """

# ==================== সিস্টেম ফাংশন ====================
def run_api():
    print("🌐 WEB SERVER STARTING...")
    print("📱 OPEN: http://127.0.0.1:5000")
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
       
def ResTarT_BoT():
    print('\n🔄 RESTARTING...')
    p = psutil.Process(os.getpid())
    open_files = p.open_files()
    connections = p.net_connections()
    for handler in open_files:
        try:
            os.close(handler.fd)
        except Exception:
            pass           
    for conn in connections:
        try:
            conn.close()
        except Exception:
            pass
    sys.path.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    python = sys.executable
    os.execl(python, python, *sys.argv)

def GeT_Time(timestamp):
    last_login = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - last_login   
    d = diff.days
    h, rem = divmod(diff.seconds, 3600)
    m, s = divmod(rem, 60)    
    return d, h, m, s

def Time_En_Ar(t): 
    return ' '.join(t.replace("Day","Day").replace("Hour","Hour").replace("Min","Min").replace("Sec","Sec").split(" - "))
    
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
    except Exception as e:
        print(f"❌ Error: {e}")
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
        combined_timestamp = timestamp_seconds * 1_000_000_000 + timestamp_nanos
        return combined_timestamp, key, iv    

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
        except requests.RequestException:
            print(f"❌ Failed to get ports!")
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
        except Exception as e:
            print(f"❌ Encoding error: {e}")
            self.PaYload = self.dT
        
        self.ResPonse = requests.post(self.UrL, headers=self.HeadErs, data=self.PaYload, verify=False)        
        if self.ResPonse.status_code == 200 and len(self.ResPonse.text) > 10:
            try:
                self.BesTo_data = json.loads(DeCode_PackEt(self.ResPonse.content.hex()))
                self.JwT_ToKen = self.BesTo_data['8']['data']           
                self.combined_timestamp, self.key, self.iv = self.GeT_Key_Iv(self.ResPonse.content)
                ip, port, ip2, port2 = self.GeT_LoGin_PorTs(self.JwT_ToKen, self.PaYload)            
                return self.JwT_ToKen, self.key, self.iv, self.combined_timestamp, ip, port, ip2, port2
            except Exception as e:
                print(f"❌ Response parsing error: {e}")
                time.sleep(5)
                return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
        else:
            print(f"❌ Token generation error, status: {self.ResPonse.status_code}")
            time.sleep(5)
            return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
      
    def Get_FiNal_ToKen_0115(self):
        try:
            result = self.Guest_GeneRaTe(self.id, self.password)
            if not result:
                print(f"⚠️ Failed to get token {self.id}, retrying...")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            token, key, iv, Timestamp, ip, port, ip2, port2 = result
            
            if not all([ip, port, ip2, port2]):
                print(f"⚠️ Failed to get ports {self.id}, retrying...")
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
            except Exception as e:
                print(f"❌ Token decode error {self.id}: {e}")
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
            except Exception as e:
                print(f"❌ Final token error {self.id}: {e}")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            self.AutH_ToKen = self.FiNal_ToKen_0115
            self.Connect_SerVer(self.JwT_ToKen, self.AutH_ToKen, ip, port, key, iv, ip2, port2)        
            return self.AutH_ToKen, key, iv
            
        except Exception as e:
            print(f"❌ {self.id} connection failed: {e}")
            time.sleep(10)
            return self.Get_FiNal_ToKen_0115()

def start_account(account):
    try:
        print(f"🚀 Starting account: {account['id']}")
        FF_CLient(account['id'], account['password'])
    except Exception as e:
        print(f"❌ {account['id']} failed to start: {e}")
        time.sleep(5)
        start_account(account)

def StarT_SerVer():
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    threads = []
    
    for account in ACCOUNTS:
        thread = threading.Thread(target=start_account, args=(account,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(3)
    
    for thread in threads:
        thread.join()

# ==================== মেইন এক্সিকিউশন ====================
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════╗
    ║       🎯 SHAFIQ SPAM SYSTEM 🎯             ║
    ║                                            ║
    ║     WEB PANEL: http://127.0.0.1:5000       ║
    ║                                            ║
    ║  API Endpoints:                            ║
    ║  - GET /spam?user_id=X                     ║
    ║  - GET /stop?user_id=X                     ║
    ║  - GET /status                             ║
    ╚════════════════════════════════════════════╝
    """)
    StarT_SerVer()