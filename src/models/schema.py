"""Schema data models for hazard rules"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class HazardCondition:
    """Condition template for a specific hazard status"""
    template: str
    notes: Optional[str] = None
    threshold_km: Optional[float] = None
    threshold_m: Optional[float] = None
    # Store any additional fields as a dict
    extras: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Convert extras to dict if needed"""
        if not isinstance(self.extras, dict):
            self.extras = {}


@dataclass
class HazardRule:
    """Rule definition for a hazard type"""
    name: str
    explanation: Optional[str] = None
    explanation_alt: Optional[str] = None
    recommendation: Optional[str] = None
    recommendation_alt: Optional[str] = None
    conditions: Dict[str, HazardCondition] = field(default_factory=dict)
    special_cases: Optional[Dict[str, Any]] = None
    applies_to: Optional[List[str]] = None

    def has_explanation(self) -> bool:
        """Check if rule has an explanation"""
        return self.explanation is not None

    def has_recommendation(self) -> bool:
        """Check if rule has a recommendation"""
        return self.recommendation is not None


@dataclass
class HazardRulesSchema:
    """Complete hazard rules schema"""
    metadata: Dict[str, str]
    earthquake_rules: Dict[str, HazardRule]
    volcano_rules: Dict[str, HazardRule]
    decision_logic: Dict[str, List[str]]
    fuzzy_logic_parameters: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict) -> 'HazardRulesSchema':
        """
        Load schema from dictionary (parsed JSON)

        Args:
            data: Dictionary containing schema data

        Returns:
            HazardRulesSchema instance
        """
        # Parse earthquake rules
        earthquake_rules = {}
        for hazard_key, rule_data in data.get('earthquake_rules', {}).items():
            # Skip if not a dict
            if not isinstance(rule_data, dict):
                continue

            conditions = {}
            for cond_key, cond_data in rule_data.get('conditions', {}).items():
                if isinstance(cond_data, dict):
                    # Extract known fields
                    known_fields = {
                        'template': cond_data.get('template', ''),
                        'notes': cond_data.get('notes'),
                        'threshold_km': cond_data.get('threshold_km'),
                        'threshold_m': cond_data.get('threshold_m'),
                    }
                    # Put unknown fields in extras
                    extras = {k: v for k, v in cond_data.items()
                             if k not in ['template', 'notes', 'threshold_km', 'threshold_m']}
                    known_fields['extras'] = extras
                    conditions[cond_key] = HazardCondition(**known_fields)

            # Name is optional
            name = rule_data.get('name', hazard_key.replace('_', ' ').title())

            earthquake_rules[hazard_key] = HazardRule(
                name=name,
                explanation=rule_data.get('explanation'),
                explanation_alt=rule_data.get('explanation_alt'),
                recommendation=rule_data.get('recommendation'),
                recommendation_alt=rule_data.get('recommendation_alt'),
                conditions=conditions,
                special_cases=rule_data.get('special_cases'),
                applies_to=rule_data.get('applies_to')
            )

        # Parse volcano rules
        volcano_rules = {}
        for hazard_key, rule_data in data.get('volcano_rules', {}).items():
            # Skip if not a dict (shouldn't happen, but be safe)
            if not isinstance(rule_data, dict):
                continue

            conditions = {}
            for cond_key, cond_data in rule_data.get('conditions', {}).items():
                if isinstance(cond_data, dict):
                    # Extract known fields
                    known_fields = {
                        'template': cond_data.get('template', ''),
                        'notes': cond_data.get('notes'),
                        'threshold_km': cond_data.get('threshold_km'),
                        'threshold_m': cond_data.get('threshold_m'),
                    }
                    # Put unknown fields in extras
                    extras = {k: v for k, v in cond_data.items()
                             if k not in ['template', 'notes', 'threshold_km', 'threshold_m']}
                    known_fields['extras'] = extras
                    conditions[cond_key] = HazardCondition(**known_fields)

            # Name is optional for special structures like 'common', 'distance_rules'
            name = rule_data.get('name', hazard_key.replace('_', ' ').title())

            # For special structures without standard fields, store entire dict as special_cases
            special_cases = rule_data.get('special_cases')
            if not rule_data.get('explanation') and not rule_data.get('recommendation') and not special_cases:
                # This is a special structure (like 'common'), store the whole thing
                special_cases = rule_data

            volcano_rules[hazard_key] = HazardRule(
                name=name,
                explanation=rule_data.get('explanation'),
                explanation_alt=rule_data.get('explanation_alt'),
                recommendation=rule_data.get('recommendation'),
                recommendation_alt=rule_data.get('recommendation_alt'),
                conditions=conditions,
                special_cases=special_cases,
                applies_to=rule_data.get('applies_to')
            )

        return cls(
            metadata=data.get('metadata', {}),
            earthquake_rules=earthquake_rules,
            volcano_rules=volcano_rules,
            decision_logic=data.get('decision_logic', {}),
            fuzzy_logic_parameters=data.get('fuzzy_logic_parameters', {})
        )
