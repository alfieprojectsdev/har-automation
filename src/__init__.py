"""HAR Automation Pipeline"""

from .models import (
    Assessment,
    AssessmentCategory,
    FeatureType,
    Coordinate,
    EarthquakeAssessment,
    VolcanoAssessment,
    HazardRulesSchema,
    ExplanationRecommendation,
    HARSection,
    HAROutput,
)
from .parser import OHASParser, SchemaLoader
from .pipeline import DecisionEngine, ConditionMatcher

__version__ = "0.1.0"

__all__ = [
    # Models
    "Assessment",
    "AssessmentCategory",
    "FeatureType",
    "Coordinate",
    "EarthquakeAssessment",
    "VolcanoAssessment",
    "HazardRulesSchema",
    "ExplanationRecommendation",
    "HARSection",
    "HAROutput",
    # Parser
    "OHASParser",
    "SchemaLoader",
    # Pipeline
    "DecisionEngine",
    "ConditionMatcher",
]
