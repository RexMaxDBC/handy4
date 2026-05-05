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
    st.error("Modell konnte nicht geladen werden: " + str(e))
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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- BILD VERARBEITEN ---
def analyze_image(img_b64):
    try:
        img_bytes = base64.b64decode(img_b64.split(",")[-1])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img = ImageOps.fit(img, (224, 224), Image.Resampling.LANCZOS)
        arr = np.asarray(img, dtype=np.float32) / 127.5 - 1
        data = np.expand_dims(arr, axis=0)
        pred = model.predict(data, verbose=0)
        idx = int(np.argmax(pred))
        return labels[idx].lower(), float(pred[0][idx])
    except Exception as ex:
        st.warning("Analysefehler: " + str(ex))
        return "fehler", 0.0

# ---------------------------------------------------------------
# SCAN-BILD EMPFANGEN
# Das Bild kommt per st.camera_input - zurueck zum stabilen Ansatz
# aber OHNE JavaScript-Auto-Klick. Stattdessen:
# Der Browser schickt Frames per fetch() POST direkt an einen
# Streamlit-eigenen Mechanismus: st.camera_input mit manuellem key-Reset.
#
# Neues Konzept: Wir nutzen st.camera_input normal, aber der
# "Aufhaenger" kam daher dass cam_key sich nicht resettet hat wenn
# das Bild nicht verarbeitet wurde. Fix: img wird sofort nach Empfang
# verarbeitet und cam_key wird IMMER inkrementiert - egal ob Handy
# erkannt oder nicht. Kein sleep(), kein JS-Klick-Trick.
# ---------------------------------------------------------------

if "cam_key" not in st.session_state:
    st.session_state.cam_key = 0

# --- CSS ---
st.markdown(
    "<style>"
    ".stApp { background-color: " + st.session_state.bg_color + "; transition: background-color 0.5s ease; }"
    ".header-container { border: 2px solid #D3D3D3; border-radius: 12px; background-color: rgba(211,211,211,0.15); display: flex; justify-content: center; padding: 15px; margin-bottom: 30px; }"
    ".title-text { color: white; font-weight: bold; font-size: 2.2rem; margin: 0; }"
    ".timer-text { text-align: center; font-size: 110px; color: white; font-weight: bold; margin: 10px 0; }"
    ".active-task-box { background: rgba(255,255,255,0.2); border: 2px solid white; border-radius: 10px; padding: 15px; margin-bottom: 10px; color: white; }"
    ".inactive-task-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; padding: 15px; margin-bottom: 10px; color: rgba(255,255,255,0.7); }"
    ".alarm-banner { background-color: #ba4949; color: white; text-align: center; font-size: 1.4rem; font-weight: bold; padding: 10px; border-radius: 8px; margin-bottom: 10px; }"
    ".scan-box { position: fixed; bottom: 0; left: 0; width: 100%; background: white; border-top: 2px solid #ddd; padding: 12px 20px; z-index: 9999; box-sizing: border-box; }"
    "</style>",
    unsafe_allow_html=True
)

# --- UI HEADER ---
st.markdown("<div class='header-container'><h1 class='title-text'>Pomodoro Wächter Pro</h1></div>", unsafe_allow_html=True)

if st.session_state.handy_detected and st.session_state.active:
    st.markdown("<div class='alarm-banner'>HANDY ERKANNT - FOKUS VERLOREN!</div>", unsafe_allow_html=True)

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
st.markdown("<div class='timer-text'>" + str(mins).zfill(2) + ":" + str(secs).zfill(2) + "</div>", unsafe_allow_html=True)

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
    if st.button("Auswahl aufheben"):
        st.session_state.selected_task = None
        st.rerun()

with st.expander("Lernfaecher verwalten"):
    c1, c2, c3 = st.columns([3, 1, 1])
    name = c1.text_input("Fach Name")
    target = c2.number_input("Ziel", min_value=1, value=4)
    if c3.button("Hinzufuegen"):
        if name:
            st.session_state.tasks[name] = {"done": 0, "target": target}
            st.rerun()

