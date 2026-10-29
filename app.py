from __future__ import annotations

import io
import json
import base64
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

from inference.loader import MODEL_FILES, MODEL_NAMES, load_bundle, load_model_cached
from inference.predictor import predict_one
from inference.preprocess import prepare_image
from inference.flower_info import flower_info
from inference.translations import text as ui_text


ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "config" / "settings.json"
MASCOT_PATH = ROOT / "assets" / "flower_gardener.png"
NAV_ICON_PATHS = {
    "home": ROOT / "assets" / "navigation" / "home.png",
    "upload": ROOT / "assets" / "navigation" / "upload.png",
    "scan": ROOT / "assets" / "navigation" / "wireless.png",
}
MAX_FILES = 20
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
PREDICTION_MODEL = "EfficientNetB0"
HOME_PAGE = "🏠 หน้าหลัก"
UPLOAD_PAGE = "🖼️ อัปโหลดภาพ"
CAMERA_PAGE = "📷 สแกนด้วยกล้อง"
MODEL_SELECT_PAGE = "🧠 เลือกโมเดล"

st.set_page_config(page_title="Flower APP", page_icon="🌼", layout="wide")


def read_settings() -> dict:
    try:
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"อ่านไฟล์ตั้งค่าไม่ได้: {exc}") from exc
    model_root = Path(settings.get("model_root", "models"))
    if not model_root.is_absolute():
        model_root = ROOT / model_root
    settings["model_root"] = str(model_root.resolve())
    return settings


try:
    SETTINGS = read_settings()
    BUNDLE = load_bundle(SETTINGS["model_root"])
    STARTUP_ERROR = None
except Exception as exc:
    BUNDLE = None
    STARTUP_ERROR = str(exc)


