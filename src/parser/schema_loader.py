"""Schema loader for hazard rules"""

import json
from pathlib import Path
from typing import Optional
from ..models import HazardRulesSchema


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails"""
    pass


class SchemaLoader:
    """
    Load and validate hazard rules schema.

    The schema defines explanations, recommendations, and conditions
    for all earthquake and volcano hazard types.
    """

    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize schema loader.

        Args:
            schema_path: Path to hazard_rules_schema_refined.json
                        If None, uses default path relative to this file
        """
        if schema_path is None:
            # Default: docs/hazard_rules_schema_refined.json
            repo_root = Path(__file__).parent.parent.parent.parent
            schema_path = repo_root / 'docs' / 'hazard_rules_schema_refined.json'

        self.schema_path = Path(schema_path)
        self._schema: Optional[HazardRulesSchema] = None

    def load(self) -> HazardRulesSchema:
        """
        Load schema from JSON file.

        Returns:
            HazardRulesSchema object

        Raises:
            FileNotFoundError: If schema file doesn't exist
            SchemaValidationError: If schema structure is invalid
        """
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}"
            )

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate basic structure
            self._validate_structure(data)

            # Parse into structured objects
            schema = HazardRulesSchema.from_dict(data)

            self._schema = schema
            return schema

        except json.JSONDecodeError as e:
            raise SchemaValidationError(
                f"Invalid JSON in schema file: {str(e)}"
            ) from e
        except Exception as e:
            raise SchemaValidationError(
                f"Error loading schema: {str(e)}"
            ) from e

    def _validate_structure(self, data: dict) -> None:
        """
        Validate that schema has required top-level keys.

        Args:
            data: Parsed JSON data

        Raises:
            SchemaValidationError: If required keys are missing
        """
        required_keys = [
            'metadata',
            'earthquake_rules',
            'volcano_rules',
            'decision_logic',
            'fuzzy_logic_parameters'
        ]

        for key in required_keys:
            if key not in data:
                raise SchemaValidationError(
                    f"Missing required top-level key: '{key}'"
                )

        # Validate earthquake rules have required hazards
        earthquake_hazards = [
            'active_fault',
            'liquefaction',
            'tsunami',
            'earthquake_induced_landslide',
            'fissure'
        ]

        for hazard in earthquake_hazards:
            if hazard not in data['earthquake_rules']:
                raise SchemaValidationError(
                    f"Missing earthquake hazard rule: '{hazard}'"
                )

        # Validate volcano rules have required hazards
        volcano_hazards = [
            'pdz_danger_zone',
            'lava_flow',
            'pyroclastic_density_current',
            'base_surge',
            'ballistic_projectiles',
            'lahar',
            'volcanic_tsunami',
            'fissure',
            'potentially_active_volcano'
        ]

        for hazard in volcano_hazards:
            if hazard not in data['volcano_rules']:
                raise SchemaValidationError(
                    f"Missing volcano hazard rule: '{hazard}'"
                )

    def get_schema(self) -> Optional[HazardRulesSchema]:
        """
        Get loaded schema (if already loaded).

        Returns:
            HazardRulesSchema object or None if not loaded yet
        """
        return self._schema

    def reload(self) -> HazardRulesSchema:
        """
        Reload schema from file.

        Returns:
            HazardRulesSchema object
        """
        return self.load()
