"""Assessment input data models"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AssessmentCategory(Enum):
    """Category of hazard assessment"""
    EARTHQUAKE = "Earthquake"
    VOLCANO = "Volcano"


class FeatureType(Enum):
    """Type of geographic feature being assessed"""
    POLYGON = "Polygon"
    POINT = "Point"
    LINE = "Line"


@dataclass
class Coordinate:
    """Geographic coordinate"""
    longitude: float
    latitude: float

    @classmethod
    def from_string(cls, coord_str: str) -> 'Coordinate':
        """
        Parse coordinate string in format: 'longitude,latitude'

        Example: '120.989669,14.537869'
        """
        lon, lat = map(float, coord_str.split(','))
        return cls(longitude=lon, latitude=lat)

    def __str__(self) -> str:
        return f"{self.longitude},{self.latitude}"


@dataclass
class EarthquakeAssessment:
    """Earthquake hazard assessment results from OHAS"""
    active_fault: Optional[str] = None
    liquefaction: Optional[str] = None
    landslide: Optional[str] = None
    tsunami: Optional[str] = None
    fissure: Optional[str] = None

    def is_assessed(self, hazard: str) -> bool:
        """
        Check if a hazard was assessed (not '--' or None)

        Args:
            hazard: Name of hazard field (e.g., 'active_fault', 'liquefaction')

        Returns:
            True if hazard was assessed, False otherwise
        """
        value = getattr(self, hazard, None)
        return value is not None and value != "--"


@dataclass
class VolcanoAssessment:
    """Volcano hazard assessment results from OHAS"""
    nearest_active_volcano: Optional[str] = None
    nearest_pav: Optional[str] = None
    fissure: Optional[str] = None
    lahar: Optional[str] = None
    pyroclastic_flow: Optional[str] = None
    base_surge: Optional[str] = None
    lava_flow: Optional[str] = None
    ballistic_projectile: Optional[str] = None
    volcanic_tsunami: Optional[str] = None

    def is_assessed(self, hazard: str) -> bool:
        """
        Check if a hazard was assessed (not '--' or None)

        Args:
            hazard: Name of hazard field (e.g., 'lahar', 'pyroclastic_flow')

        Returns:
            True if hazard was assessed, False otherwise
        """
        value = getattr(self, hazard, None)
        return value is not None and value != "--"


@dataclass
class Assessment:
    """Complete assessment for a single site/lot"""
    id: int
    category: AssessmentCategory
    feature_type: FeatureType
    location: Coordinate
    earthquake: Optional[EarthquakeAssessment] = None
    volcano: Optional[VolcanoAssessment] = None
    vicinity_map_provided: bool = False

    def has_earthquake_assessment(self) -> bool:
        """Check if earthquake assessment data exists"""
        return self.earthquake is not None

    def has_volcano_assessment(self) -> bool:
        """Check if volcano assessment data exists"""
        return self.volcano is not None