st.markdown("""
<style>
  .block-container {max-width: 1080px; padding-top: 4.5rem; padding-bottom: 6.5rem;}
  [data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#fff7fa 0%,#fffafd 42rem,#fff 75rem); color:#493444;}
  [data-testid="stMetric"] {background:#fff3f7; border:1px solid #f8d9e4; padding:.85rem; border-radius:18px;}
  [data-testid="stMetricLabel"] {color:#866476; font-weight:600; font-size:clamp(.72rem,1.3vw,.9rem);}
  [data-testid="stMetricValue"] {color:#4d3044; font-weight:700; letter-spacing:-.03em; font-size:clamp(1.15rem,2.8vw,1.8rem);}
  .st-key-app_hero {background:linear-gradient(118deg,#fff1f6 0%,#ffe5ef 55%,#f9dfeb 100%); border:1px solid #f4cfdd;
    border-radius:30px; padding:1.35rem 1.55rem .65rem; box-shadow:0 16px 38px #a53d6d12; overflow:hidden;}
  .st-key-app_hero h1 {color:#492d42; margin:.2rem 0 .55rem; letter-spacing:-.035em; font-size:clamp(2rem,4vw,3rem);}
  .st-key-app_hero p {color:#77566b; font-size:1.03rem; line-height:1.6;}
  .topline {color:#d3658f; font-size:.82rem; font-weight:800; letter-spacing:.13em;}
  .hero-pill {display:inline-block; border:1px solid #f2c9d8; background:#fff9fb; color:#8b5872;
    border-radius:999px; padding:.38rem .7rem; margin:.45rem .25rem 0 0; font-size:.82rem; font-weight:650;}
  .st-key-upload_card,.st-key-scan_card {height:100%; padding:1.2rem 1.25rem; background:linear-gradient(180deg,#fff 0%,#fffafd 100%);
    border:1px solid #f0d7e1; border-radius:24px; box-shadow:0 10px 28px #a53d6d0d;}
  .st-key-upload_card h3,.st-key-scan_card h3 {color:#52364b; margin:.1rem 0 .4rem;}
  .st-key-scan_card {background:linear-gradient(145deg,#fff 0%,#fff4f8 100%);}
  .workflow-steps {display:flex; align-items:center; gap:.55rem; flex-wrap:wrap; margin:.25rem 0 1.2rem; color:#805f71; font-size:.84rem;}
  .workflow-steps span {background:#fff; border:1px solid #f0d9e3; border-radius:999px; padding:.4rem .72rem;}
  .workflow-steps b {color:#d3658f; font-weight:750; margin-right:.25rem;}
  .scan-prompt {display:flex; align-items:center; gap:.9rem; margin:.8rem 0 1rem; padding:.9rem 1rem; border-radius:18px;
    background:linear-gradient(110deg,#fff0f5,#ffe5ef); border:1px solid #f4d2df; color:#69475b;}
  .scan-prompt-icon {width:48px; height:48px; display:grid; place-items:center; flex:0 0 48px; border-radius:15px;
    background:#fff; color:#cf638d; font-size:1.45rem; box-shadow:0 4px 12px #a53d6d12;}
  .scan-prompt-title {font-weight:750; color:#56384b; margin-bottom:.12rem;}
  .scan-prompt-sub {font-size:.84rem; color:#856d7a;}
  .st-key-camera_capture {padding:1rem 1.1rem; background:#fff8fb; border:1px solid #f3d7e2; border-radius:20px; margin-top:1rem;}
  [data-testid="stFileUploader"] section {background:#fff8fb; border:1px dashed #e9a7c0; border-radius:18px;}
  div.stButton > button {border-radius:14px; min-height:2.8rem; font-weight:700; border-color:#f0cad9; color:#8c4565; background:#fff8fb;}
  div.stButton > button:hover {border-color:#df81a5; color:#793d5a; background:#fff0f5;}
  div.stButton > button[kind="primary"] {border:0; color:white; background:linear-gradient(100deg,#dd7197,#c85883); box-shadow:0 7px 18px #c858832a;}
  [data-testid="stExpander"] {border-radius:16px; border-color:#f0d4df; background:#fffafd;}
  [data-testid="stVerticalBlockBorderWrapper"] {border-radius:22px; border-color:#f0dce4; background:#fff;}
  [data-testid="stImage"] img {max-width:100%; border-radius:20px; box-shadow:0 8px 22px #7e435814;}
  .model-label {display:inline-block; color:#995676; background:#fff1f6; border:1px solid #f5d4e0;
    border-radius:999px; padding:.35rem .75rem; font-size:.86rem; font-weight:700; margin:.1rem 0 .75rem;}
  .result-card {background:linear-gradient(180deg,#fff 0%,#fffafd 100%); border:1px solid #f0dce4;
    border-radius:24px; padding:1rem 1.1rem; box-shadow:0 12px 28px #7e43580b;}
  .flower-heading {display:flex; align-items:center; gap:.8rem; margin:.1rem 0 1rem;}
  .flower-badge {width:58px; height:58px; display:grid; place-items:center; border-radius:50%;
    background:linear-gradient(145deg,#e9f8ec,#c8edcf); border:2px solid #fff; box-shadow:0 3px 12px #39754b22; font-size:1.8rem;}
  .flower-name {font-size:1.22rem; font-weight:800; color:#3d4d41; line-height:1.2;}
  .flower-scientific {font-size:.91rem; color:#62916b; font-style:italic; margin-top:.2rem;}
  .result-status {display:inline-flex; align-items:center; gap:.4rem; padding:.45rem .72rem; border-radius:999px;
    color:#287c43; background:#eaf7ed; border:1px solid #cdebd3; font-weight:750; font-size:.9rem;}
  .result-card h4 {color:#4e3045; margin:.55rem 0 .25rem;}
  .section-title {color:#4e3045; letter-spacing:-.02em; margin-top:1.8rem;}
  [data-testid="stCaptionContainer"] {color:#806d79;}
  [data-testid="stFileUploader"] small {color:#806d79;}
  [data-testid="stDownloadButton"] button {border-radius:14px; border-color:#edc5d5; color:#87415f;}
  .st-key-navigation {position:fixed; z-index:1000; bottom:max(12px, env(safe-area-inset-bottom)); left:50%; transform:translateX(-50%);
    width:fit-content; max-width:calc(100vw - 24px); margin:0; padding:.4rem; background:rgba(255,255,255,.98);
    border:1px solid #f0d7e1; border-radius:22px; box-shadow:0 8px 28px #7e435822; backdrop-filter:blur(14px);}
  .st-key-app_header [data-testid="stRadio"] > label {display:none;}
  .st-key-app_header [role="radiogroup"] {justify-content:flex-end; gap:0 !important; padding:.2rem; background:#fff;
    border:1px solid #f0d7e1; border-radius:999px;}
  .st-key-app_header label[data-baseweb="radio"] {margin:0; padding:.3rem .65rem; border-radius:999px; color:#806d79; cursor:pointer;}
  .st-key-app_header label[data-baseweb="radio"]:has(input:checked) {background:#ffe6ef; color:#a94770; font-weight:700;}
  .st-key-app_header label[data-baseweb="radio"] > div:first-child {position:absolute; opacity:0; width:1px; height:1px; overflow:hidden;}
  .st-key-navigation [role="radiogroup"] {display:flex !important; flex-wrap:nowrap !important; gap:.25rem !important;
    width:max-content !important; max-width:100%; justify-content:center !important; margin-inline:auto !important;}
  .st-key-navigation label[data-baseweb="radio"] {display:flex; flex-direction:column; align-items:center; justify-content:center;
    flex:0 0 76px; min-width:0; min-height:3.5rem; margin:0; padding:.35rem .15rem; border-radius:16px; color:#866476;
    background:transparent; cursor:pointer; white-space:nowrap;}
  .st-key-navigation label[data-baseweb="radio"]:has(input:checked) {color:#a94770; background:#ffe6ef; font-weight:700;}
  .st-key-navigation label[data-baseweb="radio"] > div:first-child {position:absolute; opacity:0; width:1px; height:1px; overflow:hidden;}
  .st-key-navigation label[data-baseweb="radio"] p {display:flex; flex-direction:column; align-items:center; gap:.2rem;
    margin:0; font-size:.8rem; line-height:1.1; white-space:nowrap;}
  .st-key-navigation label[data-baseweb="radio"] p::before {content:""; display:block; width:21px; height:21px;
    background-repeat:no-repeat; background-position:center; background-size:contain;
    filter:invert(39%) sepia(30%) saturate(802%) hue-rotate(280deg) brightness(88%) contrast(87%);
  }
  .st-key-navigation label[data-baseweb="radio"]:nth-of-type(1) p::before {background-image:url("NAV_HOME_ICON");}
  .st-key-navigation label[data-baseweb="radio"]:nth-of-type(2) p::before {background-image:url("NAV_UPLOAD_ICON");}
  .st-key-navigation label[data-baseweb="radio"]:nth-of-type(3) p::before {background-image:url("NAV_SCAN_ICON");}
  .st-key-navigation label[data-baseweb="radio"]:nth-of-type(4) p::before {content:"🧠"; background-image:none; filter:none; font-size:18px;}
  .st-key-app_hero .stButton {margin-top:.35rem;}
  [data-testid="stImage"] {display:flex; flex-direction:column; align-items:center; justify-content:center; width:100% !important; max-width:100%; min-width:0; box-sizing:border-box; overflow:hidden;}
  [data-testid="stImage"] img {display:block; width:100% !important; max-width:100% !important; height:auto !important; margin-inline:auto !important; object-fit:contain;}
  [data-testid="stImage"] figcaption {width:100%; text-align:center;}
  .st-key-result_image {width:min(100%, 640px); max-width:calc(100vw - 3rem); min-width:0; margin-inline:auto; padding-inline:.4rem; box-sizing:border-box; overflow:hidden;}
  @media (max-width:760px) {
    .block-container {padding:3.4rem .9rem 7rem;}
    .st-key-app_hero {padding:1rem; border-radius:22px;}
    .st-key-app_hero h1 {font-size:clamp(1.65rem,7vw,2.35rem); line-height:1.2;}
    .st-key-app_hero p {font-size:.95rem;}
    [data-testid="stHorizontalBlock"] {flex-wrap:wrap !important; gap:.65rem !important;}
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {min-width:100% !important; flex:1 1 100% !important;}
    .st-key-navigation {bottom:max(10px, env(safe-area-inset-bottom)); padding:.3rem; border-radius:19px;}
    .st-key-navigation label[data-baseweb="radio"] {flex-basis:calc((100vw - 56px) / 4); min-height:3.2rem; padding:.3rem .08rem;}
    .st-key-navigation label[data-baseweb="radio"] p {font-size:clamp(.62rem,2.8vw,.75rem);}
    .st-key-navigation label[data-baseweb="radio"] p::before {width:19px; height:19px;}
    .st-key-upload_previews [data-testid="stHorizontalBlock"] {gap:.5rem !important;}
    .st-key-upload_previews [data-testid="stHorizontalBlock"] > [data-testid="column"] {min-width:calc(50% - .5rem) !important; flex:1 1 calc(50% - .5rem) !important;}
    .st-key-result_image {max-width:100%;}
    [data-testid="stMetric"] {padding:.7rem;}
    [data-testid="stMetricValue"] {font-size:clamp(1.2rem,6vw,1.7rem);}
    .st-key-camera_capture {padding:.75rem;}
    .flower-heading {gap:.6rem;}
    .flower-badge {width:48px; height:48px; flex:0 0 48px;}
    .flower-name {font-size:1.1rem;}
    [data-testid="stExpander"] summary {font-size:.9rem;}
  }
</style>
""".replace("NAV_HOME_ICON", "data:image/png;base64," + base64.b64encode(NAV_ICON_PATHS["home"].read_bytes()).decode("ascii"))
   .replace("NAV_UPLOAD_ICON", "data:image/png;base64," + base64.b64encode(NAV_ICON_PATHS["upload"].read_bytes()).decode("ascii"))
   .replace("NAV_SCAN_ICON", "data:image/png;base64," + base64.b64encode(NAV_ICON_PATHS["scan"].read_bytes()).decode("ascii")), unsafe_allow_html=True)

