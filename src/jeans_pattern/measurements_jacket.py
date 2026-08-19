"""Body measurements for the M. Mueller & Sohn denim jacket draft (Design 4041).

The five body measurements match the chart on page 12 of the booklet; every
auxiliary value the draft needs is derived here via the chart formulas.
All values are stored in millimetres.
"""
from dataclasses import dataclass

from .constants import INCH_TO_MM

CM_TO_MM = 10.0

# Formula adjustment ranges from the chart (page 12); the chosen values are the
# ones that reproduce the size-50 scale drawing on pages 11-13.
NW_ADD_MM = 30.0        # Nw = 1/10 of 1/2 Cg + 3.0 cm  (chart prints 8.5, the
                        # drawing uses 8.0 everywhere -> chart typo)
SD_ADD_MM = 125.0       # Sd = 1/8 Cg + 12.5 cm
LG_SHORTEN_MM = 31.25   # Lg = 1/2 Bh - 1/8 Bh - 2..4 cm  (3.125 -> exactly 64.0)
AD_ADD_MM = 25.0        # Ad = Sd + 2.5 cm
BW_ADD_MM = 12.0        # Bw = 2/10 Cg + 1.0..1.5 cm      (Cg <= 100)
BW_ADD_LARGE_MM = 112.0  # Bw = 1/10 Cg + 11.0..11.5 cm   (Cg > 100; continuous at 100)
SW_ADD_MM = 30.0        # Sw = 1/8 Cg + 2.5..3.5 cm
CW_ADD_MM = 8.0         # Cw = 2/10 Cg + 0.5..1.0 cm
AW_SUB_MM = 13.0        # Aw = 1/4 Wg - 1.0..2.0 cm

BW_SWITCH_CG_MM = 1000.0  # chest girth above which the second Bw formula applies


@dataclass(frozen=True)
class JacketMeasurements:
    """M&S chart (size 50 defaults): Bh 179, Cg 100, Wg 90, Hg 102, Sl 64."""
    body_height_mm: float    # Bh - statura
    chest_girth_mm: float    # Cg - giro petto
    waist_girth_mm: float    # Wg - giro vita
    hip_girth_mm: float      # Hg - giro fianchi
    sleeve_length_mm: float  # Sl - lunghezza manica

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")
        if self.sleeve_length_mm >= self.body_height_mm:
            raise ValueError(
                f"sleeve length ({self.sleeve_length_mm}) must be below "
                f"body height ({self.body_height_mm})"
            )
        if self.jacket_length_mm <= self.armhole_depth_mm:
            raise ValueError(
                f"jacket length ({self.jacket_length_mm}) must exceed "
                f"armhole depth ({self.armhole_depth_mm})"
            )

    @classmethod
    def from_cm(cls, *, body_height, chest_girth, waist_girth, hip_girth, sleeve_length):
        return cls(
            body_height_mm=body_height * CM_TO_MM,
            chest_girth_mm=chest_girth * CM_TO_MM,
            waist_girth_mm=waist_girth * CM_TO_MM,
            hip_girth_mm=hip_girth * CM_TO_MM,
            sleeve_length_mm=sleeve_length * CM_TO_MM,
        )

    @classmethod
    def from_inches(cls, *, body_height, chest_girth, waist_girth, hip_girth, sleeve_length):
        return cls(
            body_height_mm=body_height * INCH_TO_MM,
            chest_girth_mm=chest_girth * INCH_TO_MM,
            waist_girth_mm=waist_girth * INCH_TO_MM,
            hip_girth_mm=hip_girth * INCH_TO_MM,
            sleeve_length_mm=sleeve_length * INCH_TO_MM,
        )

    # ---- derived measurements (chart page 12) ----------------------------

    @property
    def neck_width_mm(self) -> float:
        """Nw = 1/10 of 1/2 Cg + 3.0 cm"""
        return self.chest_girth_mm / 20 + NW_ADD_MM

    @property
    def scye_depth_mm(self) -> float:
        """Sd = 1/8 Cg + 12.5 cm"""
        return self.chest_girth_mm / 8 + SD_ADD_MM

    @property
    def back_waist_length_mm(self) -> float:
        """Bwl = 1/4 Bh"""
        return self.body_height_mm / 4

    @property
    def jacket_length_mm(self) -> float:
        """Lg = 1/2 Bh - 1/8 Bh - 3.125 cm"""
        return self.body_height_mm / 2 - self.body_height_mm / 8 - LG_SHORTEN_MM

    @property
    def armhole_depth_mm(self) -> float:
        """Ad = Sd + 2.5 cm"""
        return self.scye_depth_mm + AD_ADD_MM

    @property
    def back_width_mm(self) -> float:
        """Bw = 2/10 Cg + 1.2 cm, or 1/10 Cg + 11.2 cm above Cg 100 cm."""
        if self.chest_girth_mm > BW_SWITCH_CG_MM:
            return self.chest_girth_mm / 10 + BW_ADD_LARGE_MM
        return self.chest_girth_mm / 5 + BW_ADD_MM

    @property
    def scye_width_mm(self) -> float:
        """Sw = 1/8 Cg + 3.0 cm"""
        return self.chest_girth_mm / 8 + SW_ADD_MM

    @property
    def chest_width_mm(self) -> float:
        """Cw = 2/10 Cg + 0.8 cm"""
        return self.chest_girth_mm / 5 + CW_ADD_MM

    @property
    def abdomen_width_mm(self) -> float:
        """Aw = 1/4 Wg - 1.3 cm, never narrower than Cw."""
        return max(self.waist_girth_mm / 4 - AW_SUB_MM, self.chest_width_mm)
