from flask import Flask, request, render_template_string, session
import os, requests, time, random, string, json, atexit
from threading import Thread, Event

app = Flask(name)                 # ✅ fully working
app.secret_key = 'WASU_SECRET_KEY'
app.debug = True

headers = {
'User-Agent': 'Mozilla/5.0',
'Accept': '/',
'Accept-Language': 'en-US,en;q=0.9',
}

───────── GLOBAL STATE & PERSISTENCE ─────────

stop_events, threads, active_users = {}, {}, {}
TASK_FILE = 'tasks.json'

def save_tasks():
with open(TASK_FILE, 'w', encoding='utf-8') as f:
json.dump(active_users, f, ensure_ascii=False, indent=2)

def load_tasks():
if not os.path.exists(TASK_FILE):
return
with open(TASK_FILE, 'r', encoding='utf-8') as f:
data = json.load(f)
for tid, info in data.items():
active_users[tid] = info
stop_events[tid] = Event()
if info.get('status') == 'ACTIVE':
if not info.get('fb_name'):
info['fb_name'] = fetch_profile_name(info['token'])
th = Thread(
target=send_messages,
args=(
info['tokens_all'],
info['thread_id'],
info['name'],
info.get('delay', 1),
info['msgs'],
tid
),
daemon=True
)
th.start()
threads[tid] = th

atexit.register(save_tasks)
load_tasks()

───────── FB PROFILE NAME ─────────

def fetch_profile_name(token: str) -> str:
try:
res = requests.get(
f'https://graph.facebook.com/me?access_token={token}',
timeout=8
)
return res.json().get('name', 'Unknown')
except Exception:
return 'Unknown'

───────── MESSAGE SENDER THREAD ─────────

def send_messages(tokens, thread_id, mn, delay, messages, task_id):
ev = stop_events[task_id]
tok_i, msg_i = 0, 0
total_tok, total_msg = len(tokens), len(messages)

while not ev.is_set():  
    tk  = tokens[tok_i]  
    msg = messages[msg_i]  
    try:  
        requests.post(  
            f'https://graph.facebook.com/v15.0/t_{thread_id}/',  
            data={'access_token': tk, 'message': f"{mn} {msg}"},  
            headers=headers,  
            timeout=10  
        )  
        print(f"[✔️ SENT] {msg[:40]}  via TOKEN-{tok_i+1}")  
    except Exception as e:  
        print("[⚠️ ERROR]", e)  

    tok_i = (tok_i + 1) % total_tok  
    msg_i = (msg_i + 1) % total_msg  
    time.sleep(delay)

───────── ROOT ─────────

@app.route('/', methods=['GET', 'POST'])
def home():
msg_html = stop_html = ""
if request.method == 'POST':
# ---------- START ----------
if 'txtFile' in request.files:
tokens = (
[request.form.get('singleToken').strip()]
if request.form.get('tokenOption') == 'single'
else request.files['tokenFile'].read()
.decode(errors='ignore')
.splitlines()
)
tokens = [t for t in tokens if t]

uid   = request.form.get('threadId','').strip()  
        hater = request.form.get('kidx','').strip()  
        delay = max(int(request.form.get('time',1) or 1),1)  
        file  = request.files['txtFile']  
        msgs  = [m for m in file.read()  
                          .decode(errors='ignore')  
                          .splitlines() if m]  

        if not (tokens and uid and hater and msgs):  
            msg_html = "<div class='alert alert-danger'>⚠️ All fields required!</div>"  
        else:  
            tid = 'bhatwasu' + ''.join(random.choices(  
                    string.ascii_letters+string.digits, k=10))  
            stop_events[tid] = Event()  
            th = Thread(  
                target=send_messages,  
                args=(tokens, uid, hater, delay, msgs, tid),  
                daemon=True  
            )  
            th.start()  
            threads[tid] = th  

            active_users[tid] = {  
                'name'       : hater,  
                'token'      : tokens[0],  
                'tokens_all' : tokens,  
                'fb_name'    : fetch_profile_name(tokens[0]),  
                'thread_id'  : uid,  
                'msg_file'   : file.filename or 'messages.txt',  
                'msgs'       : msgs,  
                'delay'      : delay,  
                'msg_count'  : len(msgs),  
                'status'     : 'ACTIVE'  
            }  
            save_tasks()  

            msg_html = f"""  
            <div class='stop-key'>  
                🔑 <b>STOP KEY↷</b><br>  
                <code>{tid}</code>  
            </div>"""  

    # ---------- STOP ----------  
    elif 'taskId' in request.form:  
        tid = request.form.get('taskId','').strip()  
        if tid in stop_events:  
            stop_events[tid].set()  
            if tid in active_users:  
                active_users[tid]['status'] = 'OFFLINE'  
            save_tasks()  
            stop_html = f"""  
            <div id='stopBox' class='stop-ok'>  
                ⏹️ <b>L O D E R  S T O P P E D ❌</b><br>  
                S T O P  K E Y➠ <code>{tid}</code>  
            </div>"""  
        else:  
            stop_html = f"""  
            <div id='stopBox' class='stop-bad'>  
                ❌ <b>INVALID KEY ➠</b><br><code>{tid}</code>  
            </div>"""  