if STARTUP_ERROR:
    startup_language = st.session_state.get("language", "TH")
    st.error(ui_text("startup_error", startup_language, error=STARTUP_ERROR))
    st.stop()

AVAILABLE_MODELS = tuple(
    name for name in MODEL_NAMES
    if (Path(BUNDLE["root"]) / name / MODEL_FILES[name]).is_file()
)

for state_key, default in {
    "results": None,
    "upload_token": 0,
    "model_upload_token": 0,
    "camera_mode": False,
    "camera_token": 0,
    "confirmed_camera_photo": None,
    "uploaded_items": [],
    "model_uploaded_items": [],
    "language": "TH",
    "active_page": HOME_PAGE,
}.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default


def on_page_change() -> None:
    if st.session_state.active_page == CAMERA_PAGE and st.session_state.confirmed_camera_photo is None:
        st.session_state.camera_mode = True


def go_to_page(page: str) -> None:
    st.session_state.active_page = page
    on_page_change()


def remember_uploads() -> None:
    selected = st.session_state.get(f"uploads_{st.session_state.upload_token}") or []
    st.session_state.uploaded_items = [{"name": item.name, "raw": item.getvalue()} for item in selected]
    if st.session_state.results and st.session_state.results.get("source") == UPLOAD_PAGE:
        st.session_state.results = None


