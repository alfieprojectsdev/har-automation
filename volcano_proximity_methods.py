"""
Volcano proximity-hazard processing methods for decision_engine.py

Add these methods to the DecisionEngine class in src/pipeline/decision_engine.py
Insert after line 484 (after _get_ashfall_statement method)
"""

import re
from typing import Optional


# ============================================================================
# VOLCANO HAZARD PROCESSING METHODS
# ============================================================================

def _process_pdz(self, assessment: Assessment, volcano_name: str) -> Optional[HARSection]:
    """
    Process PDZ (Permanent Danger Zone) assessment.
    
    PDZ is a zone that can always be affected by small-scale eruptions.
    Different volcanoes have different PDZ radii:
    - Taal: 4km radius
    - Kanlaon: 4km radius  
    - Mayon: 6km radius
    - Pinatubo: Variable based on activity
    
    Args:
        assessment: Volcano assessment data
        volcano_name: Name of volcano
        
    Returns:
        HARSection for PDZ or None if not applicable
    """
    # Check if volcano has PDZ in assessment data
    # Note: OHAS doesn't have a separate PDZ column currently,
    # so we check proximity and infer from other hazard statuses
    
    rule = self.schema.volcano_rules.get('pdz_danger_zone')
    if not rule:
        return None
    
    # Extract distance from nearest volcano text
    distance_km = self._parse_nearest_volcano(assessment).get('distance', 0.0)
    volcano_lower = volcano_name.lower()
    
    # Define PDZ radii for known volcanoes
    pdz_radii = {
        'taal': 4.0,
        'kanlaon': 4.0,
        'mayon': 6.0,
        'pinatubo': 4.0,
        'bulusan': 4.0,
        'hibok-hibok': 4.0
    }
    
    # Check if this volcano has a PDZ
    pdz_radius = None
    for volcano_key, radius in pdz_radii.items():
        if volcano_key in volcano_lower:
            pdz_radius = radius
            break
    
    if pdz_radius is None:
        return None  # No PDZ for this volcano
    
    # Determine status based on distance
    if distance_km < pdz_radius:
        status = f"Within PDZ; The site is within the {pdz_radius}-kilometer radius Permanent Danger Zone"
        condition_key = "within_pdz"
    else:
        status = f"Outside PDZ; The site is outside the {pdz_radius}-kilometer radius Permanent Danger Zone"
        condition_key = "outside_pdz"
    
    # Get explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    # For sites outside PDZ, use simpler recommendation
    if condition_key == "outside_pdz":
        explanation = f"The Permanent Danger Zone (PDZ) is a zone that can always be affected by small-scale eruptions of {volcano_name} Volcano. Human settlement is not recommended within the PDZ."
        recommendation = f"The site is outside the {pdz_radius}-kilometer radius Permanent Danger Zone of the volcano."
        
        exp_rec = ExplanationRecommendation.from_parts(
            explanation=explanation + " " + recommendation
        )
    else:
        exp_rec = ExplanationRecommendation.from_parts(
            explanation=explanation,
            recommendation=recommendation
        )
    
    return HARSection(
        heading="PDZ (Permanent Danger Zone)",
        assessment=status,
        explanation_recommendation=exp_rec
    )


def _process_lahar(self, assessment: Assessment, volcano_name: str) -> Optional[HARSection]:
    """
    Process lahar hazard assessment.
    
    Special cases:
    - Pinatubo: 5 zones (Zone 1-5) with different explanations
    - Mayon: Prone levels (Highly/Moderately/Least prone)
    - Others: Standard prone/safe assessment
    
    Args:
        assessment: Volcano assessment data
        volcano_name: Name of volcano
        
    Returns:
        HARSection for lahar or None if not assessed
    """
    lahar_status = assessment.volcano.lahar
    
    if not lahar_status or lahar_status == "--":
        return None  # Not assessed
    
    rule = self.schema.volcano_rules.get('lahar')
    if not rule:
        return None
    
    volcano_lower = volcano_name.lower()
    
    # Get base explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    # Special case: Pinatubo zones
    if "pinatubo" in volcano_lower:
        zone_match = re.search(r"zone\s+([1-5])", lahar_status, re.IGNORECASE)
        if zone_match and rule.special_cases:
            zone_num = zone_match.group(1)
            pinatubo_zones = rule.special_cases.get('pinatubo_zones', {})
            zone_data = pinatubo_zones.get(f'zone_{zone_num}')
            
            if zone_data and 'explanation' in zone_data:
                # Use zone-specific explanation
                explanation = zone_data['explanation']
    
    # Special case: Mayon prone levels
    elif "mayon" in volcano_lower:
        # Mayon has specific prone level classifications
        # but explanation and recommendation are same for all levels
        pass  # Use standard explanation and recommendation
    
    # Standard case: Other volcanoes
    # Use standard explanation and recommendation
    
    exp_rec = ExplanationRecommendation.from_parts(
        explanation=explanation,
        recommendation=recommendation
    )
    
    return HARSection(
        heading="Lahar",
        assessment=lahar_status,
        explanation_recommendation=exp_rec
    )


