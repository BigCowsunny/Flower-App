from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

MODEL_NAMES = ("MobileNetV2", "ResNet50", "EfficientNetB0")


def _read_mapping(root: Path) -> dict:
    mapping_path = root / "class_mapping.json"
    if not mapping_path.is_file():
        raise FileNotFoundError(f"ไม่พบ class_mapping.json ที่ {mapping_path}")
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    class_to_index = data.get("class_to_index")
    if not isinstance(class_to_index, dict) or not class_to_index:
        raise ValueError("class_mapping.json ไม่มี class_to_index ที่ถูกต้อง")
    indexed = {int(index): name for name, index in class_to_index.items()}
    if len(indexed) != len(class_to_index) or set(indexed) != set(range(len(indexed))):
        raise ValueError("ลำดับคลาสต้องมี index ไม่ซ้ำและต่อเนื่องจาก 0")
    if data.get("index_to_class") is not None:
        declared = {int(index): name for index, name in data["index_to_class"].items()}
        if indexed != declared:
            raise ValueError("class_to_index และ index_to_class ไม่ตรงกัน")
    thai = data.get("thai_names", {})
    return {"classes": [indexed[i] for i in range(len(indexed))], "thai_names": thai}


@st.cache_data(show_spinner=False)
def load_bundle(model_root: str) -> dict:
    root = Path(model_root).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"ไม่พบโฟลเดอร์โมเดล: {root}")
    mapping = _read_mapping(root)
    # Legacy metadata is absent in this local bundle. The checked training pipeline and
    # serialized model input shapes independently establish RGB 224x224x3.
    size = (224, 224)
    return {"root": str(root), "classes": mapping["classes"], "thai_names": mapping["thai_names"], "class_count": len(mapping["classes"]), "image_size": size}


@st.cache_resource(show_spinner="กำลังโหลดโมเดล...")
def load_model_cached(model_root: str, model_name: str, image_size: tuple[int, int], class_count: int):
    if model_name not in MODEL_NAMES:
        raise ValueError(f"ไม่รู้จักโมเดล: {model_name}")
    model_path = Path(model_root) / model_name / "best_model.keras"
    if not model_path.is_file():
        raise FileNotFoundError(f"ไม่พบไฟล์โมเดล: {model_path}")
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(model_path, compile=False, safe_mode=True)
    except Exception as exc:
        raise RuntimeError(f"โหลด {model_name} ไม่สำเร็จ: {exc}") from exc
    expected = (None, int(image_size[0]), int(image_size[1]), 3)
    shape = tuple(model.input_shape)
    if shape != expected:
        raise ValueError(f"อินพุตของ {model_name} คือ {shape} แต่ metadata ระบุ {expected}")
    output_shape = tuple(model.output_shape)
    if output_shape[-1] != class_count:
        raise ValueError(f"โมเดล {model_name} มี {output_shape[-1]} outputs แต่ mapping มี {class_count} คลาส")
    return model
