from dataclasses import dataclass

INCH_TO_MM = 25.4

@dataclass(frozen=True)
class Measurements:
    """Tutte le misure salvate in millimetri."""
    waist_mm: float
    seat_mm: float
    rise_mm: float
    knee_mm: float
    bottom_mm: float
    length_mm: float

    def __post_init__(self):
        for name, val in self.__dict__.items():
            if val <= 0:
                raise ValueError(f"{name} must be > 0, got {val}")

    @classmethod
    def from_inches(cls, *, waist, seat, rise, knee, bottom, length):
        return cls(
            waist_mm=waist * INCH_TO_MM,
            seat_mm=seat * INCH_TO_MM,
            rise_mm=rise * INCH_TO_MM,
            knee_mm=knee * INCH_TO_MM,
            bottom_mm=bottom * INCH_TO_MM,
            length_mm=length * INCH_TO_MM,
        )

    @classmethod
    def from_cm(cls, *, waist, seat, rise, knee, bottom, length):
        return cls(
            waist_mm=waist * 10,
            seat_mm=seat * 10,
            rise_mm=rise * 10,
            knee_mm=knee * 10,
            bottom_mm=bottom * 10,
            length_mm=length * 10,
        )
