# Test Cases Extracted from Real HAR Documents

## Summary

Analysis of real PHIVOLCS HAR documents using Gemini CLI revealed key patterns and edge cases for comprehensive testing.

---

## Key Findings

### 1. EIL Assessment Patterns

**Three Status Levels:**
- **Safe**: No landslide susceptibility
- **Susceptible**: Requires investigation (typically slope-based)
- **Prone**: High landslide risk

**Critical Case - HAS-Dec-25-18223:**
- **Original (Wrong)**: EIL = "Safe"
- **Corrected (Right)**: EIL = "Susceptible"
- **Evidence**: Slope analysis showed 15.11° / 27% grade
- **Lesson**: EIL assessment requires slope analysis from Google Earth elevation data

**Recommendation for Susceptible EIL:**
> "Avoidance is recommended for sites with earthquake-induced landslide hazard unless appropriate engineering interventions are in place."

---

### 2. Volcano Assessment Patterns

#### Pattern A: Safe from All Hazards (Distant Volcano)
**Example: HAS-Sep-25-17810 (Bulusan Volcano, 24 km)**
- Lahar: Safe
- Pyroclastic Flow: Safe
- Lava Flow: Safe
- Only mentions ashfall advisory

#### Pattern B: Mixed Hazards (Moderate Distance)
**Example: HAS-Feb-25-14157 (Kanlaon Volcano, 15.2 km)**
- Lahar: **Highly prone**
- Pyroclastic Flow: **Prone** (within buffer zone)
- Lava Flow: Safe
- Includes PDZ (Permanent Danger Zone) discussion

**Key Recommendations:**
- **PDZ**: "Human settlement is not recommended within the PDZ" (4 km radius)
- **PDC Avoidance**: "Avoidance is recommended for sites that may potentially be affected by primary volcanic hazards, especially pyroclastic density currents and lava flows."
- **Lahar Mitigation**: "1) observing or implementing legal easement adjacent to river banks, 2) community preparedness and evacuation plan"

---

### 3. Special Cases

#### Potentially Active Volcanoes (PAV)
**Example: Labo Volcano**
- Classification: PAV (no historical eruptions)
- Can still be assessed as "Prone" to lahar
- Statement: "eruptive and hazard potential is yet to be determined"

**Example: HAS-Dec-25-18223 mentions Labo:**
> "Labo Volcano is currently classified by DOST-PHIVOLCS as a potentially active volcano, which is morphologically young-looking but with no historical or analytical records of eruption, therefore, its eruptive and hazard potential is yet to be determined."

#### Mayon Volcano Specifics
- Often shows "Prone" to lahar even at moderate distances
- Danger zone delineations specific to Mayon

#### Pinatubo Specifics
**Example: HAS-Jul-25-8845**
- River system-based assessment: "Sacobia-Pasig-Potrero river systems"
- Multiple lahar zones (5 zones for Pinatubo)

#### Taal Volcano Specifics
**Example: HAS-Mar-25-14541**
- Permanent Danger Zone (PDZ) = entire Volcano Island
- Base surge assessments
- Specific fissure rules

---

## Test Data for E2E Testing

### Test Case 1: Basic Earthquake (Safe)
```
Assessment: 24918
Category: Earthquake
Location: 120.989669,14.537869
Active Fault: Safe; Approximately 7.1 km west of Valley Fault System
Liquefaction: High Potential
EIL: Safe
```

**Expected Output:**
- Ground rupture explanation with 5m buffer zone
- Ground shaking + liquefaction combined
- NBC/NSCP compliance recommendation

---

### Test Case 2: EIL Susceptible (Slope-Based)
```
Assessment: 18223
Category: Earthquake
Location: Lot 3, Psd-05-035637; Brgy. Colasi, Mercedes, Camarines Norte
Active Fault: Safe; Approximately 40.9 km northeast of Legaspi Lineament
EIL: Susceptible
```

**Expected Output:**
- Ground rupture explanation
- Ground shaking mitigation
- **EIL Avoidance**: "Avoidance is recommended for sites with earthquake-induced landslide hazard unless appropriate engineering interventions are in place."

---