# ---------- PAGE ----------  
return render_template_string('''

<!doctype html>

<html lang="en">  
<head>  
<meta charset="utf-8">  
<title>BHAT WASU MSG SPAMMER</title>  
<meta name="viewport" content="width=device-width,initial-scale=1">  
<link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css"  
      rel="stylesheet" integrity="sha384-whatever" crossorigin="anonymous">  
<style>  
/* SATRANGI animated gradient background */  
body{  
  min-height:100vh;  
  display:flex;  
  justify-content:center;  
  align-items:start;  
  padding-top:40px;  
  color:#fff;  
  font-family: 'Poppins', sans-serif;  
  background: linear-gradient(45deg,#ff0000,#ff7f00,#ffff00,#00ff00,#0000ff,#4b0082,#8f00ff);  
  background-size: 600% 600%;  
  animation: rainbowMove 18s ease infinite;  
}  
@keyframes rainbowMove{  
  0%{background-position:0% 50%}  
  50%{background-position:100% 50%}  
  100%{background-position:0% 50%}  
}  
h1,h2,label{text-shadow:0 0 6px #000;}  
.card-dark{  
  background:rgba(0,0,0,0.65);  
  border:2px solid lime;  
  border-radius:1.5rem;  
  padding:1.25rem;  
}  
.stop-key{  
  padding:18px;margin-top:18px;background:black;color:lime;  
  border:2px solid lime;border-radius:22px;font-size:1.1rem;text-align:center  
}  
.stop-ok{  
  padding:18px;margin-top:18px;background:darkred;color:white;  
  border:2px solid lime;border-radius:22px;font-size:1.1rem;text-align:center  
}  
.stop-bad{  
  padding:18px;margin-top:18px;background:gray;color:white;  
  border:2px solid lime;border-radius:22px;font-size:1.1rem;text-align:center  
}  
input,select,button{  
  border-radius:.8rem!important;  
}  
</style>  
<script>  
function toggleTokenOption(type){  
  document.getElementById('singleTokenDiv').style.display = (type==='single')?'block':'none';  
  document.getElementById('tokenFileDiv').style.display  = (type==='file')?'block':'none';  
}  
</script>  
</head>  
<body>  <div class="container">  
  <h1 class="text-center mb-4">👿 OWNER BHAT WASU 👿</h1>  
  <div class="card-dark">  
    <form method="POST" enctype="multipart/form-data">  <h2 class="text-center mb-3">🍁 BROKEN NADEEM 🍁</h2>  

  <!-- TOKEN OPTION -->  
  <div class="mb-3">  
    <label class="form-label">⇣ SELECT TOKEN OPTION ⇣</label><br>  
    <div class="form-check form-check-inline">  
      <input class="form-check-input" type="radio" name="tokenOption"  
             id="tokenOptSingle" value="single" checked  
             onclick="toggleTokenOption('single')">  
      <label class="form-check-label" for="tokenOptSingle">ENTER SINGLE TOKEN</label>  
    </div>  
    <div class="form-check form-check-inline">  
      <input class="form-check-input" type="radio" name="tokenOption"  
             id="tokenOptFile" value="file"  
             onclick="toggleTokenOption('file')">  
      <label class="form-check-label" for="tokenOptFile">SELECT TOKEN FILE</label>  
    </div>  
  </div>  

  <!-- SINGLE TOKEN -->  
  <div id="singleTokenDiv" class="mb-3">  
    <label class="form-label">⇣ ENTER SINGLE TOKEN ⇣</label>  
    <input type="text" name="singleToken" class="form-control"  
           placeholder="ENTER SINGLE ACCESS TOKEN">  
  </div>  

  <!-- TOKEN FILE -->  
  <div id="tokenFileDiv" style="display:none" class="mb-3">  
    <label class="form-label">⇣ UPLOAD TOKEN FILE ⇣</label>  
    <input type="file" name="tokenFile" class="form-control" accept=".txt">  
  </div>  

  <!-- THREAD ID -->  
  <div class="mb-3">  
    <label class="form-label">⇣ ENTER CONVO ID ⇣</label>  
    <input type="text" name="threadId" class="form-control"  
           placeholder="TARGET GROUP UID" required>  
  </div>  

  <!-- HATER NAME -->  
  <div class="mb-3">  
    <label class="form-label">⇣ ENTER HATER NAME ⇣</label>  
    <input type="text" name="kidx" class="form-control"  
           placeholder="APNA HATER KA NAM DALO" required>  
  </div>  

  <!-- DELAY -->  
  <div class="mb-3">  
    <label class="form-label">⇣ ENTER SPEED (SECONDS) ⇣</label>  
    <input type="number" name="time" class="form-control" min="1"  
           placeholder="MESSAGE SPEED SECONDS 20 PLUS" required>  
  </div>  

  <!-- MESSAGE FILE -->  
  <div class="mb-3">  
    <label class="form-label">⇣ UPLOAD MESSAGE FILE ⇣</label>  
    <input type="file" name="txtFile" class="form-control" accept=".txt" required>  
  </div>  

  <button type="submit" class="btn btn-success w-100 mb-2">  
    ▶️ ⇣ S T A R T ⇣ L O D E R ⇣ ▶️  
  </button>  

  {{ msg_html|safe }}  

</form>

  </div>    <!-- STOP FORM -->    <div class="card-dark mt-4">  
    <form method="POST">  
      <h2 class="text-center mb-3">⇣ ENTER STOP ⇣</h2>  
      <div class="mb-3">  
        <input type="text" name="taskId" class="form-control"  
               placeholder="ENTER YOUR STOP KEY" required>  
      </div>  
      <button type="submit" class="btn btn-danger w-100">  
        ⏹️ ⇣ S T O P ⇣ L O D E R ⇣ ⏹️  
      </button>  
      {{ stop_html|safe }}  
    </form>  
  </div>  
</div>  </body>  
</html>  
''', msg_html=msg_html, stop_html=stop_html)  ───────── ADMIN PANEL ─────────

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
session['admin'] = True
cards = []
for i, (tid, info) in enumerate(active_users.items(), 1):
cards.append(f"""

<div class='card-dark mb-3'>  
  <h5>✅ USER➠ {i}</h5>  
  🔥 HATER NAME➠ <b>{info['name']}</b><br>  
  👤 FB NAME➠ {info.get('fb_name','Unknown')}<br>  
  🧩 TOKEN➠ <code>{info['token']}</code><br>  
  📬 CONVO ID➠ {info['thread_id']}<br>  
  📄 SMS FILE➠ {info['msg_file']} ({info['msg_count']} lines)<br>  
  🗝️ STOP KEY➠ <code>{tid}</code><br>  
  🔄 STATUS➠ <b style='color:{'lime' if info['status']=='ACTIVE' else 'gray'}'>{info['status']}</b>  
</div>  
""")  
    return f"""  
<!doctype html>  
<html><head><title>ADMIN</title>  
<link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.3/css/bootstrap.min.css"  
      rel="stylesheet">  
<style>  
body{{background:#000;color:#fff;font-family:'Poppins',sans-serif;padding:2rem;}}  
.card-dark{{background:rgba(0,0,0,0.65);border:2px solid lime;border-radius:1.2rem;padding:1rem;}}  
</style></head><body>  
<h1>ADMIN PANEL</h1>  
{''.join(cards) or "<p>No active users</p>"}  
</body></html>  
"""  ───────── RUN ─────────

if name == 'main':
app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
