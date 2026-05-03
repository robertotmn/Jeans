"""Shared physical constants for the cartamodello.

All measurements internally in millimetres. INCH and SA values match the
J.E. Landis drafting PDF (page 4, seam allowance section).
"""

INCH_TO_MM: float = 25.4
INCH: float = INCH_TO_MM   # alias for compactness in draft modules

# Seam allowance presets (PDF page 4):
# - 3/8" everywhere except center back / yoke seam
# - 5/8" for center back seat seam and yoke seam (accommodates felled seam)
SA_3_8_IN_MM: float = 0.375 * INCH_TO_MM   # 9.525 mm
SA_5_8_IN_MM: float = 0.625 * INCH_TO_MM   # 15.875 mm

# Standard 1" hem allowance (PDF p.6 step 4)
HEM_1_IN_MM: float = 1.0 * INCH_TO_MM       # 25.4 mm