### Test Case 3: Volcano - All Safe (Distant)
```
Assessment: 17810
Category: Volcano
Location: Brgy. Cabid-An, Sorsogon City, Sorsogon
Volcano: Bulusan, 24 km north
Lahar: Safe
Pyroclastic Flow: Safe
Lava Flow: Safe
```

**Expected Output:**
- Nearest volcano identification: "Bulusan Volcano is the nearest identified active volcano to the site."
- Ashfall advisory only
- No specific hazard recommendations (all safe)

---

### Test Case 4: Volcano - Mixed Hazards (Kanlaon)
```
Assessment: 14157
Category: Volcano
Location: Lot 479-G, Brgy. Robles, La Castellana, Negros Occidental
Volcano: Kanlaon, 15.2 km southwest
Lahar: Highly prone
Pyroclastic Flow: Prone; Within buffer zone
Lava Flow: Safe
```

**Expected Output:**
- PDZ explanation (4 km radius for Kanlaon)
- PDC avoidance recommendation
- Lahar mitigation: legal easement + evacuation plan
- Ashfall advisory

---

### Test Case 5: PAV (Potentially Active Volcano)
```
Assessment: 18223
Category: Volcano
Location: Brgy. Colasi, Mercedes, Camarines Norte
Volcano 1: Isarog, 44 km northwest (Safe/Safe/Safe)
Volcano 2: Labo (PAV), 33 km east
```

**Expected Output:**
- Isarog as nearest active volcano
- Labo PAV statement: "morphologically young-looking but with no historical or analytical records of eruption, therefore, its eruptive and hazard potential is yet to be determined."
- Distance-based safety for Isarog

---

## Standardized Recommendation Texts

### Ground Rupture
> "Ground rupture hazard assessment is the distance to the nearest known active fault. The recommended buffer zone, or Zone of Avoidance, against ground rupture hazard is at least 5 meters on both sides of the active fault or from its zone of deformation."

### Ground Shaking
> "All sites may be affected by strong ground shaking."

### Ground Shaking Mitigation
> "Ground shaking hazard can be mitigated by following the provisions of the National Building Code and the Structural Code of the Philippines."

### EIL Avoidance (Susceptible)
> "Avoidance is recommended for sites with earthquake-induced landslide hazard unless appropriate engineering interventions are in place."

### Lahar Mitigation
> "Lahar threat to people's lives can be addressed by 1) observing or implementing legal easement adjacent to river banks, as provided in existing laws, ordinances and land-use plans, and 2) community preparedness and evacuation plan. At-risk communities must learn to evacuate themselves when lahar threats are imminent."

### PDC/Lava Avoidance
> "Avoidance is recommended for sites that may potentially be affected by primary volcanic hazards, especially pyroclastic density currents and lava flows."

### Ashfall Advisory (Standard)
> "In case of future eruptions of [VOLCANO] and other nearby volcanoes, the site/s may be affected by tephra fall/ ashfall depending on the height of the eruption plume and prevailing wind direction at the time of eruption. Generally, tephra fall/ ashfall is thicker near the eruption center and thins away from the volcano. Ash can cause widespread infrastructural, agricultural, aircraft and property damage, and negative health impacts."

---

## Validation Checklist

For each test case, verify:
- [ ] Correct hazard status extracted
- [ ] Appropriate explanation generated
- [ ] Correct recommendations applied
- [ ] Special case handling (PAV, PDZ, etc.)
- [ ] Exact wording matches official HAR templates
- [ ] All relevant hazards addressed
- [ ] Standard closing statements included

---

## Next Steps

1. **Implement E2E Tests** using pytest with these test cases
2. **Validate Decision Engine** generates correct output for each scenario
3. **Test Edge Cases**: PAV volcanoes, Taal PDZ, Pinatubo river systems
4. **Performance Testing**: Measure HAR generation time for each test case
5. **Integration Testing**: Full workflow from OHAS table → API → HAR output

---

**Document Generated**: $(date)
**Analysis Method**: Gemini CLI multimodal PDF parsing
**Source Documents**: 20+ HAR PDFs from /home/finch/repos/hasadmin/docs/
**Token Savings**: ~50K tokens (used Gemini CLI instead of Claude for bulk parsing)
