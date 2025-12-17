"""Decision engine for HAR generation"""

import re
from typing import List, Optional
from ..models import (
    Assessment,
    AssessmentCategory,
    HazardRulesSchema,
    HARSection,
    HAROutput,
    ExplanationRecommendation,
)
from .condition_matcher import ConditionMatcher


class DecisionEngine:
    """
    Core decision engine for generating HAR content.

    Applies decision logic workflow to match assessment statuses
    to appropriate explanations and recommendations from the schema.
    """

    def __init__(self, schema: HazardRulesSchema):
        """
        Initialize decision engine.

        Args:
            schema: Loaded hazard rules schema
        """
        self.schema = schema
        self.matcher = ConditionMatcher()

    def process_assessment(self, assessment: Assessment) -> HAROutput:
        """
        Process assessment and generate HAR output.

        Args:
            assessment: Assessment data from OHAS

        Returns:
            HAROutput with all sections and statements

        Raises:
            ValueError: If assessment category is invalid or data is missing
        """
        if assessment.category == AssessmentCategory.EARTHQUAKE:
            return self.process_earthquake_assessment(assessment)
        elif assessment.category == AssessmentCategory.VOLCANO:
            return self.process_volcano_assessment(assessment)
        else:
            raise ValueError(f"Unknown assessment category: {assessment.category}")

    def process_earthquake_assessment(self, assessment: Assessment) -> HAROutput:
        """
        Process earthquake assessment following decision workflow.

        Workflow:
        1. check_map_availability
        2. assess_active_fault_distance
        3. assess_fissure_proximity_if_applicable
        4. assess_liquefaction
        5. assess_earthquake_induced_landslide
        6. assess_tsunami_if_coastal
        7. add_ground_shaking_statement
        8. add_mitigation_statement
        9. add_supersedes_statement

        Args:
            assessment: Earthquake assessment data

        Returns:
            HAROutput for earthquake hazards
        """
        if not assessment.has_earthquake_assessment():
            raise ValueError("Assessment missing earthquake data")

        sections: List[HARSection] = []

        # 1. Intro statement
        intro = self._get_intro_statement(assessment)

        # 2. Active Fault
        if assessment.earthquake.is_assessed('active_fault'):
            section = self._process_active_fault(assessment)
            sections.append(section)

        # 3. Fissure (only if within buffer zone or transected by fault)
        # TODO: Implement fissure assessment based on active fault distance

        # 4. Liquefaction
        if assessment.earthquake.is_assessed('liquefaction'):
            section = self._process_liquefaction(assessment)
            sections.append(section)

        # 5. Earthquake-Induced Landslide
        if assessment.earthquake.is_assessed('landslide'):
            section = self._process_eil(assessment)
            sections.append(section)

        # 6. Tsunami
        if assessment.earthquake.is_assessed('tsunami'):
            section = self._process_tsunami(assessment)
            sections.append(section)

        # 7-8. Common statements (Ground Shaking + Mitigation)
        common = self._get_common_earthquake_statements()

        # 9. Supersedes statement
        supersedes = self._get_supersedes_statement(single_site=True)

        # Additional recommendations
        additional = self._get_additional_recommendations()

        return HAROutput(
            category=AssessmentCategory.EARTHQUAKE,
            intro=intro,
            sections=sections,
            common_statements=common,
            supersedes=supersedes,
            additional_recommendations=additional
        )

    def process_volcano_assessment(self, assessment: Assessment) -> HAROutput:
        """
        Process volcano assessment following decision workflow.

        Workflow:
        1. check_map_availability
        2. identify_nearest_active_volcano → Add "X Volcano is the nearest identified active volcano"
        3. check_distance_category → Add distance-based safety if > ~50km
        4. assess_pdz_status
        5. assess_lava_flow
        6. assess_pyroclastic_flow
        7. assess_lahar
        8. assess_ballistic_projectiles_if_applicable
        9. assess_base_surge_if_taal
        10. assess_volcanic_tsunami_if_applicable
        11. assess_fissure_if_taal_area
        12. check_potentially_active_volcano
        13. add_ashfall_statement
        14. add_avoidance_recommendation_if_prone
        15. add_supersedes_statement

        Args:
            assessment: Volcano assessment data

        Returns:
            HAROutput for volcano hazards
        """
        if not assessment.has_volcano_assessment():
            raise ValueError("Assessment missing volcano data")

        sections: List[HARSection] = []
        common: List[ExplanationRecommendation] = []

        # 1. Intro statement
        intro = self._get_intro_statement(assessment)

        # 2. Parse volcano information and add nearest volcano statement
        volcano_info = self._parse_nearest_volcano(assessment)
        volcano_name = volcano_info.get('name', 'Unknown')
        distance_km = volcano_info.get('distance', 0.0)

        # Add "Biliran Volcano is the nearest identified active volcano to the site."
        if volcano_name != 'Unknown':
            nearest_statement = ExplanationRecommendation.from_parts(
                explanation=f"{volcano_name} Volcano is the nearest identified active volcano to the site."
            )
            common.append(nearest_statement)

        # 3. Distance-based safety statement
        # Check if site is safe from proximity hazards based on distance or hazard statuses
        is_distance_safe = self._check_distance_based_safety(assessment, distance_km)

        if is_distance_safe:
            safety_statement = ExplanationRecommendation.from_parts(
                explanation=(
                    f"Considering the distance of the site from the volcano, the site is safe from "
                    f"volcanic hazards such as pyroclastic density currents, lava flows, and ballistic "
                    f"projectiles that may originate from the volcano."
                )
            )
            common.append(safety_statement)

        # 4-11. Process individual hazards (simplified for now)
        # TODO: Implement individual hazard processing

        # 12. PAV (Potentially Active Volcano) - only if no nearby active volcano
        # Skip PAV if we already have a nearby active volcano
        # Real HARs prioritize nearest AV over distant PAV

        # 13. Ashfall (always included)
        ashfall_statement = self._get_ashfall_statement(volcano_name)
        common.append(ashfall_statement)

        # 14. Avoidance recommendation (only if any hazard is prone)
        # TODO: Check if any hazard is prone

        # 15. Supersedes
        supersedes = self._get_supersedes_statement(single_site=True)

        # Additional recommendations
        additional = self._get_additional_recommendations()

        return HAROutput(
            category=AssessmentCategory.VOLCANO,
            intro=intro,
            sections=sections,
            common_statements=common,
            supersedes=supersedes,
            additional_recommendations=additional
        )

    def _get_intro_statement(self, assessment: Assessment) -> str:
        """
        Generate intro statement based on vicinity map availability.

        Includes standard opening: "All hazard assessments are based on..."

        Args:
            assessment: Assessment data

        Returns:
            Intro statement text (multi-line)
        """
        # Standard opening (always included)
        intro = "All hazard assessments are based on the latest available hazard maps and on the location indicated "

        # Vary based on vicinity map availability
        if assessment.vicinity_map_provided:
            intro += "in the vicinity map provided."
        else:
            intro += "by the coordinates provided."

        return intro

    def _process_active_fault(self, assessment: Assessment) -> HARSection:
        """
        Process Active Fault assessment.

        Args:
            assessment: Assessment with active fault data

        Returns:
            HARSection for ground rupture
        """
        status = assessment.earthquake.active_fault
        rule = self.schema.earthquake_rules['active_fault']

        # Get explanation and recommendation from schema
        explanation = rule.explanation
        recommendation = rule.recommendation

        # Combine as paired unit
        exp_rec = ExplanationRecommendation.from_parts(
            explanation=explanation,
            recommendation=recommendation
        )

        return HARSection(
            heading="Ground Rupture",
            assessment=status,
            explanation_recommendation=exp_rec
        )

    def _process_liquefaction(self, assessment: Assessment) -> HARSection:
        """
        Process Liquefaction assessment.

        Note: Liquefaction explanation/recommendation is combined with
        Ground Shaking in actual HARs as a single numbered point.

        Args:
            assessment: Assessment with liquefaction data

        Returns:
            HARSection for liquefaction
        """
        status = assessment.earthquake.liquefaction
        rule = self.schema.earthquake_rules['liquefaction']

        # Liquefaction only has recommendation (no separate explanation)
        recommendation = rule.recommendation

        exp_rec = ExplanationRecommendation.from_parts(
            recommendation=recommendation
        )

        return HARSection(
            heading="Ground Shaking and Liquefaction",
            assessment=f"All sites may be affected by strong ground shaking. {status}",
            explanation_recommendation=exp_rec
        )

    def _process_eil(self, assessment: Assessment) -> HARSection:
        """
        Process Earthquake-Induced Landslide assessment.

        Args:
            assessment: Assessment with landslide data

        Returns:
            HARSection for EIL
        """
        status = assessment.earthquake.landslide
        rule = self.schema.earthquake_rules['earthquake_induced_landslide']

        # Match status to condition
        condition_key = self.matcher.match_landslide(status)

        # Get explanation and recommendation
        explanation = rule.explanation
        recommendation = rule.recommendation

        exp_rec = ExplanationRecommendation.from_parts(
            explanation=explanation,
            recommendation=recommendation
        )

        return HARSection(
            heading="Earthquake-Induced Landslide",
            assessment=status,
            explanation_recommendation=exp_rec
        )

    def _process_tsunami(self, assessment: Assessment) -> HARSection:
        """
        Process Tsunami assessment.

        Args:
            assessment: Assessment with tsunami data

        Returns:
            HARSection for tsunami
        """
        status = assessment.earthquake.tsunami
        rule = self.schema.earthquake_rules['tsunami']

        # Get explanation and recommendation
        explanation = rule.explanation
        recommendation = rule.recommendation

        exp_rec = ExplanationRecommendation.from_parts(
            explanation=explanation,
            recommendation=recommendation
        )

        return HARSection(
            heading="Tsunami",
            assessment=status,
            explanation_recommendation=exp_rec
        )

    def _get_common_earthquake_statements(self) -> List[ExplanationRecommendation]:
        """
        Get common statements for earthquake assessments.

        Returns:
            List containing ground shaking statement
        """
        # Ground shaking is already combined with liquefaction
        # So no separate common statement needed
        return []

    def _parse_nearest_volcano(self, assessment: Assessment) -> dict:
        """
        Parse nearest volcano information.

        Formats:
        - "Approximately 58.3 km north of Taal Volcano"
        - "Approximately 67.7 kilometers east of Biliran Volcano"

        Args:
            assessment: Volcano assessment

        Returns:
            Dictionary with distance, direction, and volcano name
        """
        text = assessment.volcano.nearest_active_volcano
        # Accept both "km" and "kilometers"
        pattern = r"Approximately\s+([\d.]+)\s*(?:km|kilometers)\s+(\w+)\s+of\s+(.+?)\s+Volcano"
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return {
                'distance': float(match.group(1)),
                'direction': match.group(2),
                'name': match.group(3)
            }
        else:
            # Fallback parsing
            return {
                'distance': 0.0,
                'direction': 'unknown',
                'name': 'Unknown Volcano'
            }

    def _check_distance_based_safety(self, assessment: Assessment, distance_km: float) -> bool:
        """
        Check if site is safe from proximity hazards based on distance or hazard statuses.

        Distance-based safety statement is shown when:
        1. Site is far from volcano (> ~50km), OR
        2. All proximity hazards (PDC, lava flow, ballistic) are "Safe"

        Args:
            assessment: Volcano assessment data
            distance_km: Distance to nearest volcano in km

        Returns:
            True if distance-based safety statement should be included
        """
        # Check distance threshold (50km is typical safe distance)
        if distance_km > 50.0:
            return True

        # Check if all proximity hazards are "Safe"
        proximity_hazards = []

        if assessment.volcano.pyroclastic_flow:
            proximity_hazards.append(assessment.volcano.pyroclastic_flow)
        if assessment.volcano.lava_flow:
            proximity_hazards.append(assessment.volcano.lava_flow)
        if assessment.volcano.ballistic_projectile:
            proximity_hazards.append(assessment.volcano.ballistic_projectile)

        # All must be "Safe" for distance-based safety statement
        if proximity_hazards and all('Safe' in h for h in proximity_hazards):
            return True

        return False

    def _get_distance_safe_section(self, volcano_name: str) -> HARSection:
        """
        Get distance-based safety section for volcanoes > 50km away.

        Args:
            volcano_name: Name of volcano

        Returns:
            HARSection for distance-based safety
        """
        rule = self.schema.volcano_rules.get('distance_rules', {})

        # Get the safe statement
        safe_statement = (
            "Considering the distance of the site/s from the volcano, "
            "the site/s is/are safe from volcanic hazards such as "
            "pyroclastic density currents, lava flows, and ballistic "
            "projectiles that may originate from the volcano."
        )

        exp_rec = ExplanationRecommendation.from_parts(
            explanation=safe_statement
        )

        return HARSection(
            heading="Proximity Hazards",
            assessment=f"Safe (> 50 km from {volcano_name} Volcano)",
            explanation_recommendation=exp_rec
        )

    def _process_pav(self, assessment: Assessment) -> HARSection:
        """
        Process Potentially Active Volcano statement.

        Args:
            assessment: Assessment with PAV data

        Returns:
            HARSection for PAV
        """
        pav_text = assessment.volcano.nearest_pav

        # Extract volcano name from text if possible
        # Format: "Corregidor Volcano is currently classified as potentially active volcano"
        volcano_name = "Unknown"
        if "Volcano" in pav_text:
            parts = pav_text.split("Volcano")
            if parts:
                volcano_name = parts[0].strip()

        exp_rec = ExplanationRecommendation.from_parts(
            explanation=pav_text
        )

        return HARSection(
            heading="Potentially Active Volcano",
            assessment=f"{volcano_name} Volcano - Potentially Active",
            explanation_recommendation=exp_rec
        )

    def _get_ashfall_statement(self, volcano_name: str) -> ExplanationRecommendation:
        """
        Get ashfall statement (always included for volcano assessments).

        Args:
            volcano_name: Name of volcano

        Returns:
            ExplanationRecommendation for ashfall
        """
        # Ashfall is in common rule's special_cases (stored as raw dict)
        common_rule = self.schema.volcano_rules.get('common')
        if common_rule and common_rule.special_cases:
            ashfall_data = common_rule.special_cases.get('ashfall', {})
            ashfall_template = ashfall_data.get('template', '')
        else:
            # Fallback generic ashfall statement
            ashfall_template = (
                "In case of future eruptions of {volcano_name} Volcano and other nearby volcanoes, "
                "the site/s may be affected by tephra fall/ ashfall depending on the height of the eruption plume "
                "and prevailing wind direction at the time of eruption."
            )

        # Substitute volcano name
        explanation = ashfall_template.replace('{volcano_name}', volcano_name)

        return ExplanationRecommendation.from_parts(
            explanation=explanation
        )

    def _get_supersedes_statement(self, single_site: bool = True) -> str:
        """
        Get supersedes statement.

        Args:
            single_site: True if single site, False if multiple sites

        Returns:
            Supersedes statement text
        """
        if single_site:
            return (
                "This assessment supersedes all previous reports "
                "issued for this site."
            )
        else:
            return (
                "This assessment supersedes all previous reports "
                "issued for these sites."
            )

    def _get_additional_recommendations(self) -> List[str]:
        """
        Get additional recommendations (HazardHunterPH, GeoAnalyticsPH).

        Returns:
            List of additional recommendation texts
        """
        return [
            (
                "For more information on geohazards in the Philippines, "
                "please visit HazardHunterPH (https://hazardhunter.georisk.gov.ph/) "
                "and GeoAnalyticsPH (https://geoanalytics.georisk.gov.ph/)."
            )
        ]
