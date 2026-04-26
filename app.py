import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import os
import streamlit.components.v1 as components

# --- INITIALISIERUNG ---
if "active" not in st.session_state:
    st.session_state.active = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "mode" not in st.session_state:
    st.session_state.mode = "Pomodoro"
if "bg_color" not in st.session_state:
    st.session_state.bg_color = "#2d5a27"
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0
if "tasks" not in st.session_state:
    st.session_state.tasks = {}
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

st.set_page_config(page_title="Handy-Wächter", layout="centered")

# --- KI SETUP ---
@st.cache_resource
def load_my_model():
    try:
        if os.path.exists("keras_model.h5"):
            return tf.keras.models.load_model("keras_model.h5", compile=False)
        return None
    except:
        return None

model = load_my_model()

def predict(image):
    if model is None:
        return 0, 0.0
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)
    normalized_image_array = (image_array / 127.5) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    prediction = model.predict(data, verbose=0)
    index = np.argmax(prediction)
    confidence = prediction[0][index]
    return index, confidence

# --- CSS (Originalgetreu) ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.4s ease;
    }}
    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        padding: 10px;
        margin-bottom: 30px;
    }}
    .title-text {{
        color: white;
        font-weight: bold;
        font-size: 2.2rem;
        margin: 0;
    }}
    .timer-text {{
        text-align: center;
        font-size: 110px;
        color: white;
        font-weight: bold;
        margin: 10px 0;
    }}
    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 10px;
        z-index: 1000;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='header-container'><h1 class='title-text'>Handy-Wächter</h1></div>", unsafe_allow_html=True)

# --- MODUS ---
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
        st.rerun()
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pause", 5*60, "#457b9d"
        st.session_state.active = False
        st.rerun()
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Lange Pause", 15*60, "#457b9d"
        st.session_state.active = False
        st.rerun()

# --- TIMER ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.6, 1, 0.6])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        st.rerun()

# --- TASKS ---
with st.expander("📝 Aufgaben"):
    c1, c2 = st.columns([3, 1])
    name = c1.text_input("Neues Fach")
    if c2.button("Add") and name:
        st.session_state.tasks[name] = {"done": 0, "target": 4}
        st.rerun()
    for t_name, t_data in st.session_state.tasks.items():
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(t_name)
        col2.write(f"{t_data['done']}/4")
        if col3.button("+1", key=t_name):
            st.session_state.tasks[t_name]["done"] += 1
            st.rerun()

# --- SCANNER (Die schnelle Version) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    # Automatischer Klick alle 5 Sek
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Check", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            idx, conf = predict(img)
            # Wir nutzen 0.85 als Sicherheitsschwelle
            if idx == 1 and conf > 0.85:
                st.session_state.bg_color = "#ba4949"
                st.error("HANDY!")
            else:
                st.session_state.bg_color = "#2d5a27"
                st.success("OK")
            st.session_state.cam_key += 1
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()model = load_my_model()

def predict(image):
    if model is None:
        return 0, 0.0
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)
    normalized_image_array = (image_array / 127.5) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    prediction = model.predict(data, verbose=0)
    index = np.argmax(prediction)
    confidence = prediction[0][index]
    return index, confidence

# --- CSS DESIGN ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.8s ease;
    }}
    .header-container {{
        border: 2px solid #D3D3D3;
        border-radius: 12px;
        background-color: rgba(211, 211, 211, 0.15);
        display: flex;
        justify-content: center;
        padding: 10px;
        margin-bottom: 30px;
    }}
    .title-text {{
        color: white;
        font-weight: bold;
        font-size: 2.2rem;
        margin: 0;
    }}
    .timer-text {{
        text-align: center;
        font-size: 110px;
        color: white;
        font-weight: bold;
        margin: 10px 0;
        line-height: 1;
    }}
    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 15px;
        z-index: 1000;
        border-top: 1px solid #ddd;
    }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='header-container'><h1 class='title-text'>Handy-Wächter</h1></div>", unsafe_allow_html=True)

# --- MODUS AUSWAHL ---
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
        st.rerun()
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pause", 5*60, "#457b9d"
        st.session_state.active = False
        st.rerun()
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Lange Pause", 15*60, "#457b9d"
        st.session_state.active = False
        st.rerun()

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.6, 1, 0.6])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        st.rerun()

# --- TASK SYSTEM ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Fach Name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Speichern"):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            st.rerun()
    
    for t_name, t_data in st.session_state.tasks.items():
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"📚 {t_name}")
        col2.write(f"{t_data['done']}/{t_data['target']}")
        if col3.button("+1", key=t_name):
            st.session_state.tasks[t_name]["done"] += 1
            st.rerun()

# --- KI SCANNER ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    # Automatischer Foto-Trigger alle 6 Sekunden (etwas langsamer für Stabilität)
    components.html("<script>if(window.parent.photoInterval) clearInterval(window.parent.photoInterval); window.parent.photoInterval = setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 6000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        # cam_key sorgt dafür, dass das Kamera-Widget jedes Mal "frisch" geladen wird
        img_file = st.camera_input("Handy-Check", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            idx, conf = predict(img)
            
            if idx == 1 and conf > 0.85:
                st.session_state.bg_color = "#ba4949" # Rot
                st.error(f"HANDY! ({conf:.0%})")
            else:
                st.session_state.bg_color = "#2d5a27" # Grün
                st.success(f"OK ({conf:.0%})")
            
            # WICHTIG: Erst nach Verarbeitung den Key erhöhen und pausieren
            st.session_state.cam_key += 1
            time.sleep(1.5) # Dem Browser Zeit geben
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# Timer-Update im Hintergrund
if st.session_state.active:
    time.sleep(0.5)
    st.rerun()