def remember_model_uploads() -> None:
    selected = st.session_state.get(f"model_uploads_{st.session_state.model_upload_token}") or []
    st.session_state.model_uploaded_items = [{"name": item.name, "raw": item.getvalue()} for item in selected]
    if st.session_state.results and st.session_state.results.get("source") == MODEL_SELECT_PAGE:
        st.session_state.results = None


def clear_model_results() -> None:
    if st.session_state.results and st.session_state.results.get("source") == MODEL_SELECT_PAGE:
        st.session_state.results = None


def retake_photo() -> None:
    st.session_state.camera_token += 1
    st.session_state.confirmed_camera_photo = None
    st.session_state.camera_mode = True
    if st.session_state.results and st.session_state.results.get("source") == CAMERA_PAGE:
        st.session_state.results = None


with st.container(key="app_header"):
    brand_col, language_col = st.columns([5, 1], vertical_alignment="center")
    with brand_col:
        st.markdown('<div class="topline">🌸 Flower APP <span style="color:#a38b98;font-weight:500;letter-spacing:0">· FLOWER IDENTIFIER</span></div>', unsafe_allow_html=True)
    with language_col:
        st.radio("TH / EN", ["TH", "EN"], horizontal=True, key="language", label_visibility="collapsed")

language = st.session_state.language
def t(key: str, **values) -> str:
    return ui_text(key, language, **values)

active_page = st.session_state.active_page

with st.container(key="navigation"):
    active_page = st.radio(
        t("main_menu"), [HOME_PAGE, UPLOAD_PAGE, CAMERA_PAGE, MODEL_SELECT_PAGE],
        format_func=lambda page: {HOME_PAGE: t("nav_home"), UPLOAD_PAGE: t("nav_upload"), CAMERA_PAGE: t("nav_camera"), MODEL_SELECT_PAGE: t("nav_models")}[page],
        horizontal=True, key="active_page", label_visibility="collapsed", on_change=on_page_change,
    )