def _process_pyroclastic_flow(self, assessment: Assessment) -> Optional[HARSection]:
    """
    Process pyroclastic flow/PDC hazard assessment.
    
    Args:
        assessment: Volcano assessment data
        
    Returns:
        HARSection for PDC or None if not assessed
    """
    pdc_status = assessment.volcano.pyroclastic_flow
    
    if not pdc_status or pdc_status == "--":
        return None
    
    rule = self.schema.volcano_rules.get('pyroclastic_density_current')
    if not rule:
        return None
    
    # Get explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    exp_rec = ExplanationRecommendation.from_parts(
        explanation=explanation,
        recommendation=recommendation
    )
    
    return HARSection(
        heading="Pyroclastic Density Current",
        assessment=pdc_status,
        explanation_recommendation=exp_rec
    )


def _process_lava_flow(self, assessment: Assessment) -> Optional[HARSection]:
    """
    Process lava flow hazard assessment.
    
    Args:
        assessment: Volcano assessment data
        
    Returns:
        HARSection for lava flow or None if not assessed
    """
    lava_status = assessment.volcano.lava_flow
    
    if not lava_status or lava_status == "--":
        return None
    
    # Skip if Safe (usually not shown in HAR for Safe status)
    if "safe" in lava_status.lower():
        return None
    
    rule = self.schema.volcano_rules.get('lava_flow')
    if not rule:
        return None
    
    # Get explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    exp_rec = ExplanationRecommendation.from_parts(
        explanation=explanation,
        recommendation=recommendation
    )
    
    return HARSection(
        heading="Lava Flow",
        assessment=lava_status,
        explanation_recommendation=exp_rec
    )


def _process_ballistic_projectiles(self, assessment: Assessment) -> Optional[HARSection]:
    """
    Process ballistic projectiles hazard assessment.
    
    Args:
        assessment: Volcano assessment data
        
    Returns:
        HARSection for ballistic projectiles or None if not assessed
    """
    ballistic_status = assessment.volcano.ballistic_projectile
    
    if not ballistic_status or ballistic_status == "--":
        return None
    
    # Skip if Safe
    if "safe" in ballistic_status.lower():
        return None
    
    rule = self.schema.volcano_rules.get('ballistic_projectiles')
    if not rule:
        return None
    
    # Get explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    exp_rec = ExplanationRecommendation.from_parts(
        explanation=explanation,
        recommendation=recommendation
    )
    
    return HARSection(
        heading="Ballistic Projectiles",
        assessment=ballistic_status,
        explanation_recommendation=exp_rec
    )


def _process_base_surge(self, assessment: Assessment) -> Optional[HARSection]:
    """
    Process base surge hazard assessment (Taal-specific).
    
    Args:
        assessment: Volcano assessment data
        
    Returns:
        HARSection for base surge or None if not assessed
    """
    base_surge_status = assessment.volcano.base_surge
    
    if not base_surge_status or base_surge_status == "--":
        return None
    
    # Skip if Safe
    if "safe" in base_surge_status.lower():
        return None
    
    rule = self.schema.volcano_rules.get('base_surge')
    if not rule:
        return None
    
    # Get explanation and recommendation
    explanation = rule.explanation
    recommendation = rule.recommendation
    
    exp_rec = ExplanationRecommendation.from_parts(
        explanation=explanation,
        recommendation=recommendation
    )
    
    return HARSection(
        heading="Base Surge",
        assessment=base_surge_status,
        explanation_recommendation=exp_rec
    )


