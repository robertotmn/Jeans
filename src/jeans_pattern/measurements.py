"""Body measurements for the M. Mueller & Sohn "Jeans-Basics" draft.

The six body measurements match the chart on page 2 of the booklet; every
auxiliary value the draft needs is derived here via the chart formulas.
All values are stored in millimetres.
"""
from dataclasses import dataclass

from .constants import INCH_TO_MM

CM_TO_MM = 10.0

# Formula adjustment ranges from the chart (page 2); mid-range values are the
# ones the booklet itself uses for size 50 (parenthesised in the chart).
BCW_ADD_MM = 20.0    # Bcw = 1/10 Hg + 1.5..2.5 cm  (2.0)
BTW_ADD_MM = 25.0    # Btw = 1/4 Hg + 2.0..3.0 cm   (2.5)


@dataclass(frozen=True)
class Measurements:
    """M&S chart (size 50 defaults): W 90, Hg 102, Kg 43, Hw 38, Os 102, Is 82."""
    waistband_mm: float    # W  - giro vita
    hip_girth_mm: float    # Hg - giro fianchi
    knee_girth_mm: float   # Kg - giro ginocchio
    hem_width_mm: float    # Hw - giro fondo gamba
    outseam_mm: float      # Os - lunghezza esterna
    inseam_mm: float       # Is - lunghezza interna

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")
        if self.outseam_mm <= self.inseam_mm:
            raise ValueError(
                f"outseam ({self.outseam_mm}) must exceed inseam ({self.inseam_mm})"
            )

    @classmethod
    def from_cm(cls, *, waistband, hip_girth, knee_girth, hem_width, outseam, inseam):
        return cls(
            waistband_mm=waistband * CM_TO_MM,
            hip_girth_mm=hip_girth * CM_TO_MM,
            knee_girth_mm=knee_girth * CM_TO_MM,
            hem_width_mm=hem_width * CM_TO_MM,
            outseam_mm=outseam * CM_TO_MM,
            inseam_mm=inseam * CM_TO_MM,
        )

    @classmethod
    def from_inches(cls, *, waistband, hip_girth, knee_girth, hem_width, outseam, inseam):
        return cls(
            waistband_mm=waistband * INCH_TO_MM,
            hip_girth_mm=hip_girth * INCH_TO_MM,
            knee_girth_mm=knee_girth * INCH_TO_MM,
            hem_width_mm=hem_width * INCH_TO_MM,
            outseam_mm=outseam * INCH_TO_MM,
            inseam_mm=inseam * INCH_TO_MM,
        )

    # ---- derived measurements (chart page 2) -----------------------------

    @property
    def body_rise_mm(self) -> float:
        """Br = Os - Is"""
        return self.outseam_mm - self.inseam_mm

    @property
    def knee_length_mm(self) -> float:
        """Kl = 1/2 Is + 1/10 Is - 2 cm (height of the knee line above the hem)"""
        return self.inseam_mm / 2 + self.inseam_mm / 10 - 2 * CM_TO_MM

    @property
    def front_trouser_width_mm(self) -> float:
        """Ftw = 1/4 Hg"""
        return self.hip_girth_mm / 4

    @property
    def front_crotch_width_mm(self) -> float:
        """Fcw = 1/10 of 1/2 Hg"""
        return self.hip_girth_mm / 20

    @property
    def back_crotch_width_mm(self) -> float:
        """Bcw = 1/10 Hg + 2.0 cm"""
        return self.hip_girth_mm / 10 + BCW_ADD_MM

    @property
    def back_trouser_width_mm(self) -> float:
        """Btw = 1/4 Hg + 2.5 cm"""
        return self.hip_girth_mm / 4 + BTW_ADD_MM

    @property
    def hip_depth_above_crotch_mm(self) -> float:
        """Hip line sits 1/10 of 1/2 Hg + 3 cm above the crotch line."""
        return self.hip_girth_mm / 20 + 3 * CM_TO_MM
