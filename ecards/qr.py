from pathlib import Path
from urllib.parse import quote
import qrcode
from qrcode.constants import ERROR_CORRECT_M

# Files
INPUT_FILE = "data.txt"
OUTPUT_FILE = "qr.png"

# Read text
text = Path(INPUT_FILE).read_text(encoding="utf-8")
encoded = quote(text, safe="")
print(f"Encoded text: {encoded}")
# Create QR
qr = qrcode.QRCode(
    version=None,  # Auto-size
    error_correction=ERROR_CORRECT_M,
    box_size=10,
    border=4,
)

qr.add_data(text)
qr.make(fit=True)

# Generate image
img = qr.make_image(fill_color="black", back_color="white")
img.save(OUTPUT_FILE)

print(f"QR code saved as {OUTPUT_FILE}")
import cv2

img = cv2.imread("qr.png")
detector = cv2.QRCodeDetector()
data, _, _ = detector.detectAndDecode(img)

print(repr(data))