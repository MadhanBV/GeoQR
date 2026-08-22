import io
import base64
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def generate_qr_base64(data: str, box_size: int = 10, border: int = 2) -> str:
    """
    Generates a high-quality QR code image for the given data string
    and returns it as a Base64-encoded Data URL (e.g., 'data:image/png;base64,...').
    This avoids creating temporary files on the server filesystem.

    :param data: The target URL or text to encode inside the QR code
    :param box_size: The size of each square box in pixels (default: 10)
    :param border: The white border around the QR code in boxes (default: 2)
    :return: Base64 Data URL string ready for direct HTML <img src="..."> usage
    """
    qr = qrcode.QRCode(
        version=None,  # Automatically determine the smallest QR version needed
        error_correction=ERROR_CORRECT_M,  # ~15% error recovery for robust phone camera scanning
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Render image with dark blue brand color (#1E293B / #2563EB) or standard black
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")

    # Save image to in-memory byte buffer
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode bytes to base64 string
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded_image}"
