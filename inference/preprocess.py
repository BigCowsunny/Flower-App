from __future__ import annotations

import io
import warnings

import numpy as np
from PIL import Image, ImageOps


def prepare_image(raw: bytes, image_size: tuple[int, int]) -> np.ndarray:
    """Apply the verified input path: EXIF, RGB, TF bilinear antialias, float32 0..255."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(raw)) as opened:
            opened.load()
            oriented = ImageOps.exif_transpose(opened).convert("RGB")
    array = np.asarray(oriented, dtype=np.uint8)
    import tensorflow as tf
    with tf.device("/CPU:0"):
        resized = tf.image.resize(array, image_size, method="bilinear", antialias=True).numpy()
    return resized.astype(np.float32, copy=False)
