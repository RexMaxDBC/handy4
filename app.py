import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import os
import streamlit.components.v1 as components
import base64

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

st.set_page_config(page_title="Handy-Wächter Pro", layout="wide") # 'wide' hilft, links Platz zu schaffen

# --- HINTERGRUNDBILD LADEN ---
@st.cache_data
def get_base64_of_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

bg_img_base64 = get_base64_of_image("IMG_3403.jpg")

# --- SOUND FUNKTIONEN ---
def play_alarm():
    if os.path.exists("batle-alarm-star-wars.mp3"):
        with open("batle-alarm-star-wars.mp3", "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio id="alarm_sound" autoplay loop>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)

def stop_alarm():
    stop_js = """
        <script>
        var audio = window.parent.document.getElementById("alarm_sound");
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
            audio.remove();
        }
        </script>
        """
    components.html(stop_js, height=0)

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
    if model is None: return 0, 0.0
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

# --- CSS DESIGN (Optimiert für Sichtbarkeit des Bildes) ---
bg_img_css = ""
if bg_img_base64:
    bg_img_css = f"""
        background-image: url("data:image/jpg;base64,{bg_img_base64}");
        background-repeat: no-repeat;
        background-position: left center;
        background-size: 30%; /* Bild nimmt 30% der Breite ein */
        background-attachment: fixed;
    """

st.markdown(f"""
<style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        {bg_img_css}
        transition: background-color 0.8s ease;
    }}
    /* Hauptcontainer etwas nach rechts schieben, damit links Platz für das Bild ist */
    .main .block-container {{
        max-width: 600px;
        margin-left: 35%; 
    }}
    .header-container {{
        border: 2px solid rgba(255,255,255,0.3);
        border-radius: 12px;
        background-color: rgba(255, 255, 255, 0.1);
        padding: 10px;
        margin-bottom: 20px;
        text-align: center;
    }}
    .title-text {{ color: white; font-weight: bold; font-size: 2rem; }}
    .timer-text {{
        text-align: center; font-size: 100px; color: white;
        font-weight: bold; margin: 10px 0;
    }}
    .fixed-bottom {{
        position: fixed; bottom: 0; left: 0; width: 100%;
        background-color: rgba(255,255,255,0.9); padding: 15px; z-index: 1000;
        border-top: 1px solid #ddd;
    }}
</style>
""", unsafe_allow_html=True)

# --- UI ---
st.markdown("<div class='header-container'><h1 class='title-text'>Handy-Wächter Pro</h1></div>", unsafe_allow_html=True)

cols = st.columns(3)
modes = [("Pomodoro", 25*60, "#2d5a27"), ("Pause", 5*60, "#457b9d"), ("Lange Pause", 15*60, "#457b9d")]
for i, (name, sec, color) in enumerate(modes):
    if cols[i].button(name, use_container_width=True):
        st.session_state.mode, st.session_state.remaining_sec, st.session_state.bg_color = name, sec, color
        st.session_state.active = False
        st.rerun()

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

_, btn_c, _ = st.columns([0.5, 1, 0.5])
if btn_c.button("STOP" if st.session_state.active else "START", use_container_width=True):
    st.session_state.active = not st.session_state.active
    st.session_state.last_tick = time.time()
    st.rerun()

with st.expander("📝 Aufgaben"):
    c1, c2 = st.columns([3, 1])
    n = c1.text_input("Neues Fach")
    if c2.button("Add") and n:
        st.session_state.tasks[n] = {"done": 0, "target": 4}
        st.rerun()
    for tn, td in st.session_state.tasks.items():
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(tn)
        col2.write(f"{td['done']}/4")
        if col3.button("+1", key=tn):
            st.session_state.tasks[tn]["done"] += 1
            st.rerun()

# --- KI SCANNER ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    components.html("<script>if(window.parent.pI) clearInterval(window.parent.pI); window.parent.pI = setInterval(() => { const b = Array.from(window.parent.document.querySelectorAll('button')).find(x => x.innerText.includes('Photo')); if(b) b.click(); }, 6000);</script>", height=0)
    
    st.markdown('<div class="fixed-bottom">', unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1:
        img_f = st.camera_input("Scanner", key=f"c_{st.session_state.cam_key}", label_visibility="collapsed")
    with c2:
        if img_f:
            img = Image.open(img_f)
            idx, conf = predict(img)
            if idx == 1 and conf > 0.95:
                st.session_state.bg_color = "#ba4949"
                st.error("HANDY!")
                play_alarm()
            else:
                st.session_state.bg_color = "#2d5a27"
                st.success("OK")
                stop_alarm()
            st.session_state.cam_key += 1
            time.sleep(1.2)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.active:
    time.sleep(0.5)
    st.rerun()
