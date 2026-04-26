import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import streamlit.components.v1 as components

# --- KI SETUP ---
@st.cache_resource
def load_my_model():
    try:
        # Lädt die .h5 Datei direkt aus dem Hauptverzeichnis (app.py Ebene)
        return tf.keras.models.load_model("keras_model.h5", compile=False)
    except Exception as e:
        st.error(f"Fehler: 'keras_model.h5' konnte nicht geladen werden. Hast du die Datei in GitHub hochgeladen? {e}")
        return None

model = load_my_model()

def predict(image):
    if model is None:
        return 0, 0.0
    
    # Bildvorbereitung (Standard für Teachable Machine Modelle)
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)
    
    # Normalisierung: Pixelwerte (0-255) auf Bereich (-1 bis 1) bringen
    normalized_image_array = (image_array / 127.5) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    
    # Vorhersage
    prediction = model.predict(data, verbose=0)
    index = np.argmax(prediction)
    confidence_score = prediction[0][index]
    return index, confidence_score

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
if "selected_task" not in st.session_state:
    st.session_state.selected_task = None

st.set_page_config(page_title="Pomodoro Handy-Wächter", layout="centered")

# --- CSS DESIGN ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.6s ease;
    }}
    .timer-text {{
        text-align: center; 
        font-size: 110px; 
        color: white; 
        font-weight: bold;
        margin: 20px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }}
    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px;
        z-index: 1000;
        border-top: 1px solid #ddd;
    }}
    /* Button Styling */
    div.stButton > button {{
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Handy-Wächter Pomodoro")

# --- MODUS AUSWAHL ---
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

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.session_state.remaining_sec = 0
        st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- TASK SYSTEM ---
st.markdown("---")
with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Neues Fach")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Hinzufügen", use_container_width=True):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            st.rerun()

# --- KI SCANNER (Nur im Pomodoro Modus aktiv) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    # Automatischer Foto-Trigger alle 5 Sek
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        img_file = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with col2:
        if img_file:
            img = Image.open(img_file)
            class_idx, confidence = predict(img)
            
            # Klasse 1 = Handy erkannt
            if class_idx == 1 and confidence > 0.7:
                st.session_state.bg_color = "#ba4949" # Rot
                st.error(f"HANDY GEFUNDEN! ({confidence:.0%})")
            else:
                st.session_state.bg_color = "#2d5a27" # Grün
                st.success(f"Fokussiert... ({confidence:.0%})")
            
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
