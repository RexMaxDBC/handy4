import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import os
import base64
import io
import streamlit.components.v1 as components

st.set_page_config(page_title="Pomodoro Wächter Pro", layout="centered")

# --- KI SETUP ---
@st.cache_resource
def load_my_model():
    return tf.keras.models.load_model("keras_model.h5", compile=False)

def load_labels():
    if os.path.exists("labels.txt"):
        with open("labels.txt", "r") as f:
            return [line.strip() for line in f.readlines()]
    return ["Klasse 0", "Klasse 1"]

try:
    model = load_my_model()
    labels = load_labels()
    model_loaded = True
except Exception as e:
    st.error(f"Modell konnte nicht geladen werden: {e}")
    model_loaded = False

# --- ALARM SOUND LADEN ---
alarm_b64 = ""
if os.path.exists("batle-alarm-star-wars.mp3"):
    with open("batle-alarm-star-wars.mp3", "rb") as f:
        alarm_b64 = base64.b64encode(f.read()).decode()

# --- SESSION STATE ---
defaults = {
    "active": False,
    "remaining_sec": 25 * 60,
    "mode": "Pomodoro",
    "last_tick": time.time(),
    "bg_color": "#2d5a27",
    "tasks": {},
    "selected_task": None,
    "alarm_playing": False,
    "handy_detected": False,
    "img_data": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- BILD VERARBEITEN ---
def analyze_image(img_b64: str):
    try:
        img_data = base64.b64decode(img_b64.split(",")[-1])
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img = ImageOps.fit(img, (224, 224), Image.Resampling.LANCZOS)
        arr = np.asarray(img, dtype=np.float32) / 127.5 - 1
        data = np.expand_dims(arr, axis=0)
        pred = model.predict(data, verbose=0)
        idx = np.argmax(pred)
        return labels[idx].lower(), float(pred[0][idx])
    except Exception:
        return "fehler", 0.0

# --- CSS ---
st.markdown(f"""
<style>
    .stApp {{ background-color: {st.session_state.bg_color}; transition: background-color 0.5s ease; }}
    .header-container {{
        border: 2px solid #D3D3D3; border-radius: 12px;
        background-color: rgba(211,211,211,0.15);
        display: flex; justify-content: center; padding: 15px; margin-bottom: 30px;
    }}
    .title-text {{ color: white; font-weight: bold; font-size: 2.2rem; margin: 0; }}
    .timer-text {{ text-align: center; font-size: 110px; color: white; font-weight: bold; margin: 10px 0; }}
    .active-task-box {{
        background: rgba(255,255,255,0.2); border: 2px solid white;
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: white;
    }}
    .inactive-task-box {{
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: rgba(255,255,255,0.7);
    }}
    .alarm-banner {{
        background-color: #ba4949; color: white; text-align: center;
        font-size: 1.4rem; font-weight: bold; padding: 10px;
        border-radius: 8px; margin-bottom: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# --- UI ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>",
            unsafe_allow_html=True)

if st.session_state.handy_detected and st.session_state.active:
    st.markdown("<div class='alarm-banner'>📱 HANDY ERKANNT – FOKUS VERLOREN!</div>",
                unsafe_allow_html=True)

# --- MODUS AUSWAHL ---
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.update(mode="Pomodoro", remaining_sec=25*60,
                                bg_color="#2d5a27", active=False,
                                alarm_playing=False, handy_detected=False)
        st.rerun()
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.update(mode="Pause", remaining_sec=5*60,
                                bg_color="#457b9d", active=False,
                                alarm_playing=False, handy_detected=False)
        st.rerun()
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.update(mode="Lange Pause", remaining_sec=15*60,
                                bg_color="#457b9d", active=False,
                                alarm_playing=False, handy_detected=False)
        st.rerun()

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= now - st.session_state.last_tick
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.update(active=False, alarm_playing=False,
                                handy_detected=False, bg_color="#2d5a27")
        if st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task]["done"] += 1
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.6, 1, 0.6])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        if not st.session_state.active:
            fallback = "#2d5a27" if st.session_state.mode == "Pomodoro" else "#457b9d"
            st.session_state.update(alarm_playing=False, handy_detected=False, bg_color=fallback)
        st.rerun()

# --- TASK DASHBOARD ---
st.markdown("<hr style='opacity: 0.2'>", unsafe_allow_html=True)
if st.session_state.selected_task:
    if st.button("❌ Auswahl aufheben"):
        st.session_state.selected_task = None
        st.rerun()

with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Fach Name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Hinzufügen"):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            st.rerun()

if st.session_state.tasks:
    for t_name, t_data in list(st.session_state.tasks.items()):
        is_active = (st.session_state.selected_task == t_name)
        css = "active-task-box" if is_active else "inactive-task-box"
        st.markdown(
            f"<div class='{css}'><b>{t_name}</b> | Erledigt: {t_data['done']}/{t_data['target']}</div>",
            unsafe_allow_html=True)
        b1, b2, _ = st.columns([0.2, 0.2, 0.6])
        if not is_active:
            if b1.button("Start", key=f"s_{t_name}"):
                st.session_state.selected_task = t_name
                st.rerun()
        if b2.button("Löschen", key=f"d_{t_name}"):
            del st.session_state.tasks[t_name]
            if st.session_state.selected_task == t_name:
                st.session_state.selected_task = None
            st.rerun()

# -----------------------------------------------------------------------
# KI SCANNER – vollständig browserbasiert
#
# Architektur:
#   Browser                          Python (Streamlit)
#   ──────────────────               ──────────────────────
#   <video> live stream              analyze_image()
#   setInterval alle 5s              → label + score
#   canvas.toDataURL()               → session_state aktualisieren
#   → hidden <input> schreiben       → st.rerun()
#   → React input event feuern
#
# Kein st.camera_input → kein Aufhängen möglich.
# Der Browser-Stream läuft vollständig unabhängig von Streamlit-Reruns.
# -----------------------------------------------------------------------

scanner_active = st.session_state.active and st.session_state.mode == "Pomodoro" and model_loaded

# Unsichtbares Text-Input als Datenkanal Browser → Python
img_input = st.text_input("__img__", key="img_data", label_visibility="collapsed")

if scanner_active:
    alarm_src = f"data:audio/mp3;base64,{alarm_b64}" if alarm_b64 else ""
    status_text = "📱 HANDY ERKANNT!" if st.session_state.handy_detected else "✅ FOKUS AKTIV"
    status_color = "#ba4949" if st.session_state.handy_detected else "#2d5a27"
    alarm_should_play = str(st.session_state.alarm_playing).lower()

    components.html(f"""
    <style>
      #cam-wrap {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #fff; border-top: 2px solid #ddd;
        padding: 10px 20px; z-index: 9999;
        display: flex; align-items: center; gap: 16px;
        box-sizing: border-box;
      }}
      #cam-video {{
        width: 200px; height: 150px; border-radius: 8px;
        object-fit: cover; background: #000; flex-shrink: 0;
      }}
      #cam-canvas {{ display: none; }}
      #cam-status {{
        flex: 1; font-size: 1.2rem; font-weight: bold;
        color: {status_color}; text-align: center;
      }}
      #cam-counter {{
        font-size: 0.85rem; color: #888; text-align: center; margin-top: 4px;
      }}
    </style>

    <div id="cam-wrap">
      <video id="cam-video" autoplay playsinline muted></video>
      <canvas id="cam-canvas" width="224" height="224"></canvas>
      <div>
        <div id="cam-status">{status_text}</div>
        <div id="cam-counter">Nächster Scan in <span id="cnt">5</span>s</div>
      </div>
    </div>

    <audio id="pomo-alarm" loop src="{alarm_src}"></audio>

    <script>
    (function() {{
      var video  = document.getElementById('cam-video');
      var canvas = document.getElementById('cam-canvas');
      var ctx    = canvas.getContext('2d');
      var status = document.getElementById('cam-status');
      var cnt    = document.getElementById('cnt');
      var alarm  = document.getElementById('pomo-alarm');

      // Alarm-Zustand aus Python-Render übernehmen
      if ({alarm_should_play} && alarm.src) {{
        alarm.play().catch(function(){{}});
      }} else {{
        alarm.pause();
        alarm.currentTime = 0;
      }}

      // Countdown-Anzeige
      var countdown = 5;
      setInterval(function() {{
        countdown--;
        if (countdown < 0) countdown = 5;
        if (cnt) cnt.textContent = countdown;
      }}, 1000);

      // Streamlit hidden input finden
      // Wir suchen das Input mit data-testid und unserem key
      function findInput() {{
        var all = window.parent.document.querySelectorAll('input[type="text"]');
        for (var i = 0; i < all.length; i++) {{
          if (all[i].value === '' || all[i].getAttribute('data-pomocam') === '1') {{
            all[i].setAttribute('data-pomocam', '1');
            return all[i];
          }}
        }}
        return null;
      }}

      function pushToStreamlit(b64) {{
        var inp = findInput();
        if (!inp) return;
        var setter = Object.getOwnPropertyDescriptor(
          window.HTMLInputElement.prototype, 'value').set;
        setter.call(inp, b64);
        inp.dispatchEvent(new Event('input', {{bubbles: true}}));
      }}

      // Kamera starten
      navigator.mediaDevices.getUserMedia({{video: {{facingMode: 'user'}}, audio: false}})
        .then(function(stream) {{
          video.srcObject = stream;

          // Scan-Interval: alle 5 Sekunden
          setInterval(function() {{
            // Nur scannen wenn Video wirklich läuft
            if (video.readyState < 2) return;
            ctx.drawImage(video, 0, 0, 224, 224);
            var b64 = canvas.toDataURL('image/jpeg', 0.8);
            pushToStreamlit(b64);
            countdown = 5;
            if (status) {{
              status.style.color = '#888';
              status.textContent = '🔍 Analysiere…';
            }}
          }}, 5000);
        }})
        .catch(function(err) {{
          if (status) {{
            status.style.color = '#ba4949';
            status.textContent = '❌ Kamera: ' + err.message;
          }}
        }});
    }})();
    </script>
    """, height=185)

    # Bild analysieren wenn angekommen
    if img_input and img_input.startswith("data:image"):
        lbl, score = analyze_image(img_input)

        if "handy" in lbl and score > 0.7:
            st.session_state.handy_detected = True
            st.session_state.alarm_playing = True
            st.session_state.bg_color = "#ba4949"
        else:
            st.session_state.handy_detected = False
            st.session_state.alarm_playing = False
            st.session_state.bg_color = "#2d5a27"

        st.session_state.img_data = ""
        st.rerun()

else:
    # Alarm stoppen wenn Scanner inaktiv
    st.session_state.alarm_playing = False
    st.session_state.handy_detected = False
    components.html("""
    <script>
      var a = window.parent.document.getElementById('pomo-alarm');
      if (a) {{ a.pause(); a.currentTime = 0; }}
    </script>
    """, height=0)

# Timer-Rerun (kein sleep nötig für Kamera, nur für Timer-Anzeige)
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()    "cam_key": 0,
    "bg_color": "#2d5a27",
    "tasks": {},
    "selected_task": None,
    "alarm_playing": False,   # NEU: Alarm-Status wird explizit getrackt
    "handy_detected": False,  # NEU: Erkennungsstatus getrennt speichern
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- ALARM FUNKTIONEN ---
# Kernidee: Der Alarm-Status wird in session_state gespeichert.
# Das Audio-HTML wird bei JEDEM Rerun neu gerendert basierend auf dem Status.
# So kann der Alarm auch gestoppt werden, wenn der Kamera-Zyklus aussetzt.

def render_alarm_controller():
    """
    Wird bei jedem Rerun aufgerufen.
    Spielt Alarm ab oder stoppt ihn, je nach session_state.alarm_playing.
    Kein Aufhängen mehr, weil dieser Block IMMER ausgeführt wird.
    """
    if st.session_state.alarm_playing:
        if os.path.exists("batle-alarm-star-wars.mp3"):
            with open("batle-alarm-star-wars.mp3", "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            # Prüft ob Audio bereits läuft, bevor neu gestartet wird
            components.html(f"""
                <script>
                (function() {{
                    var existing = window.parent.document.getElementById('pomo_alarm');
                    if (!existing) {{
                        var audio = document.createElement('audio');
                        audio.id = 'pomo_alarm';
                        audio.loop = true;
                        audio.src = 'data:audio/mp3;base64,{b64}';
                        window.parent.document.body.appendChild(audio);
                        audio.play().catch(e => console.log('Autoplay blocked:', e));
                    }}
                }})();
                </script>
            """, height=0)
    else:
        # Alarm stoppen - läuft immer, auch wenn Kamera hängt
        components.html("""
            <script>
            (function() {
                var audio = window.parent.document.getElementById('pomo_alarm');
                if (audio) {
                    audio.pause();
                    audio.currentTime = 0;
                    audio.remove();
                }
                // Auch den Kamera-Interval stoppen falls aktiv
                if (window.parent.pomo_cam_interval) {
                    clearInterval(window.parent.pomo_cam_interval);
                    window.parent.pomo_cam_interval = null;
                }
            })();
            </script>
        """, height=0)

def start_cam_interval():
    """Startet den automatischen Kamera-Klick-Interval (sauber, ohne Doppel-Interval)."""
    components.html("""
        <script>
        (function() {
            // Alten Interval immer erst clearen
            if (window.parent.pomo_cam_interval) {
                clearInterval(window.parent.pomo_cam_interval);
            }
            window.parent.pomo_cam_interval = setInterval(function() {
                var btns = Array.from(window.parent.document.querySelectorAll('button'));
                var camBtn = btns.find(function(b) { return b.innerText.includes('Photo'); });
                if (camBtn) camBtn.click();
            }, 5000);
        })();
        </script>
    """, height=0)

def stop_cam_interval():
    components.html("""
        <script>
        if (window.parent.pomo_cam_interval) {
            clearInterval(window.parent.pomo_cam_interval);
            window.parent.pomo_cam_interval = null;
        }
        </script>
    """, height=0)

# --- CSS ---
st.markdown(f"""
<style>
    .stApp {{ background-color: {st.session_state.bg_color}; transition: background-color 0.5s ease; }}
    .header-container {{
        border: 2px solid #D3D3D3; border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex; justify-content: center; padding: 15px; margin-bottom: 30px;
    }}
    .title-text {{ color: white; font-weight: bold; font-size: 2.2rem; margin: 0; }}
    .timer-text {{ text-align: center; font-size: 110px; color: white; font-weight: bold; margin: 10px 0; }}
    .active-task-box {{
        background: rgba(255,255,255,0.2); border: 2px solid white;
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: white;
    }}
    .inactive-task-box {{
        background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2);
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: rgba(255,255,255,0.7);
    }}
    .fixed-bottom {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: white; padding: 15px; z-index: 1000; border-top: 1px solid #ddd;
    }}
    .alarm-banner {{
        background-color: #ba4949; color: white; text-align: center;
        font-size: 1.4rem; font-weight: bold; padding: 10px;
        border-radius: 8px; margin-bottom: 10px; animation: pulse 1s infinite;
    }}
    @keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.7; }} }}