def _check_needs_avoidance(self, assessment: Assessment) -> bool:
    """
    Check if any volcano hazard requires avoidance recommendation.
    
    Returns True if any hazard is "Prone" or within hazardous zones.
    
    Args:
        assessment: Volcano assessment data
        
    Returns:
        True if avoidance recommendation should be included
    """
    volcano = assessment.volcano
    
    # Keywords that indicate hazardous status
    prone_keywords = ["prone", "highly", "moderately", "within buffer", 
                     "inside pdz", "within pdz", "zone 1", "zone 2", "zone 3"]
    
    # Check all proximity hazards
    hazard_fields = [
        volcano.lahar,
        volcano.pyroclastic_flow,
        volcano.lava_flow,
        volcano.base_surge,
        volcano.ballistic_projectile
    ]
    
    for field in hazard_fields:
        if field:
            field_lower = field.lower()
            # Check if any prone keyword is in the status
            if any(keyword in field_lower for keyword in prone_keywords):
                # But not if it's "least prone" or "safe"
                if "least prone" not in field_lower and "safe" not in field_lower:
                    return True
    
    return False


def _get_avoidance_recommendation(self) -> ExplanationRecommendation:
    """
    Get general avoidance recommendation for prone volcanic hazards.
    
    This is shown when any proximity hazard is prone or highly prone.
    
    Returns:
        ExplanationRecommendation with avoidance text
    """
    text = (
        "Avoidance is recommended for sites that may potentially be affected by "
        "primary volcanic hazards, especially pyroclastic density currents and lava flows."
    )
    
    return ExplanationRecommendation.from_parts(explanation=text)


# ============================================================================
# UPDATED process_volcano_assessment METHOD
# ============================================================================

def process_volcano_assessment_UPDATED(self, assessment: Assessment) -> HAROutput:
    """
    Process volcano assessment following decision workflow.
    
    UPDATED VERSION - Includes proximity-hazard processing
    
    Workflow:
    1. check_map_availability ✅
    2. identify_nearest_active_volcano ✅
    3. check_distance_category ✅
    4. assess_pdz_status ✅ NEW
    5. assess_lava_flow ✅ NEW
    6. assess_pyroclastic_flow ✅ NEW
    7. assess_lahar ✅ NEW
    8. assess_ballistic_projectiles_if_applicable ✅ NEW
    9. assess_base_surge_if_taal ✅ NEW
    10. check_potentially_active_volcano ✅
    11. add_ashfall_statement ✅
    12. add_avoidance_recommendation_if_prone ✅ NEW
    13. add_supersedes_statement ✅
    
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
    
    # Add "X Volcano is the nearest identified active volcano to the site."
    if volcano_name != 'Unknown':
        nearest_statement = ExplanationRecommendation.from_parts(
            explanation=f"{volcano_name} Volcano is the nearest identified active volcano to the site."
        )
        common.append(nearest_statement)
    
    # 3. Distance-based safety statement
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
    
    # 4-9. Process individual hazards (ONLY if not distance-safe)
    if not is_distance_safe:
        # PDZ (Permanent Danger Zone)
        pdz_section = self._process_pdz(assessment, volcano_name)
        if pdz_section:
            sections.append(pdz_section)
        
        # Lahar (with special cases for Pinatubo zones and Mayon prone levels)
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
        
        # Ballistic Projectiles (if assessed)
        ballistic_section = self._process_ballistic_projectiles(assessment)
        if ballistic_section:
            sections.append(ballistic_section)
        
        # Base Surge (Taal only)
        if "taal" in volcano_name.lower():
            base_surge_section = self._process_base_surge(assessment)
            if base_surge_section:
                sections.append(base_surge_section)
    
    # 10. PAV (Potentially Active Volcano) - skip if we have nearby active volcano
    # Real HARs prioritize nearest AV over distant PAV
    # Only show PAV if it's mentioned and relevant
    
    # 11. Ashfall (always included)
    ashfall_statement = self._get_ashfall_statement(volcano_name)
    common.append(ashfall_statement)
    
    # 12. Avoidance recommendation (only if any hazard is prone)
    if not is_distance_safe and self._check_needs_avoidance(assessment):
        avoidance = self._get_avoidance_recommendation()
        common.append(avoidance)
    
    # 13. Supersedes
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
