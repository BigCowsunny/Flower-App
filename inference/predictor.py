from __future__ import annotations

import numpy as np


def predict_one(model, pixels: np.ndarray, classes: list[str], thai_names: dict[str, str]) -> dict:
    probabilities = np.asarray(model(pixels[None, ...], training=False).numpy())[0]
    if probabilities.shape != (len(classes),) or not np.isfinite(probabilities).all():
        raise ValueError("ผลโมเดลมีจำนวนคลาสหรือค่าตัวเลขไม่ถูกต้อง")
    if not np.allclose(probabilities.sum(), 1.0, atol=1e-3):
        raise ValueError("ผลลัพธ์ไม่ใช่ softmax probabilities ตามที่คาด")
    order = np.argsort(-probabilities, kind="stable")[:3]
    top3 = [{"class_name": classes[int(i)], "thai_name": thai_names.get(classes[int(i)], classes[int(i)]), "confidence": float(probabilities[int(i)])} for i in order]
    return {"class_name": top3[0]["class_name"], "thai_name": top3[0]["thai_name"], "confidence": top3[0]["confidence"], "top3": top3}