</style>
""", unsafe_allow_html=True)

# --- ALARM CONTROLLER (bei JEDEM Rerun ausführen!) ---
# Das ist der Kern-Fix: Alarm-Steuerung läuft unabhängig vom Kamera-Zyklus
render_alarm_controller()

# --- UI ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>", unsafe_allow_html=True)

# Alarm-Banner anzeigen wenn Handy erkannt
if st.session_state.handy_detected and st.session_state.active:
    st.markdown("<div class='alarm-banner'>📱 HANDY ERKANNT – FOKUS VERLOREN!</div>", unsafe_allow_html=True)

# MODUS AUSWAHL
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.bg_color = "#2d5a27"
        st.session_state.active = False
        st.session_state.alarm_playing = False
        st.session_state.handy_detected = False
        st.rerun()
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode = "Pause"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.bg_color = "#457b9d"
        st.session_state.active = False
        st.session_state.alarm_playing = False
        st.session_state.handy_detected = False
        st.rerun()
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode = "Lange Pause"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.bg_color = "#457b9d"
        st.session_state.active = False
        st.session_state.alarm_playing = False
        st.session_state.handy_detected = False
        st.rerun()

# TIMER LOGIK
if st.session_state.active:
    now = time.time()
    elapsed = now - st.session_state.last_tick
    st.session_state.remaining_sec -= elapsed
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.session_state.alarm_playing = False
        st.session_state.handy_detected = False
        st.session_state.bg_color = "#2d5a27"
        if st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task]["done"] += 1
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.6, 1, 0.6])
with btn_center:
    btn_label = "STOP" if st.session_state.active else "START"
    if st.button(btn_label, use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        if not st.session_state.active:
            # Timer gestoppt: Alarm und Kamera-Interval beenden
            st.session_state.alarm_playing = False
            st.session_state.handy_detected = False
            st.session_state.bg_color = "#2d5a27" if st.session_state.mode == "Pomodoro" else "#457b9d"
            stop_cam_interval()
        st.rerun()

# --- TASK DASHBOARD ---
st.markdown("<hr style='opacity: 0.2'>", unsafe_allow_html=True)
if st.session_state.selected_task:
    if st.button("❌ Auswahl aufheben"):
        st.session_state.selected_task = None
        st.rerun()

with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Fach Name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Hinzufügen"):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            st.rerun()

if st.session_state.tasks:
    for t_name, t_data in list(st.session_state.tasks.items()):
        is_active = (st.session_state.selected_task == t_name)
        css = "active-task-box" if is_active else "inactive-task-box"
        st.markdown(
            f"<div class='{css}'><b>{t_name}</b> | Erledigt: {t_data['done']}/{t_data['target']}</div>",
            unsafe_allow_html=True
        )
        b1, b2, _ = st.columns([0.2, 0.2, 0.6])
        if not is_active:
            if b1.button("Start", key=f"s_{t_name}"):
                st.session_state.selected_task = t_name
                st.rerun()
        if b2.button("Löschen", key=f"d_{t_name}"):
            del st.session_state.tasks[t_name]
            if st.session_state.selected_task == t_name:
                st.session_state.selected_task = None
            st.rerun()

# --- KI SCANNER ---
if st.session_state.active and st.session_state.mode == "Pomodoro" and model_loaded:
    # Kamera-Interval starten (wird sauber neugestartet bei jedem Rerun)
    start_cam_interval()

    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_f = st.camera_input(
            "Scanner",
            key=f"c_{st.session_state.cam_key}",
            label_visibility="collapsed"
        )
    with c2:
        if img_f is not None:
            try:
                # Bildvorbereitung
                img = Image.open(img_f).convert("RGB")
                img = ImageOps.fit(img, (224, 224), Image.Resampling.LANCZOS)
                img_array = np.asarray(img, dtype=np.float32) / 127.5 - 1
                data = np.expand_dims(img_array, axis=0)

                # Vorhersage
                prediction = model.predict(data, verbose=0)
                index = np.argmax(prediction)
                label = labels[index].lower()
                score = float(prediction[0][index])

                # Handy-Erkennung
                if "handy" in label and score > 0.7:
                    st.session_state.handy_detected = True
                    st.session_state.alarm_playing = True
                    st.session_state.bg_color = "#ba4949"
                    st.error(f"📱 HANDY ERKANNT! ({score:.0%})")
                else:
                    st.session_state.handy_detected = False
                    st.session_state.alarm_playing = False
                    st.session_state.bg_color = "#2d5a27"
                    st.success(f"✅ FOKUS AKTIV ({score:.0%})")

            except Exception as e:
                st.warning(f"Scan-Fehler: {e}")
                # Bei Fehler: Alarm sicherheitshalber stoppen
                st.session_state.alarm_playing = False
                st.session_state.handy_detected = False

            # Kamera zurücksetzen für nächsten Scan
            st.session_state.cam_key += 1
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# Timer-Rerun (kein sleep mehr!)
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
