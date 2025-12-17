"""Condition matcher for matching assessment statuses to schema conditions"""

from typing import Dict, Optional
from ..models import HazardCondition


class ConditionMatchError(Exception):
    """Exception raised when condition matching fails"""
    pass


class ConditionMatcher:
    """
    Match assessment statuses to schema conditions.

    OHAS outputs assessment statuses like:
    - "Safe"
    - "High Potential"
    - "Prone; Within the tsunami inundation zone"
    - "Highly Prone"

    This class maps these to schema condition keys like:
    - "safe"
    - "high_potential"
    - "prone"
    - "highly_prone"
    """

    @staticmethod
    def match_status(
        status: str,
        conditions: Dict[str, HazardCondition]
    ) -> Optional[str]:
        """
        Match assessment status to condition key.

        Args:
            status: Assessment status from OHAS (e.g., "High Potential")
            conditions: Dictionary of condition key → HazardCondition

        Returns:
            Condition key (e.g., "high_potential") or None if no match

        Examples:
            >>> conditions = {
            ...     "safe": HazardCondition(template="Safe"),
            ...     "high_potential": HazardCondition(template="High Potential")
            ... }
            >>> match_status("High Potential", conditions)
            "high_potential"
        """
        if not status or status == "--":
            return None

        # Try exact template match first
        for key, condition in conditions.items():
            if condition.template == status:
                return key

        # Fall back to fuzzy matching
        return ConditionMatcher._fuzzy_match(status, conditions)

    @staticmethod
    def _fuzzy_match(
        status: str,
        conditions: Dict[str, HazardCondition]
    ) -> Optional[str]:
        """
        Fuzzy match status to condition using keyword detection.

        Args:
            status: Assessment status string
            conditions: Dictionary of conditions

        Returns:
            Condition key or None
        """
        status_lower = status.lower()

        # Safe variants
        if status_lower == "safe":
            return "safe"

        # Liquefaction potential variants
        if "high potential" in status_lower:
            return "high_potential"
        if "moderate potential" in status_lower:
            return "moderate_potential"
        if "low potential" in status_lower:
            return "low_potential"

        # Landslide susceptibility variants
        if "highly susceptible" in status_lower:
            return "highly_susceptible"
        if "moderately susceptible" in status_lower:
            return "moderately_susceptible"
        if "least susceptible" in status_lower:
            return "least_susceptible"

        # Lahar prone variants (Mayon)
        if "highly prone" in status_lower:
            return "highly_prone"
        if "moderately prone" in status_lower:
            return "moderately_prone"
        if "least prone" in status_lower:
            return "least_prone"

        # Generic prone (tsunami, other hazards)
        if "prone" in status_lower:
            return "prone"

        # Active fault buffer zone
        if "buffer" in status_lower or "zone of avoidance" in status_lower:
            return "buffer_zone"

        # Active fault transected
        if "transected" in status_lower:
            return "transected"

        # PDZ variants
        if "within pdz" in status_lower or "permanent danger zone" in status_lower:
            return "within_pdz"

        # Pinatubo lahar zones
        if "zone" in status_lower:
            # Extract zone number if present
            import re
            zone_match = re.search(r"zone\s+([1-5])", status_lower)
            if zone_match:
                zone_num = zone_match.group(1)
                return f"zone_{zone_num}"

        # No match found
        return None

    @staticmethod
    def match_liquefaction(status: str) -> str:
        """
        Match liquefaction status to condition.

        Args:
            status: Liquefaction status (e.g., "High Potential")

        Returns:
            Condition key (e.g., "high_potential")

        Examples:
            >>> match_liquefaction("High Potential")
            "high_potential"
            >>> match_liquefaction("Safe")
            "safe"
        """
        status_lower = status.lower()

        if "high potential" in status_lower:
            return "high_potential"
        elif "moderate potential" in status_lower:
            return "moderate_potential"
        elif "low potential" in status_lower:
            return "low_potential"
        elif "safe" in status_lower:
            return "safe"
        else:
            # Default to safe if uncertain
            return "safe"

    @staticmethod
    def match_landslide(status: str) -> str:
        """
        Match landslide (EIL) status to condition.

        Args:
            status: Landslide status (e.g., "Highly Susceptible")

        Returns:
            Condition key (e.g., "highly_susceptible")
        """
        status_lower = status.lower()

        if "highly susceptible" in status_lower:
            return "highly_susceptible"
        elif "moderately susceptible" in status_lower:
            return "moderately_susceptible"
        elif "least susceptible" in status_lower:
            return "least_susceptible"
        elif "safe" in status_lower:
            return "safe"
        else:
            # Default based on presence of "susceptible"
            if "susceptible" in status_lower:
                return "moderately_susceptible"
            return "safe"

    @staticmethod
    def match_tsunami(status: str) -> str:
        """
        Match tsunami status to condition.

        Args:
            status: Tsunami status

        Returns:
            Condition key
        """
        status_lower = status.lower()

        if "prone" in status_lower:
            return "prone"
        elif "safe" in status_lower:
            return "safe"
        else:
            return "safe"

    @staticmethod
    def match_lahar(status: str, volcano_name: str) -> str:
        """
        Match lahar status to condition (volcano-specific).

        Args:
            status: Lahar status
            volcano_name: Name of volcano

        Returns:
            Condition key
        """
        status_lower = status.lower()
        volcano_lower = volcano_name.lower()

        # Pinatubo: Zone-based
        if "pinatubo" in volcano_lower:
            if "zone" in status_lower:
                import re
                zone_match = re.search(r"zone\s+([1-5])", status_lower)
                if zone_match:
                    return f"zone_{zone_match.group(1)}"
            # Default to safe if no zone specified
            return "safe"

        # Mayon: Prone classification
        if "mayon" in volcano_lower:
            if "highly prone" in status_lower:
                return "highly_prone"
            elif "moderately prone" in status_lower:
                return "moderately_prone"
            elif "least prone" in status_lower:
                return "least_prone"
            elif "safe" in status_lower:
                return "safe"
            # Default based on presence of "prone"
            if "prone" in status_lower:
                return "moderately_prone"
            return "safe"

        # Default volcanoes: prone/safe
        if "prone" in status_lower:
            return "prone"
        elif "safe" in status_lower:
            return "safe"
        else:
            return "safe"
