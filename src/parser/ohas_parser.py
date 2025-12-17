"""Parser for OHAS assessment data"""

from typing import Dict, Optional, Union, List
from ..models import (
    Assessment,
    AssessmentCategory,
    FeatureType,
    Coordinate,
    EarthquakeAssessment,
    VolcanoAssessment,
)


class OHASParseError(Exception):
    """Exception raised when parsing OHAS data fails"""
    pass


class OHASParser:
    """
    Parse OHAS assessment data from various formats.

    Supports:
    - Dictionary (from JSON, database, etc.)
    - Future: HTML table parsing, clipboard parsing
    """

    @staticmethod
    def parse_from_dict(data: Dict) -> Assessment:
        """
        Parse assessment from dictionary format.

        Expected format:
        {
            "id": 24918,
            "category": "Earthquake",
            "feature_type": "Polygon",
            "location": "120.989669,14.537869",
            "earthquake": {
                "active_fault": "Safe; Approximately 7.1 kilometers west...",
                "liquefaction": "High Potential",
                "landslide": "--",
                "tsunami": "Prone; Within the tsunami inundation zone",
                "fissure": "--"
            }
        }

        Args:
            data: Dictionary containing assessment data

        Returns:
            Assessment object

        Raises:
            OHASParseError: If required fields are missing or invalid
        """
        try:
            # Parse required fields
            assessment_id = data.get('id')
            if not assessment_id:
                raise OHASParseError("Missing required field: 'id'")

            category_str = data.get('category')
            if not category_str:
                raise OHASParseError("Missing required field: 'category'")

            category = OHASParser._parse_category(category_str)

            feature_type_str = data.get('feature_type')
            if not feature_type_str:
                raise OHASParseError("Missing required field: 'feature_type'")

            feature_type = OHASParser._parse_feature_type(feature_type_str)

            location_str = data.get('location')
            if not location_str:
                raise OHASParseError("Missing required field: 'location'")

            location = Coordinate.from_string(location_str)

            # Parse optional earthquake assessment
            earthquake = None
            if 'earthquake' in data:
                earthquake = OHASParser._parse_earthquake_assessment(
                    data['earthquake']
                )

            # Parse optional volcano assessment
            volcano = None
            if 'volcano' in data:
                volcano = OHASParser._parse_volcano_assessment(data['volcano'])

            # Check if vicinity map was provided
            vicinity_map_provided = data.get('vicinity_map_provided', False)

            return Assessment(
                id=assessment_id,
                category=category,
                feature_type=feature_type,
                location=location,
                earthquake=earthquake,
                volcano=volcano,
                vicinity_map_provided=vicinity_map_provided
            )

        except (ValueError, KeyError) as e:
            raise OHASParseError(f"Error parsing assessment data: {str(e)}") from e

    @staticmethod
    def _parse_category(category_str: str) -> AssessmentCategory:
        """Parse category string to enum"""
        category_lower = category_str.lower()
        if 'earthquake' in category_lower:
            return AssessmentCategory.EARTHQUAKE
        elif 'volcano' in category_lower:
            return AssessmentCategory.VOLCANO
        else:
            raise OHASParseError(
                f"Unknown category: '{category_str}'. "
                "Must be 'Earthquake' or 'Volcano'"
            )

    @staticmethod
    def _parse_feature_type(feature_type_str: str) -> FeatureType:
        """Parse feature type string to enum"""
        feature_lower = feature_type_str.lower()
        if 'polygon' in feature_lower:
            return FeatureType.POLYGON
        elif 'point' in feature_lower:
            return FeatureType.POINT
        elif 'line' in feature_lower:
            return FeatureType.LINE
        else:
            raise OHASParseError(
                f"Unknown feature type: '{feature_type_str}'. "
                "Must be 'Polygon', 'Point', or 'Line'"
            )

    @staticmethod
    def _parse_earthquake_assessment(
        earthquake_data: Dict
    ) -> EarthquakeAssessment:
        """Parse earthquake assessment data"""
        return EarthquakeAssessment(
            active_fault=earthquake_data.get('active_fault'),
            liquefaction=earthquake_data.get('liquefaction'),
            landslide=earthquake_data.get('landslide'),
            tsunami=earthquake_data.get('tsunami'),
            fissure=earthquake_data.get('fissure')
        )

    @staticmethod
    def _parse_volcano_assessment(volcano_data: Dict) -> VolcanoAssessment:
        """Parse volcano assessment data"""
        return VolcanoAssessment(
            nearest_active_volcano=volcano_data.get('nearest_active_volcano'),
            nearest_pav=volcano_data.get('nearest_pav'),
            fissure=volcano_data.get('fissure'),
            lahar=volcano_data.get('lahar'),
            pyroclastic_flow=volcano_data.get('pyroclastic_flow'),
            base_surge=volcano_data.get('base_surge'),
            lava_flow=volcano_data.get('lava_flow'),
            ballistic_projectile=volcano_data.get('ballistic_projectile'),
            volcanic_tsunami=volcano_data.get('volcanic_tsunami')
        )

    @staticmethod
    def parse_from_table(table_text: str) -> List['Assessment']:
        """
        Parse assessment(s) from markdown table or tab-separated text.

        Supports:
        - Markdown tables (from Obsidian webclipper)
        - TSV (tab-separated, copy-paste from browser)
        - Field-based format (like HAM filename tools)

        Expected format:
        ```
        | Assessment | Category   | Feature Type | Location              | Active Fault | ... |
        |------------|------------|--------------|------------------------|--------------|-----|
        | 24918      | Earthquake | Polygon      | 120.989669,14.537869  | Safe; ...    | ... |
        ```

        Args:
            table_text: Table text in markdown or tab-separated format

        Returns:
            List of Assessment objects (can be multiple rows)

        Raises:
            OHASParseError: If parsing fails
        """
        try:
            from .table_parser import TableParser
            return TableParser.parse_from_text(table_text)
        except Exception as e:
            raise OHASParseError(f"Failed to parse table: {str(e)}") from e

    @staticmethod
    def parse_from_clipboard() -> List['Assessment']:
        """
        Parse assessment(s) from clipboard.

        Auto-detects format (markdown table, TSV, or field-based).
        Similar to how HAM filename tools read from clipboard.

        Returns:
            List of Assessment objects

        Raises:
            OHASParseError: If clipboard is empty or parsing fails

        Example:
            ```python
            # Copy OHAS summary table from browser
            # Then run:
            assessments = OHASParser.parse_from_clipboard()
            for assessment in assessments:
                har = engine.process_assessment(assessment)
                print(har.to_text())
            ```
        """
        try:
            from .table_parser import TableParser
            return TableParser.parse_from_clipboard()
        except Exception as e:
            raise OHASParseError(f"Failed to parse clipboard: {str(e)}") from e
