"""QR code image generation for share URLs."""

from __future__ import annotations

from io import BytesIO

import qrcode
from qrcode.image.pil import PilImage


def make_qr_png(url: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#080B14", back_color="#F8FAFC", image_factory=PilImage)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
