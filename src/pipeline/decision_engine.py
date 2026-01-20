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
        3. check_distance_category → Add distance-based safety if > ~50km or all proximity hazards Safe
        4. assess_pdz_status (if not distance-safe)
        5. assess_lahar (if not distance-safe, with Pinatubo zones and Mayon prone levels)
        6. assess_pyroclastic_flow (if not distance-safe)
        7. assess_lava_flow (if not distance-safe)
        8. assess_ballistic_projectiles (if not distance-safe)
        9. assess_base_surge_if_taal (if not distance-safe and Taal volcano)
        10. assess_volcanic_tsunami (if not distance-safe and assessed)
        11. assess_fissure_if_taal (if not distance-safe and Taal volcano)
        12. check_potentially_active_volcano (future implementation)
        13. add_ashfall_statement (always included)
        14. add_avoidance_recommendation_if_prone (if any proximity hazard is prone)
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

        # 4-10. Process individual hazards (ONLY if not distance-safe)
        if not is_distance_safe:
            # PDZ
            pdz_section = self._process_pdz(assessment, volcano_name)
            if pdz_section:
                sections.append(pdz_section)

            # Lahar
            lahar_section = self._process_lahar(assessment, volcano_name)
            if lahar_section:
                sections.append(lahar_section)

            # Pyroclastic Flow
            pdc_section = self._process_pyroclastic_flow(assessment)
            if pdc_section:
                sections.append(pdc_section)

            # Lava Flow
            lava_section = self._process_lava_flow(assessment)
            if lava_section:
                sections.append(lava_section)

            # Ballistic Projectiles
            ballistic_section = self._process_ballistic_projectiles(assessment)
            if ballistic_section:
                sections.append(ballistic_section)

            # Base Surge (Taal only)
            if "taal" in volcano_name.lower():
                base_surge_section = self._process_base_surge(assessment)
                if base_surge_section:
                    sections.append(base_surge_section)

            # Volcanic Tsunami (if assessed)
            tsunami_section = self._process_volcanic_tsunami(assessment)
            if tsunami_section:
                sections.append(tsunami_section)

            # Fissure (if within 50km)
            fissure_section = self._process_fissure(assessment, volcano_name, distance_km)
            if fissure_section:
                sections.append(fissure_section)

        # 11. PAV (Potentially Active Volcano) - always include if present
        # Official HARs show PAV statements appear even when there's a nearby AV
        # (confirmed by HAS-Jul-24-12496, HAS-Jun-25-14462, etc.)
        if assessment.volcano.nearest_pav and assessment.volcano.nearest_pav != "--":
            pav_statement = self._get_pav_statement(assessment.volcano.nearest_pav)
            common.append(pav_statement)

        # 12. Ashfall (always included)
        ashfall_statement = self._get_ashfall_statement(volcano_name)
        common.append(ashfall_statement)

        # 13. Avoidance recommendation (only if any hazard is prone)
        if not is_distance_safe and self._check_needs_avoidance(assessment):
            avoidance = self._get_avoidance_recommendation()
            common.append(avoidance)

        # 14. Supersedes
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

    def _process_pdz(self, assessment: Assessment, volcano_name: str) -> Optional[HARSection]:
        """
        Process Permanent Danger Zone assessments.

        Args:
            assessment: Assessment with volcano data
            volcano_name: Name of volcano (case-insensitive)

        Returns:
            HARSection for PDZ or None if not applicable
        """
        try:
            # Get PDZ rule from schema
            rule = self.schema.volcano_rules.get('pdz_danger_zone')
            if not rule:
                return None

            # Case-insensitive volcano name matching
            volcano_lower = volcano_name.lower()

            # Check for special cases in schema
            special_cases = rule.special_cases or {}

            # Get radius from special cases or return None
            radius_km = None
            volcano_config = None

            for volcano_key in special_cases:
                if volcano_key.lower() in volcano_lower or volcano_lower in volcano_key.lower():
                    volcano_config = special_cases[volcano_key]
                    # Handle Taal special case (no radius, just explanation)
                    if volcano_key.lower() == 'taal':
                        # Taal uses special explanation
                        if isinstance(volcano_config, dict):
                            explanation = volcano_config.get('explanation')
                            if explanation:
                                # For Taal, we need to check if site is on Volcano Island
                                # This would be in the assessment status, but not always available
                                # Return None for now - Taal PDZ handling needs assessment status
                                return None
                    else:
                        # Other volcanoes might have radius_km
                        if isinstance(volcano_config, dict):
                            radius_km = volcano_config.get('radius_km')
                    break

            # If no special case found, return None (general PDZ not in schema)
            if radius_km is None:
                return None

            # Get distance to volcano
            volcano_info = self._parse_nearest_volcano(assessment)
            distance_km = volcano_info.get('distance', 0.0)

            # Determine if inside or outside PDZ
            if distance_km < radius_km:
                # Inside PDZ
                status = f"Within PDZ; The site is within the {int(radius_km)}-kilometer radius Permanent Danger Zone"

                # Get explanation and recommendation from schema
                explanation = rule.explanation or ''
                recommendation = rule.recommendation or ''

                # Replace placeholders
                explanation = explanation.replace('{volcano_name}', volcano_name)
                explanation = explanation.replace('{radius}', str(int(radius_km)))

                exp_rec = ExplanationRecommendation.from_parts(
                    explanation=explanation,
                    recommendation=recommendation
                )
            else:
                # Outside PDZ
                status = f"Outside PDZ; The site is outside the {int(radius_km)}-kilometer radius Permanent Danger Zone"

                # For sites outside PDZ, use simpler explanation
                explanation = f"The Permanent Danger Zone (PDZ) is a zone that can always be affected by small-scale eruptions of {volcano_name} Volcano. Human settlement is not recommended within the PDZ."
                recommendation = f"The site is outside the {int(radius_km)}-kilometer radius Permanent Danger Zone of the volcano."

                exp_rec = ExplanationRecommendation.from_parts(
                    explanation=explanation + " " + recommendation
                )

            return HARSection(
                heading="PDZ (Permanent Danger Zone)",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation on missing schema keys
            return None

    def _process_lahar(self, assessment: Assessment, volcano_name: str) -> Optional[HARSection]:
        """
        Process Lahar assessments with Pinatubo zones and Mayon prone levels.

        Args:
            assessment: Assessment with volcano data
            volcano_name: Name of volcano (case-insensitive)

        Returns:
            HARSection for Lahar or None if not applicable
        """
        try:
            # Extract status from assessment
            status = assessment.volcano.lahar
            if not status or status == "--":
                return None

            # Return None if status is "Safe"
            if "Safe" in status:
                return None

            # Get lahar rule from schema
            rule = self.schema.volcano_rules.get('lahar')
            if not rule:
                return None

            # Case-insensitive volcano matching
            volcano_lower = volcano_name.lower()

            # Get base explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            # Check for special cases
            special_cases = rule.special_cases or {}

            # Pinatubo special case - 5 zones
            if 'pinatubo' in volcano_lower:
                pinatubo_config = special_cases.get('pinatubo')
                if pinatubo_config and isinstance(pinatubo_config, dict):
                    # Add intro for Pinatubo
                    intro = pinatubo_config.get('intro', '')

                    # Extract zone number from status
                    zone_match = re.search(r'Zone\s+([1-5])', status, re.IGNORECASE)
                    if zone_match:
                        zone_num = zone_match.group(1)
                        zones = pinatubo_config.get('zones', {})
                        zone_config = zones.get(f'zone_{zone_num}')

                        if zone_config and isinstance(zone_config, dict):
                            # Get zone-specific explanation
                            zone_explanation = zone_config.get('explanation', '')
                            # Combine intro + zone explanation
                            if intro and zone_explanation:
                                explanation = f"{intro} {zone_explanation}"

            # Mayon special case - prone levels
            elif 'mayon' in volcano_lower:
                mayon_config = special_cases.get('mayon')
                if mayon_config and isinstance(mayon_config, dict):
                    # Add intro for Mayon
                    intro = mayon_config.get('intro', '')

                    # Map status to prone level
                    zones = mayon_config.get('zones', {})

                    if 'Highly Prone' in status:
                        zone_config = zones.get('highly_prone')
                    elif 'Moderately Prone' in status:
                        zone_config = zones.get('moderately_prone')
                    elif 'Least Prone' in status:
                        zone_config = zones.get('least_prone')
                    else:
                        zone_config = None

                    if zone_config and isinstance(zone_config, dict):
                        # Get zone-specific explanation
                        zone_explanation = zone_config.get('explanation', '')
                        if intro and zone_explanation:
                            explanation = f"{intro} {zone_explanation}"

            # General case - use standard explanation/recommendation
            # (already loaded above)

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Lahar",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_pyroclastic_flow(self, assessment: Assessment) -> Optional[HARSection]:
        """
        Process Pyroclastic Flow (PDC) assessments.

        Args:
            assessment: Assessment with volcano data

        Returns:
            HARSection for PDC or None if not applicable
        """
        try:
            # Extract status - check multiple possible field names
            status = assessment.volcano.pyroclastic_flow
            if not status or status == "--":
                return None

            # Return None if status is "Safe"
            if "Safe" in status:
                return None

            # Get PDC rule from schema
            rule = self.schema.volcano_rules.get('pyroclastic_density_current')
            if not rule:
                return None

            # Get explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Pyroclastic Density Current",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_lava_flow(self, assessment: Assessment) -> Optional[HARSection]:
        """
        Process lava flow hazard assessment.

        Args:
            assessment: Volcano assessment data

        Returns:
            HARSection for lava flow or None if not assessed
        """
        try:
            # Extract status from assessment
            status = assessment.volcano.lava_flow
            if not status or status == "--":
                return None

            # Skip if Safe
            if "safe" in status.lower():
                return None

            # Get lava flow rule from schema
            rule = self.schema.volcano_rules.get('lava_flow')
            if not rule:
                return None

            # Get explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Lava Flow",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_ballistic_projectiles(self, assessment: Assessment) -> Optional[HARSection]:
        """
        Process ballistic projectiles hazard assessment.

        Args:
            assessment: Volcano assessment data

        Returns:
            HARSection for ballistic projectiles or None if not assessed
        """
        try:
            # Extract status from assessment
            status = assessment.volcano.ballistic_projectile
            if not status or status == "--":
                return None

            # Skip if Safe
            if "safe" in status.lower():
                return None

            # Get ballistic projectiles rule from schema
            rule = self.schema.volcano_rules.get('ballistic_projectiles')
            if not rule:
                return None

            # Get explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Ballistic Projectiles",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_base_surge(self, assessment: Assessment) -> Optional[HARSection]:
        """
        Process base surge hazard assessment (Taal-specific).

        Args:
            assessment: Volcano assessment data

        Returns:
            HARSection for base surge or None if not assessed
        """
        try:
            # Extract status from assessment
            status = assessment.volcano.base_surge
            if not status or status == "--":
                return None

            # Skip if Safe
            if "safe" in status.lower():
                return None

            # Get base surge rule from schema
            rule = self.schema.volcano_rules.get('base_surge')
            if not rule:
                return None

            # Get explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Base Surge",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_volcanic_tsunami(self, assessment: Assessment) -> Optional[HARSection]:
        """
        Process volcanic tsunami assessment.

        Volcanic tsunamis can be generated by pyroclastic flows,
        debris avalanches, or caldera collapse entering bodies of water.

        Args:
            assessment: Volcano assessment data

        Returns:
            HARSection for volcanic tsunami or None if not assessed
        """
        try:
            # Check if field exists in assessment
            status = assessment.volcano.volcanic_tsunami
            if not status or status == "--":
                return None

            # Skip if Safe
            if "safe" in status.lower():
                return None

            # Get volcanic tsunami rule from schema
            rule = self.schema.volcano_rules.get('volcanic_tsunami')
            if not rule:
                return None

            # Get explanation and recommendation
            explanation = rule.explanation
            recommendation = rule.recommendation

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Volcanic Tsunami",
                assessment=status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _process_fissure(self, assessment: Assessment, volcano_name: str, distance_km: float) -> Optional[HARSection]:
        """
        Process volcanic fissure assessment.

        Fissures can be assessed for ANY volcano if site is < ~50km or within watershed.
        Taal has special case with municipality-specific rules and additional reporting.

        TODO: Municipality-specific handling requires extending Assessment model
        with location text/municipality field. Current implementation processes
        all fissure assessments based on volcano proximity.

        Args:
            assessment: Volcano assessment data
            volcano_name: Name of volcano
            distance_km: Distance to volcano in km

        Returns:
            HARSection for fissure or None if not assessed
        """
        try:
            # Only assess fissures if site is < 50km or within watershed
            # (watershed determination would need additional data)
            if distance_km > 50.0:
                return None

            # Extract fissure status
            fissure_status = assessment.volcano.fissure

            if not fissure_status or fissure_status == "--":
                return None

            # Get fissure rule from schema
            rule = self.schema.volcano_rules.get('fissure')
            if not rule:
                return None

            # Build explanation from schema parts
            explanation_parts = []

            # Main explanation (applies to all volcanoes)
            if rule.explanation:
                explanation_parts.append(rule.explanation)

            # Development info
            if rule.development:
                explanation_parts.append(rule.development)

            # Combine explanation
            explanation = " ".join(explanation_parts) if explanation_parts else ""

            # Get recommendation (applies to all volcanoes)
            recommendation = rule.recommendation or ""

            # Add Taal-specific reporting if applicable
            volcano_lower = volcano_name.lower()
            if "taal" in volcano_lower:
                special_cases = rule.special_cases or {}
                taal_config = special_cases.get('taal', {})
                reporting = taal_config.get('reporting', '')
                if reporting:
                    recommendation += f" {reporting}"

            if not explanation:
                return None

            # Create ExplanationRecommendation
            exp_rec = ExplanationRecommendation.from_parts(
                explanation=explanation,
                recommendation=recommendation
            )

            return HARSection(
                heading="Fissure",
                assessment=fissure_status,
                explanation_recommendation=exp_rec
            )

        except (KeyError, AttributeError, TypeError):
            # Graceful degradation
            return None

    def _check_needs_avoidance(self, assessment: Assessment) -> bool:
        """
        Determine if avoidance recommendation is needed.

        Returns True if ANY proximity hazard is prone/within hazardous zones.

        Args:
            assessment: Assessment with volcano data

        Returns:
            True if avoidance recommendation should be included
        """
        try:
            volcano = assessment.volcano

            # Check PDZ - not in current assessment fields, skip for now

            # Check Lahar
            if volcano.lahar:
                status = volcano.lahar.lower()
                if 'prone' in status or 'susceptible' in status:
                    if 'safe' not in status:  # Exclude "Safe" statuses
                        return True

            # Check Pyroclastic Flow
            if volcano.pyroclastic_flow:
                status = volcano.pyroclastic_flow.lower()
                if 'prone' in status or 'susceptible' in status or 'within' in status:
                    if 'safe' not in status:
                        return True

            # Check Lava Flow
            if volcano.lava_flow:
                status = volcano.lava_flow.lower()
                if 'prone' in status or 'within' in status:
                    if 'safe' not in status:
                        return True

            # Check Ballistic Projectiles
            if volcano.ballistic_projectile:
                status = volcano.ballistic_projectile.lower()
                if 'prone' in status or 'within' in status:
                    if 'safe' not in status:
                        return True

            return False

        except (AttributeError, TypeError):
            # Graceful degradation
            return False

    def _get_avoidance_recommendation(self) -> ExplanationRecommendation:
        """
        Get avoidance recommendation for prone volcanic hazards.

        Returns:
            ExplanationRecommendation with avoidance text from schema
        """
        try:
            # Get from schema - based on schema, avoidance is in individual hazard rules
            # Use standard avoidance text for PDC and lava flows

            # Get from pyroclastic_density_current rule as it has the avoidance text
            pdc_rule = self.schema.volcano_rules.get('pyroclastic_density_current')
            if pdc_rule and pdc_rule.recommendation:
                return ExplanationRecommendation.from_parts(
                    recommendation=pdc_rule.recommendation
                )

            # Fallback to generic avoidance
            text = (
                "Avoidance is recommended for site/sites that may potentially be affected by "
                "pyroclastic density currents (PDCs) and lava flows."
            )
            return ExplanationRecommendation.from_parts(
                recommendation=text
            )

        except (KeyError, AttributeError, TypeError):
            # Fallback
            text = (
                "Avoidance is recommended for site/sites that may potentially be affected by "
                "pyroclastic density currents (PDCs) and lava flows."
            )
            return ExplanationRecommendation.from_parts(
                recommendation=text
            )

    def _check_distance_based_safety(self, assessment: Assessment, distance_km: float) -> bool:
        """
        Check if site is safe from proximity hazards based on distance.

        Distance-based safety statement is shown when site is > ~50-60km from volcano.
        This is independent of hazard statuses - even if some hazards (like lahar)
        are Prone, the distance-based statement still appears for proximity hazards
        (PDC, lava flows, ballistic projectiles).

        Evidence: HAS-Apr-25-14786 has distance-based safety at 64.4km even though
        Lahar status is "Prone".

        Args:
            assessment: Volcano assessment data (unused, kept for compatibility)
            distance_km: Distance to nearest volcano in km

        Returns:
            True if distance-based safety statement should be included
        """
        # Threshold is approximately 50-60km based on official HARs
        # Using 50km as conservative threshold
        if distance_km > 50.0:
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

    def _get_pav_statement(self, pav_text: str) -> ExplanationRecommendation:
        """
        Get PAV (Potentially Active Volcano) statement for common statements section.

        PAV statements are always included when a PAV is present, regardless of
        whether there's also a nearby active volcano. This is confirmed by official
        HARs (HAS-Jul-24-12496, HAS-Jun-25-14462, etc.) which include both AV and
        PAV statements.

        Args:
            pav_text: Text from assessment.volcano.nearest_pav
                      Format: "Approximately X kilometers [direction] of [Volcano Name] Volcano"

        Returns:
            ExplanationRecommendation for PAV
        """
        # Extract volcano name from text
        # Format: "Approximately 15.8 kilometers northeast of Labo Volcano"
        volcano_name = "Unknown"
        if "of " in pav_text and "Volcano" in pav_text:
            parts = pav_text.split("of ")[-1]  # Get part after "of "
            volcano_name = parts.split(" Volcano")[0].strip()

        # Standard PAV explanation (exact wording from official HARs)
        explanation = (
            f"{volcano_name} Volcano is currently classified by DOST-PHIVOLCS as a "
            f"potentially active volcano, which is morphologically young-looking but with "
            f"no historical or analytical records of eruption, therefore, its eruptive and "
            f"hazard potential is yet to be determined."
        )

        return ExplanationRecommendation.from_parts(explanation=explanation)

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
