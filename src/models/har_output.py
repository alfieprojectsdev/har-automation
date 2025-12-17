"""HAR output data models"""

from dataclasses import dataclass
from typing import List, Optional
from .assessment import AssessmentCategory


@dataclass
class ExplanationRecommendation:
    """
    Explanation and Recommendation as a paired unit.

    In actual HARs, explanations and recommendations are NOT separate
    paragraphs - they form a single cohesive text block where the
    recommendation immediately follows the explanation.

    Example:
        "Ground rupture hazard assessment is the distance to the nearest
        known active fault. The recommended buffer zone, or Zone of Avoidance,
        against ground rupture hazard is at least 5 meters on both sides of
        the active fault or from its zone of deformation."
    """
    text: str

    @classmethod
    def from_parts(
        cls,
        explanation: Optional[str] = None,
        recommendation: Optional[str] = None
    ) -> 'ExplanationRecommendation':
        """
        Combine explanation and recommendation into single unit.

        Args:
            explanation: Explanation text (optional)
            recommendation: Recommendation text (optional)

        Returns:
            ExplanationRecommendation with combined text

        Raises:
            ValueError: If neither explanation nor recommendation is provided

        Examples:
            >>> ExplanationRecommendation.from_parts(
            ...     explanation="Ground rupture hazard assessment is...",
            ...     recommendation="The recommended buffer zone..."
            ... )
            ExplanationRecommendation(text="Ground rupture hazard assessment is... The recommended buffer zone...")

            >>> ExplanationRecommendation.from_parts(
            ...     recommendation="Ground shaking and liquefaction hazards can be mitigated..."
            ... )
            ExplanationRecommendation(text="Ground shaking and liquefaction hazards can be mitigated...")
        """
        parts = []
        if explanation:
            parts.append(explanation)
        if recommendation:
            parts.append(recommendation)

        if not parts:
            raise ValueError("Must provide at least explanation or recommendation")

        return cls(text=" ".join(parts))


@dataclass
class HARSection:
    """
    A hazard section in the HAR.

    Structure in actual HAR:
    - Heading (e.g., "GROUND RUPTURE", "LIQUEFACTION")
    - Assessment (e.g., "Safe; Approximately 7.1 kilometers west...")
    - Explanation and Recommendation (single unit, not separate)

    Example:
        heading = "GROUND RUPTURE"
        assessment = "Safe; Approximately 7.1 kilometers west of the Valley Fault System"
        explanation_recommendation = ExplanationRecommendation(text="Ground rupture hazard assessment...")
    """
    heading: str
    assessment: str
    explanation_recommendation: ExplanationRecommendation

    def to_numbered_point(self, number: int) -> str:
        """
        Format as numbered point for HAR output.

        Args:
            number: Point number (1, 2, 3, etc.)

        Returns:
            Formatted string like:
            "1. Ground Rupture: Safe; Approximately... Ground rupture hazard assessment..."

        Example:
            >>> section.to_numbered_point(1)
            "1. Ground Rupture: Safe; Approximately 7.1 kilometers west of the Valley Fault System. Ground rupture hazard assessment is the distance to the nearest known active fault. The recommended buffer zone..."
        """
        return f"{number}. {self.heading}: {self.assessment}. {self.explanation_recommendation.text}"


@dataclass
class HAROutput:
    """Complete HAR output for a single assessment"""
    category: AssessmentCategory
    intro: str
    sections: List[HARSection]
    common_statements: List[ExplanationRecommendation]
    supersedes: str
    additional_recommendations: List[str] = None

    def __post_init__(self):
        """Initialize optional fields"""
        if self.additional_recommendations is None:
            self.additional_recommendations = []

    def to_text(self) -> str:
        """
        Generate plain text HAR in official format.

        Structure:
            [CATEGORY] HAZARD ASSESSMENT

            [Intro statement]

            [Summary Table]
            | Hazard | Assessment |

            EXPLANATION AND RECOMMENDATION
            1. [Hazard 1]: [Assessment]. [Explanation + Recommendation]
            2. [Hazard 2]: [Assessment]. [Explanation + Recommendation]
            ...

            [Common statements]

            [Supersedes statement]

            [Additional recommendations]

        Returns:
            Formatted HAR text
        """
        lines = []

        # Header
        lines.append(f"{self.category.value.upper()} HAZARD ASSESSMENT")
        lines.append("")

        # Intro
        lines.append(self.intro)
        lines.append("")

        # TODO: Summary table (will be implemented in formatter module)
        # For now, skip this section

        # Explanation and Recommendation section
        lines.append("EXPLANATION AND RECOMMENDATION")
        lines.append("")

        # Numbered points for each hazard section
        for i, section in enumerate(self.sections, start=1):
            lines.append(section.to_numbered_point(i))
            lines.append("")

        # Common statements (Ground Shaking, Ashfall, etc.)
        point_num = len(self.sections) + 1
        for statement in self.common_statements:
            # Common statements don't have heading or assessment
            # They're just explanation+recommendation
            lines.append(f"{point_num}. {statement.text}")
            lines.append("")
            point_num += 1

        # Supersedes
        lines.append(self.supersedes)
        lines.append("")

        # Additional recommendations
        for rec in self.additional_recommendations:
            lines.append(rec)
            lines.append("")

        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Generate markdown HAR"""
        # TODO: Implement markdown formatting
        # Similar to to_text() but with markdown headers and formatting
        return self.to_text()  # Placeholder

    def to_dict(self) -> dict:
        """Generate JSON-serializable dictionary"""
        return {
            "category": self.category.value,
            "intro": self.intro,
            "sections": [
                {
                    "heading": section.heading,
                    "assessment": section.assessment,
                    "explanation_recommendation": section.explanation_recommendation.text
                }
                for section in self.sections
            ],
            "common_statements": [stmt.text for stmt in self.common_statements],
            "supersedes": self.supersedes,
            "additional_recommendations": self.additional_recommendations
        }
