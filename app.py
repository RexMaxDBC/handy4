import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import streamlit.components.v1 as components

# --- KI SETUP (NEU: Eigenes Modell laden) ---
@st.cache_resource
def load_custom_model():
    # Pfad zu deinem entpackten SavedModel Ordner
    model_path = "converted_savedmodel/model.savedmodel"
    return tf.saved_model.load(model_path)

# Wir laden die Labels aus deiner labels.txt
labels = ["Ohne Handy", "Mit Handy"] 

custom_model = load_custom_model()

def predict(image, model):
    # Bildvorbereitung für Teachable Machine Modelle (224x224)
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image)
    
    # Normalisierung (falls dein Modell dies erwartet, meist 0-1 oder -1 bis 1)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1
    
    # Modell-Input vorbereiten (Batch-Dimension hinzufügen)
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    
    # Vorhersage treffen
    infer = model.signatures["serving_default"]
    prediction = infer(tf.constant(data))
    
    # Das Ergebnis extrahieren (die erste Ausgabe des Modells)
    output_key = list(prediction.keys())[0]
    probs = prediction[output_key].numpy()[0]
    
    # Index mit der höchsten Wahrscheinlichkeit finden
    return np.argmax(probs), np.max(probs)

# --- INITIALISIERUNG (Gleichbleibend) ---
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

st.set_page_config(page_title="Handy-Wächter (Eigene KI)", layout="centered")

# --- CSS (Gleichbleibend) ---
st.markdown(f"""
<style>
    .stApp {{ background-color: {st.session_state.bg_color}; transition: background-color 0.3s ease; }}
    .header-container {{ border: 2px solid #D3D3D3; border-radius: 12px; background-color: rgba(211, 211, 211, 0.15); display: flex; justify-content: center; align-items: center; margin: 0 auto 40px auto; padding: 0 40px; min-width: 320px; height: 85px; }}
    .title-text {{ color: white !important; font-weight: bold !important; font-size: 2.2rem !important; margin: 0 !important; }}
    .active-task-box {{ background: rgba(255, 255, 255, 0.2); border: 2px solid #D3D3D3; border-radius: 10px; padding: 15px; margin-bottom: 10px; color: white; }}
    .timer-text {{ text-align: center; font-size: 120px; color: white; font-weight: bold; margin: 10px 0; }}
    [data-testid="stExpander"] button {{ height: 38px !important; margin-top: 28px !important; }}
    div.stMainBlockContainer > div:nth-child(7) button {{ background-color: white !important; color: {st.session_state.bg_color} !important; font-size: 24px !important; height: 60px !important; width: 200px !important; margin: 20px auto !important; display: block !important; border: none !important; box-shadow: 0px 5px 0px rgba(0,0,0,0.2); }}
    .fixed-bottom {{ position: fixed; bottom: 0; left: 0; width: 100%; background-color: rgba(255, 255, 255, 0.95); padding: 15px; z-index: 1000; }}
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown("<div class='header-container'><h1 class='title-text'>Handy-Wächter Pro</h1></div>", unsafe_allow_html=True)

# --- MODUS WAHL ---
m_col1, m_col2, m_col3 = st.columns([1, 1, 1])
with m_col1:
    if st.button("Pomodoro", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Pomodoro", 25*60, "#2d5a27"
        st.session_state.active = False
with m_col2:
    if st.button("Kurze Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Short Break", 5*60, "#457b9d"
        st.session_state.active = False
with m_col3:
    if st.button("Lange Pause", use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = "Long Break", 15*60, "#457b9d"
        st.session_state.active = False

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        if st.session_state.mode == "Pomodoro" and st.session_state.selected_task:
            st.session_state.tasks[st.session_state.selected_task]["done"] += 1
            st.balloons()
        st.rerun()

mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    if st.button("STOP" if st.session_state.active else "START", use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()

# --- TASK DASHBOARD (Gleichbleibend) ---
st.markdown("<hr style='opacity: 0.1'>", unsafe_allow_html=True)
if st.session_state.selected_task:
    if st.button("❌ Auswahl aufheben"):
        st.session_state.selected_task = None
        st.rerun()
else:
    st.markdown("<div style='text-align: center; color: white; opacity: 0.8; margin-bottom: 10px;'>✨ Freies Lernen aktiv</div>", unsafe_allow_html=True)

with st.expander("📝 Neues Lern-Fach anlegen"):
    c1, c2, c3 = st.columns([3, 1, 1]) 
    name = c1.text_input("Name", key="add_name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    with c3:
        if st.button("Speichern", use_container_width=True):
            if name: st.session_state.tasks[name] = {"done": 0, "target": target}; st.rerun()

# --- KI & KAMERA (NEU: Mit eigener KI Vorhersage) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_file = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_file:
            img = Image.open(img_file)
            # Eigene KI Vorhersage
            class_idx, confidence = predict(img, custom_model)
            
            # Klasse 1 ist "Mit Handy"
            handy_erkannt = (class_idx == 1 and confidence > 0.7)
            
            st.session_state.bg_color = "#ba4949" if handy_erkannt else "#2d5a27"
            st.write(f"Status: {labels[class_idx]} ({confidence:.1%})")
            st.image(img if not handy_erkannt else ImageOps.colorize(img.convert("L"), "red", "white"), width=120)
            
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