if st.session_state.tasks:
    for t_name, t_data in list(st.session_state.tasks.items()):
        is_active = (st.session_state.selected_task == t_name)
        css = "active-task-box" if is_active else "inactive-task-box"
        st.markdown(
            "<div class='" + css + "'><b>" + t_name + "</b> | Erledigt: "
            + str(t_data['done']) + "/" + str(t_data['target']) + "</div>",
            unsafe_allow_html=True
        )
        b1, b2, _ = st.columns([0.2, 0.2, 0.6])
        if not is_active:
            if b1.button("Start", key="s_" + t_name):
                st.session_state.selected_task = t_name
                st.rerun()
        if b2.button("Loeschen", key="d_" + t_name):
            del st.session_state.tasks[t_name]
            if st.session_state.selected_task == t_name:
                st.session_state.selected_task = None
            st.rerun()

# --- ALARM ABSPIELEN / STOPPEN ---
# Läuft bei JEDEM Rerun - unabhängig vom Kamera-Zyklus
if st.session_state.alarm_playing and alarm_b64:
    components.html(
        "<audio id='pomo-alarm' autoplay loop>"
        "<source src='data:audio/mp3;base64," + alarm_b64 + "' type='audio/mp3'>"
        "</audio>"
        "<script>"
        "(function() {"
        "  var existing = window.parent.document.getElementById('pomo-alarm-global');"
        "  if (!existing) {"
        "    var a = document.createElement('audio');"
        "    a.id = 'pomo-alarm-global';"
        "    a.loop = true;"
        "    a.src = 'data:audio/mp3;base64," + alarm_b64 + "';"
        "    window.parent.document.body.appendChild(a);"
        "    a.play().catch(function() {});"
        "  }"
        "})();"
        "</script>",
        height=0
    )
else:
    components.html(
        "<script>"
        "(function() {"
        "  var a = window.parent.document.getElementById('pomo-alarm-global');"
        "  if (a) { a.pause(); a.currentTime = 0; a.remove(); }"
        "})();"
        "</script>",
        height=0
    )

# --- KI SCANNER ---
scanner_active = st.session_state.active and st.session_state.mode == "Pomodoro" and model_loaded

if scanner_active:
    st.markdown("<div class='scan-box'>", unsafe_allow_html=True)
    col_cam, col_status = st.columns([2, 1])

    with col_cam:
        # JS-Auto-Klick: alle 5s den "Take Photo"-Button klicken
        # Diesmal mit korrektem Interval-Management
        components.html(
            "<script>"
            "(function() {"
            "  if (window.parent._pomoInterval) {"
            "    clearInterval(window.parent._pomoInterval);"
            "  }"
            "  function clickCam() {"
            "    var btns = Array.from(window.parent.document.querySelectorAll('button'));"
            "    var btn = btns.find(function(b) { return b.innerText.trim() === 'Take Photo'; });"
            "    if (btn) btn.click();"
            "  }"
            "  window.parent._pomoInterval = setInterval(clickCam, 5000);"
            "})();"
            "</script>",
            height=0
        )
        img_file = st.camera_input(
            "Kamera",
            key="cam_" + str(st.session_state.cam_key),
            label_visibility="collapsed"
        )

    with col_status:
        if st.session_state.handy_detected:
            st.error("HANDY ERKANNT!")
        else:
            st.success("FOKUS AKTIV")

    st.markdown("</div>", unsafe_allow_html=True)

    # Bild sofort verarbeiten wenn vorhanden
    if img_file is not None:
        img_b64 = "data:image/jpeg;base64," + base64.b64encode(img_file.read()).decode()
        lbl, score = analyze_image(img_b64)

        if "handy" in lbl and score > 0.7:
            st.session_state.handy_detected = True
            st.session_state.alarm_playing = True
            st.session_state.bg_color = "#ba4949"
        else:
            st.session_state.handy_detected = False
            st.session_state.alarm_playing = False
            st.session_state.bg_color = "#2d5a27"

        # cam_key IMMER hochzählen - verhindert das Einfrieren
        st.session_state.cam_key += 1
        st.rerun()

else:
    # Scanner aus: Interval stoppen
    components.html(
        "<script>"
        "if (window.parent._pomoInterval) {"
        "  clearInterval(window.parent._pomoInterval);"
        "  window.parent._pomoInterval = null;"
        "}"
        "</script>",
        height=0
    )
    st.session_state.alarm_playing = False
    st.session_state.handy_detected = False

# Timer-Rerun
if st.session_state.active:
    time.sleep(0.1)
    st.rerun()