if active_page == HOME_PAGE:
    with st.container(key="app_hero"):
        intro, mascot = st.columns([1.65, 1], vertical_alignment="center")
        with intro:
            st.markdown(f'<div class="topline">{t("home_helper")}</div>', unsafe_allow_html=True)
            st.title(t("welcome"))
            st.write(t("home_description"))
            st.write(t("start"))
            st.button(t("button_upload"), type="primary", use_container_width=True,
                      on_click=go_to_page, args=(UPLOAD_PAGE,))
            st.button(t("button_camera"), use_container_width=True,
                      on_click=go_to_page, args=(CAMERA_PAGE,))
            st.button(t("button_models"), use_container_width=True,
                      on_click=go_to_page, args=(MODEL_SELECT_PAGE,))
        with mascot:
            if MASCOT_PATH.is_file():
                st.image(str(MASCOT_PATH), width="stretch")
    st.markdown(f"### {t('workflow_title')}")
    st.markdown(f'<div class="workflow-steps"><span><b>01</b> {t("step_1")}</span><span><b>02</b> {t("step_2")}</span><span><b>03</b> {t("step_3")}</span></div>', unsafe_allow_html=True)
    st.stop()

if active_page == UPLOAD_PAGE:
    st.markdown(f"## {t('upload_title')}")
    st.caption(t("upload_limits"))
    with st.container(key="upload_card"):
        st.markdown(f"### {t('select_images')}")
        st.caption(t("select_images_hint"))
        st.file_uploader(t("file_uploader"), type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                         key=f"uploads_{st.session_state.upload_token}", label_visibility="collapsed", on_change=remember_uploads)
elif active_page == MODEL_SELECT_PAGE:
    st.markdown(f"## {t('model_title')}")
    st.caption(t("model_hint"))
    st.selectbox(t("model_label"), AVAILABLE_MODELS, key="selected_model", on_change=clear_model_results)
    with st.container(key="upload_card"):
        st.markdown(f"### {t('select_images')}")
        st.caption(t("select_images_hint"))
        st.file_uploader(t("file_uploader"), type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
                         key=f"model_uploads_{st.session_state.model_upload_token}", label_visibility="collapsed", on_change=remember_model_uploads)
else:
    st.markdown(f"## {t('camera_title')}")
    st.caption(t("camera_hint"))
    if st.session_state.confirmed_camera_photo is not None:
        st.button(t("retake"), on_click=retake_photo, use_container_width=True)

camera_photo = None
if active_page == CAMERA_PAGE and st.session_state.camera_mode:
    with st.container(key="camera_capture"):
        st.markdown(f"### {t('camera_heading')}")
        st.caption(t("camera_permission"))
        camera_photo = st.camera_input(t("camera_heading"), key=f"camera_{st.session_state.camera_token}", label_visibility="collapsed")
        if camera_photo is not None:
            st.subheader(t("review_photo"))
            st.image(camera_photo, caption=t("camera_photo"), width="stretch")
            st.caption(t("camera_not_sent"))
            confirm_col, retry_col = st.columns(2)
            with confirm_col:
                if st.button(t("confirm_photo"), type="primary", use_container_width=True):
                    st.session_state.confirmed_camera_photo = camera_photo.getvalue()
                    st.session_state.camera_mode = False
                    st.rerun()
            with retry_col:
                st.button(t("retake_short"), use_container_width=True, on_click=retake_photo)

input_items = list(st.session_state.uploaded_items) if active_page == UPLOAD_PAGE else []
if active_page == MODEL_SELECT_PAGE:
    input_items = list(st.session_state.model_uploaded_items)
if active_page == CAMERA_PAGE and st.session_state.confirmed_camera_photo is not None:
    input_items.append({"name": t("camera_filename"), "raw": st.session_state.confirmed_camera_photo})

if len(input_items) > MAX_FILES:
    st.error(t("too_many_images", count=MAX_FILES))
    st.stop()

