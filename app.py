import streamlit as st
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import time
import os

# --- INITIALISIERUNG (MUSS VOR set_page_config SEIN!) ---
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
if "last_tick" not in st.session_state:
    st.session_state.last_tick = time.time()

st.set_page_config(page_title="Pomodoro Handy-Wächter", layout="centered")

# --- KI SETUP - LADE H5 MODELL ---
@st.cache_resource
def load_my_model():
    try:
        # Prüfe ob die Datei existiert
        if os.path.exists("keras_model.h5"):
            # Lade H5 Datei (NICHT saved_model)
            model = tf.keras.models.load_model("keras_model.h5", compile=False)
            st.success("✅ KI-Modell erfolgreich geladen!")
            return model
        else:
            st.error("❌ Datei 'keras_model.h5' nicht gefunden!")
            st.info("Stelle sicher, dass die Datei im gleichen Verzeichnis wie app.py liegt")
            return None
    except Exception as e:
        st.error(f"❌ Fehler beim Laden des Modells: {e}")
        return None

# Modell laden
model = load_my_model()

# Lade Labels
def load_labels():
    try:
        if os.path.exists("labels.txt"):
            with open("labels.txt", "r") as f:
                labels = [line.strip() for line in f.readlines()]
            return labels
        else:
            return ["Ohne Handy", "Mit Handy"]
    except:
        return ["Ohne Handy", "Mit Handy"]

labels = load_labels()

def predict(image):
    if model is None:
        return 0, 0.0
    
    try:
        # Bildvorbereitung für Teachable Machine Modell
        size = (224, 224)
        image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
        image_array = np.asarray(image).astype(np.float32)
        
        # Normalisierung: Pixelwerte (0-255) auf Bereich (-1 bis 1)
        normalized_image_array = (image_array / 127.5) - 1
        data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
        data[0] = normalized_image_array
        
        # Vorhersage
        prediction = model.predict(data, verbose=0)
        index = np.argmax(prediction)
        confidence_score = prediction[0][index]
        return index, confidence_score
    except Exception as e:
        st.warning(f"Fehler bei der Vorhersage: {e}")
        return 0, 0.0

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
div.stButton > button {{
    border-radius: 8px;
}}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Handy-Wächter Pomodoro")

# --- MODUS AUSWAHL ---
m_col1, m_col2, m_col3 = st.columns(3)
with m_col1:
    if st.button("🍅 Pomodoro", use_container_width=True):
        st.session_state.mode = "Pomodoro"
        st.session_state.remaining_sec = 25 * 60
        st.session_state.bg_color = "#2d5a27"
        st.session_state.active = False
        st.rerun()

with m_col2:
    if st.button("☕ Kurze Pause", use_container_width=True):
        st.session_state.mode = "Pause"
        st.session_state.remaining_sec = 5 * 60
        st.session_state.bg_color = "#457b9d"
        st.session_state.active = False
        st.rerun()

with m_col3:
    if st.button("😴 Lange Pause", use_container_width=True):
        st.session_state.mode = "Lange Pause"
        st.session_state.remaining_sec = 15 * 60
        st.session_state.bg_color = "#457b9d"
        st.session_state.active = False
        st.rerun()

# --- TIMER LOGIK ---
if st.session_state.active:
    now = time.time()
    elapsed = now - st.session_state.last_tick
    st.session_state.remaining_sec -= elapsed
    st.session_state.last_tick = now
    
    if st.session_state.remaining_sec <= 0:
        st.session_state.active = False
        st.session_state.remaining_sec = 0
        st.balloons()
        st.success("🎉 Zeit vorbei! 🎉")
        st.rerun()

# Timer anzeigen
mins, secs = divmod(int(max(0, st.session_state.remaining_sec)), 60)
st.markdown(f"<div class='timer-text'>{mins:02d}:{secs:02d}</div>", unsafe_allow_html=True)

# Start/Stop Button
_, btn_center, _ = st.columns([0.5, 1, 0.5])
with btn_center:
    button_text = "⏸️ STOP" if st.session_state.active else "▶️ START"
    if st.button(button_text, use_container_width=True):
        st.session_state.active = not st.session_state.active
        st.session_state.last_tick = time.time()
        st.rerun()

# --- TASK SYSTEM ---
st.markdown("---")
with st.expander("📝 Lernfächer verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        name = st.text_input("Neues Fach")
    with c2:
        target = st.number_input("Ziel (Minuten)", min_value=1, value=25)
    with c3:
        if st.button("➕ Hinzufügen", use_container_width=True):
            if name and name not in st.session_state.tasks:
                st.session_state.tasks[name] = {"done": 0, "target": target}
                st.rerun()
    
    # Tasks anzeigen
    if st.session_state.tasks:
        st.write("**Aktuelle Fächer:**")
        for task_name, task_data in st.session_state.tasks.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"📚 {task_name}")
            with col2:
                if task_data["target"] > 0:
                    progress = min(task_data["done"] / task_data["target"], 1.0)
                    st.progress(progress)
                st.write(f"{task_data['done']}/{task_data['target']}")
            with col3:
                if st.button("+1", key=f"add_{task_name}"):
                    if task_data["done"] < task_data["target"]:
                        st.session_state.tasks[task_name]["done"] += 1
                        st.rerun()

# --- KI SCANNER (Nur im Pomodoro Modus) ---
if st.session_state.active and st.session_state.mode == "Pomodoro":
    st.markdown("---")
    st.subheader("📸 Handy-Scanner")
    st.caption("Das KI-Modell prüft, ob du auf dein Handy schaust")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        img_file = st.camera_input("Kamera", key=f"camera_{st.session_state.cam_key}", label_visibility="collapsed")
    
    with col2:
        if img_file and model is not None:
            img = Image.open(img_file)
            class_idx, confidence = predict(img)
            
            # Klasse 1 = "Mit Handy" (laut deiner labels.txt)
            if class_idx == 1 and confidence > 0.7:
                st.session_state.bg_color = "#ba4949"  # Rot
                st.error(f"⚠️ HANDY ERKANNT! ({confidence:.0%})")
                st.markdown("**📵 Leg bitte das Handy weg!**")
            else:
                st.session_state.bg_color = "#2d5a27"  # Grün
                st.success(f"✅ Gut gemacht! Kein Handy erkannt ({confidence:.0%})")
            
            # Zeige erkannte Klasse an
            st.write(f"Erkannt: {labels[class_idx] if class_idx < len(labels) else 'Unbekannt'}")
            
            # Kleines Vorschaubild
            st.image(img, width=100)
            
            # Nächsten Scan auslösen
            st.session_state.cam_key += 1
            time.sleep(1)
            st.rerun()
        elif img_file and model is None:
            st.error("KI-Modell nicht geladen. Kann nicht scannen.")

# Automatisches Neuladen für Timer
if st.session_state.active:
    time.sleep(0.5)
    st.rerun()
