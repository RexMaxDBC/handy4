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
        # Lädt die .h5 Datei direkt aus dem Hauptverzeichnis deiner GitHub-Repo
        return tf.keras.models.load_model("keras_model.h5", compile=False)
    except Exception as e:
        st.error(f"Fehler: 'keras_model.h5' konnte nicht geladen werden. {e}")
        return None

model = load_my_model()

def predict(image):
    if model is None:
        return 0, 0.0
    
    # Bildvorbereitung (Teachable Machine Standard)
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    image_array = np.asarray(image).astype(np.float32)
    
    # Normalisierung: Umwandlung der Pixelwerte (0-255) in den Bereich (-1 bis 1)
    normalized_image_array = (image_array / 127.5) - 1
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array
    
    # Vorhersage treffen
    prediction = model.predict(data, verbose=0)
    index = np.argmax(prediction)
    confidence_score = prediction[0][index]
    return index, confidence_score

# --- INITIALISIERUNG ---
if "active" not in st.session_state:
    st.session_state.active = False
if "remaining_sec" not in st.session_state:
    st.session_state.remaining_sec = 25 * 60
if "bg_color" not in st.session_state:
    st.session_state.bg_color = "#2d5a27" 
if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0

st.set_page_config(page_title="Handy Wächter Pro", layout="centered")

# --- CSS ---
st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        transition: background-color 0.5s ease;
    }}
    .timer-text {{
        text-align: center; 
        font-size: 100px; 
        color: white; 
        font-weight: bold;
        margin-bottom: 20px;
    }}
    .fixed-bottom {{
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: white;
        padding: 10px;
        z-index: 1000;
        border-top: 2px solid #ccc;
    }}
</style>
""", unsafe_allow_html=True)

st.title("Handy-Wächter (Eigene KI)")

# --- TIMER ANZEIGE ---
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

# Start/Stop Button
if st.button("TIMER START / STOP", use_container_width=True):
    st.session_state.active = not st.session_state.active
    st.session_state.last_tick = time.time()

# Timer Logik
if st.session_state.active:
    now = time.time()
    st.session_state.remaining_sec -= (now - st.session_state.last_tick)
    st.session_state.last_tick = now
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.balloons()
        st.rerun()

# --- KAMERA & KI SCANNER ---
if st.session_state.active:
    # JavaScript Trigger für automatisches Foto alle 5 Sekunden
    components.html("<script>setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 5000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    
    with c1:
        img_file = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    
    with c2:
        if img_file:
            img = Image.open(img_file)
            class_idx, confidence = predict(img)
            
            # Klasse 1 ist "Mit Handy"
            if class_idx == 1 and confidence > 0.7:
                st.session_state.bg_color = "#ba4949" # Rot
                st.error(f"HANDY! ({confidence:.0%})")
            else:
                st.session_state.bg_color = "#2d5a27" # Grün
                st.success(f"OK ({confidence:.0%})")
            
            st.session_state.cam_key += 1
            time.sleep(0.5)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