valid_uploads = []
bad_files = []
for uploaded in input_items:
    suffix = Path(uploaded["name"]).suffix.lower()
    raw = uploaded["raw"]
    if suffix not in ALLOWED_SUFFIXES:
        bad_files.append((uploaded["name"], t("unsupported_type")))
        continue
    if len(raw) > MAX_FILE_BYTES:
        bad_files.append((uploaded["name"], t("file_too_large")))
        continue
    try:
        with Image.open(io.BytesIO(raw)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(raw)) as opened:
            opened.load()
            oriented = ImageOps.exif_transpose(opened).convert("RGB")
            if oriented.width * oriented.height > MAX_IMAGE_PIXELS:
                bad_files.append((uploaded["name"], t("image_too_large")))
                continue
            preview = oriented.copy()
        valid_uploads.append({"name": uploaded["name"], "raw": raw, "preview": preview})
    except Exception as exc:
        bad_files.append((uploaded["name"], t("image_open_error", kind=type(exc).__name__)))

if bad_files:
    with st.expander(t("skipped_files", count=len(bad_files)), expanded=True):
        for name, reason in bad_files:
            st.warning(f"{name}: {reason}")

if valid_uploads:
    st.subheader(t("preview_count", count=len(valid_uploads)))
    with st.container(key="upload_previews"):
        columns = st.columns(min(4, len(valid_uploads)))
        for i, item in enumerate(valid_uploads):
            with columns[i % len(columns)]:
                st.image(item["preview"], caption=item["name"], use_container_width=True)
if active_page == CAMERA_PAGE and st.session_state.confirmed_camera_photo is not None:
    st.success(t("camera_confirmed", model=PREDICTION_MODEL))

if st.button(t("predict"), type="primary", disabled=not valid_uploads, use_container_width=True):
    records = []
    failures = []
    with st.status(t("preparing"), expanded=True) as status:
        progress = st.progress(0)
        for i, item in enumerate(valid_uploads, 1):
            try:
                pixels = prepare_image(item["raw"], BUNDLE["image_size"])
                records.append({"filename": item["name"], "pixels": pixels, "preview": item["preview"]})
            except Exception as exc:
                failures.append({"filename": item["name"], "error": t("prepare_error", error=exc)})
            progress.progress(i / len(valid_uploads), text=t("preparing_progress", current=i, total=len(valid_uploads)))

        model_results = {}
        model_name = st.session_state.selected_model if active_page == MODEL_SELECT_PAGE else PREDICTION_MODEL
        status.update(label=t("predicting_model", model=model_name))
        try:
            model = load_model_cached(BUNDLE["root"], model_name, BUNDLE["image_size"], BUNDLE["class_count"], MODEL_FILES[model_name])
            model_results[model_name] = [predict_one(model, row["pixels"], BUNDLE["classes"], BUNDLE["thai_names"]) for row in records]
        except Exception as exc:
            failures.append({"filename": "—", "error": t("model_error", model=model_name, error=exc)})
        st.session_state.results = {"records": records, "model_results": model_results, "failures": failures, "models": [model_name], "source": active_page}
        status.update(label=t("prediction_done"), state="complete", expanded=False)

results = st.session_state.results
if results and results.get("source") == active_page:
    for failure in results["failures"]:
        st.warning(f"{failure['filename']}: {failure['error']}")
    if results["records"] and results["model_results"]:
        st.markdown(f'<h2 class="section-title">{t("prediction_heading")}</h2>', unsafe_allow_html=True)
        for image_index, record in enumerate(results["records"]):
            with st.container(border=True):
                with st.container(key="result_image"):
                    st.image(record["preview"], caption=record["filename"], width="stretch")
                for model_name in results["models"]:
                    if model_name not in results["model_results"]:
                        continue
                    prediction = results["model_results"][model_name][image_index]
                    info = flower_info(prediction["class_name"], language)
                    flower_name = info["common_name"] or prediction["thai_name"]
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="flower-heading"><div class="flower-badge">🌼</div><div>'
                            f'<div class="flower-name">{flower_name}</div>'
                            f'<div class="flower-scientific">{info["scientific_name"]}</div></div></div>'
                            f'<span class="result-status">{t("classified")}</span>',
                            unsafe_allow_html=True,
                        )
                        st.metric(t("confidence"), f"{prediction['confidence'] * 100:.2f}%")
                    with st.expander(t("flower_details"), expanded=True):
                        st.write(f"{t('background')}: {info['details']['background']}")
                        st.write(f"{t('meaning')}: {info['details']['meaning']}")
                        st.write(f"{t('temple')}: {info['details']['temple']}")
                    st.divider()
