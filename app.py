import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import os
import base64
import streamlit.components.v1 as components

# --- KI SETUP (Dein selbsttrainiertes Modell) ---
@st.cache_resource
def load_my_model():
    # Lädt dein Teachable Machine / Keras Modell
    return tf.keras.models.load_model("keras_model.h5", compile=False)

def load_labels():
    if os.path.exists("labels.txt"):
        with open("labels.txt", "r") as f:
            return [line.strip() for line in f.readlines()]
    return ["Klasse 0", "Klasse 1"]

model = load_my_model()
labels = load_labels()

# --- INITIALISIERUNG ---
if "active" not in st.session_state:
    st.session_state.active = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "mode" not in st.session_state:
    st.session_state.mode = "Pomodoro"
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0
if "bg_color" not in st.session_state:
    st.session_state.bg_color = "#2d5a27" 
if "tasks" not in st.session_state:
    st.session_state.tasks = {} 
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Wächter Pro", layout="centered")

# --- SOUND FUNKTIONEN ---
def play_alarm():
    if os.path.exists("batle-alarm-star-wars.mp3"):
        with open("batle-alarm-star-wars.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            audio_html = f"""
                <audio id="alarm_sound" autoplay="true" loop="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = window.parent.document.getElementById("alarm_sound");
                    if (audio) {{ audio.play().catch(e => console.log(e)); }}
                </script>
                """
            st.markdown(audio_html, unsafe_allow_html=True)

def stop_alarm():
    stop_js = """
        <script>
        var audio = window.parent.document.getElementById("alarm_sound");
        if (audio) { audio.pause(); audio.currentTime = 0; audio.remove(); }
        </script>
        """
    components.html(stop_js, height=0)

# --- CSS DESIGN (Vom funktionierenden Code übernommen) ---
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
        background: rgba(255, 255, 255, 0.2); border: 2px solid white;
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: white;
    }}
    .inactive-task-box {{
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px; padding: 15px; margin-bottom: 10px; color: rgba(255, 255, 255, 0.7);
    }}
    .fixed-bottom {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: white; padding: 15px; z-index: 1000; border-top: 1px solid #ddd;
    }}
</style>
""", unsafe_allow_html=True)

# --- UI ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>", unsafe_allow_html=True)

# MODUS AUSWAHL
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pause", 5*60, "#457b9d"
        st.session_state.active = False
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Lange Pause", 15*60, "#457b9d"
        st.session_state.active = False

# TIMER LOGIK
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
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
        if not st.session_state.active: stop_alarm()
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
        st.markdown(f"<div class='{css}'><b>{t_name}</b> | Erledigt: {t_data['done']}/{t_data['target']}</div>", unsafe_allow_html=True)
        
        b1, b2, _ = st.columns([0.2, 0.2, 0.6])
        if not is_active:
            if b1.button("Start", key=f"s_{t_name}"):
                st.session_state.selected_task = t_name
                st.rerun()
        if b2.button("Löschen", key=f"d_{t_name}"):
            del st.session_state.tasks[t_name]
            if st.session_state.selected_task == t_name: st.session_state.selected_task = None
            st.rerun()

# --- KI SCANNER (ST-LOGIK IN VT-STRUKTUR) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>if(!window.parent.pI) window.parent.pI = setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_f = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_f:
            # Bildvorbereitung für Keras Modell
            img = Image.open(img_f).convert("RGB")
            img = ImageOps.fit(img, (224, 224), Image.Resampling.LANCZOS)
            img_array = np.asarray(img).astype(np.float32) / 127.5 - 1
            data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
            data[0] = img_array
            
            # Prediction
            prediction = model.predict(data, verbose=0)
            index = np.argmax(prediction)
            label = labels[index].lower()
            score = prediction[0][index]
            
            # Handy-Logik (Prüft ob 'handy' im Label steht)
            if "handy" in label and score > 0.7:
                st.session_state.bg_color = "#ba4949"
                play_alarm()
                st.error("HANDY ERKANNT!")
            else:
                st.session_state.bg_color = "#2d5a27"
                stop_alarm()
                st.success("FOKUS AKTIV")
            
            # Reset der Kamera für den nächsten Scan
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
