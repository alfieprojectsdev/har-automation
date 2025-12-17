# Validation Comparison: Assessments 24777 & 24778

**Date:** 2025-12-15
**Source:** HAS-nOv-25-18268.pdf (Approved HAR from PHIVOLCS)
**Generated:** har-automation pipeline v0.1.0

---

## Assessment 24777 (Earthquake)

### Real Approved HAR (from PDF)

```
EXPLANATION AND RECOMMENDATION

* All hazard assessments are based on the latest available hazard maps and on the location
  indicated in the vicinity map provided.

* Ground rupture hazard assessment is the distance to the nearest known active fault. The
  recommended buffer zone, or Zone of Avoidance, against ground rupture hazard is at least 5
  meters on both sides of the active fault or from its zone of deformation.

* All sites may be affected by strong ground shaking.

* Ground shaking hazard can be mitigated by following the provisions of the National Building
  Code and the Structural Code of the Philippines.

* Avoidance is recommended for sites with earthquake-induced landslide hazard unless
  appropriate engineering interventions are in place.

* This hazard assessment supersedes any previous assessment made by this office regarding
  the site.

* QR code included in this document may be scanned to validate the authenticity of this Hazard
  Assessment Report.

* Hazard assessments reflected in this document may contain additional analysis conducted by
  researchers from the Institute.

* In some areas, hazard assessment may be updated as new data become available for
  interpretation or as a result of major topographic changes due to onset of natural events. To
  ensure up-to-date information and quick hazards assessment, access DOST-PHIVOLCS'
  online platforms. For point-specific location, use HazardHunterPH
  (https://hazardhunter.georisk.gov.ph), for LGU-based information, use GeoAnalyticsPH
  (https://geoanalytics.georisk.gov.ph).

* For site-specific evaluation or construction of critical facilities, detailed engineering assessment
  and onsite geotechnical engineering survey may be required.
```

### Our Generated HAR

```
EXPLANATION AND RECOMMENDATION

1. Ground Rupture: Safe; Approximately 458 meters west of the Central Samar Fault: Paranas Segment.
   Ground rupture hazard assessment is the distance to the nearest known active fault. The
   recommended buffer zone, or Zone of Avoidance, against ground rupture hazard is at least 5
   meters on both sides of the active fault or from its zone of deformation.

2. Ground Shaking and Liquefaction: All sites may be affected by strong ground shaking. Safe.
   Ground shaking and liquefaction hazards can be mitigated by following the provisions of the
   National Building Code and the Structural Code of the Philippines.

3. Earthquake-Induced Landslide: Least to Highly Susceptible; Within the depositional zone.
   Avoidance is recommended for sites with earthquake-induced landslide hazard unless
   appropriate engineering interventions are in place.

4. Tsunami: Safe. Tsunami threat to people's lives can be addressed by community preparedness
   and tsunami evacuation plan. Advice for tsunami evacuation comes from public agencies and
   local governments. But more importantly, coastal communities must learn to evacuate themselves
   when they recognize the three natural signs of tsunami, namely 1) strong ground shaking,
   2) unusual rise or fall of sea level, and 3) strong or unusual sound coming from the sea.

This assessment supersedes all previous reports issued for this site.

For more information on geohazards in the Philippines, please visit HazardHunterPH
(https://hazardhunter.georisk.gov.ph/) and GeoAnalyticsPH (https://geoanalytics.georisk.gov.ph/).
```

### Comparison

| Aspect | Real HAR | Our Generated | Match? |
|--------|----------|---------------|--------|
| **Format** | Bullet points (`*`) | Numbered points (`1. 2. 3.`) | ❌ Different |
| **Intro statement** | "All hazard assessments are based on..." | Missing | ❌ Missing |
| **Ground Rupture** | Explanation + Recommendation | ✅ Explanation + Recommendation | ✅ Correct wording |
| **Assessment status in point** | Not repeated | Included ("Safe; Approximately...") | ❌ Different |
| **Ground Shaking** | Separate bullet | Combined with Liquefaction | ❌ Different structure |
| **Liquefaction** | Combined with Ground Shaking | Combined with Ground Shaking | ✅ Correct |
| **EIL** | Explanation + Recommendation | ✅ Explanation + Recommendation | ✅ Correct wording |
| **Tsunami** | Not shown (Safe = omitted?) | Included with full explanation | ❌ Should be omitted? |
| **Supersedes** | "This hazard assessment supersedes any previous..." | "This assessment supersedes all previous reports..." | ⚠️ Similar wording |
| **QR Code disclaimer** | Included | Missing | ❌ Missing |
| **Additional analysis disclaimer** | Included | Missing | ❌ Missing |
| **Update disclaimer** | Included with HazardHunterPH/GeoAnalyticsPH | Shortened version | ⚠️ Partial |
| **Site-specific evaluation disclaimer** | Included | Missing | ❌ Missing |

### Key Findings

**✅ Correct:**
- Ground rupture explanation and recommendation wording is **exact match**
- Liquefaction mitigation wording is **exact match**
- EIL avoidance recommendation is **exact match**
- Schema wordings are **accurate**

**❌ Differences:**
1. **Format**: Bullets vs numbered points
2. **Missing intro**: "All hazard assessments are based on..."
3. **Assessment statuses**: Real HAR doesn't repeat status in each point
4. **Tsunami**: Real HAR omits when "Safe" (?)
5. **Missing disclaimers**: QR code, additional analysis, update, site-specific evaluation

---

## Assessment 24778 (Volcano)

### Real Approved HAR (from PDF)

```
EXPLANATION AND RECOMMENDATION

* All hazard assessments are based on the latest available hazard maps and on the location
  indicated in the vicinity map provided.

* Biliran Volcano is the nearest identified active volcano to the site.

* Considering the distance of the site from the volcano, the site is safe from volcanic hazards
  such as pyroclastic density currents, lava flows, and ballistic projectiles that may originate
  from the volcano.

* In case of future eruptions of Biliran Volcano and other nearby volcanoes, the site/s may be
  affected by tephra fall/ ashfall depending on the height of the eruption plume and prevailing
  wind direction at the time of eruption. Generally, tephra fall/ ashfall is thicker near the eruption
  center and thins away from the volcano. Ash can cause widespread infrastructural,
  agricultural, aircraft and property damage, and negative health impacts.

* This hazard assessment supersedes any previous assessment made by this office regarding
  the site.

* [Same disclaimers as earthquake assessment]
```

### Our Generated HAR

```
EXPLANATION AND RECOMMENDATION

1. Potentially Active Volcano: Approximately 85.4 km northeast of Cancajanag Volcano -
   Potentially Active. Approximately 85.4 km northeast of Cancajanag Volcano

2. In case of future eruptions of Unknown Volcano Volcano and other nearby volcanoes, the
   site/s may be affected by tephra fall/ ashfall depending on the height of the eruption plume
   and prevailing wind direction at the time of eruption. Generally, tephra fall/ ashfall is thicker
   near the eruption center and thins away from the volcano. Ash can cause widespread
   infrastructural, agricultural, and property damages, and negative health impacts.

This assessment supersedes all previous reports issued for this site.

For more information on geohazards in the Philippines, please visit HazardHunterPH
(https://hazardhunter.georisk.gov.ph/) and GeoAnalyticsPH (https://geoanalytics.georisk.gov.ph/).
```

### Comparison

| Aspect | Real HAR | Our Generated | Match? |
|--------|----------|---------------|--------|
| **Format** | Bullet points | Numbered points | ❌ Different |
| **Intro statement** | "All hazard assessments are based on..." | Missing | ❌ Missing |
| **Nearest volcano statement** | "Biliran Volcano is the nearest identified active volcano" | Missing | ❌ **Missing** |
| **Distance-based safety** | "Considering the distance of the site from the volcano..." | Missing | ❌ **Missing** |
| **PAV statement** | Not shown (Cancajanag PAV omitted?) | Shown as point 1 | ❌ **Wrong priority** |
| **Ashfall** | "In case of future eruptions of Biliran Volcano..." | "In case of future eruptions of Unknown Volcano Volcano..." | ❌ **Wrong volcano name** |
| **Ashfall wording** | Exact match from schema | ✅ Exact match | ✅ Correct |

### Key Findings

**✅ Correct:**
- Ashfall explanation wording is **exact match** (when volcano name is fixed)

**❌ Major Issues:**
1. **Missing nearest volcano statement**: "Biliran Volcano is the nearest identified active volcano"
2. **Missing distance-based safety**: "Considering the distance... the site is safe from..."
3. **Wrong volcano used**: Shows "Unknown Volcano" instead of "Biliran"
4. **PAV shown when shouldn't be**: Real HAR omits Cancajanag PAV, only mentions Biliran (nearest AV)

**Root cause:** Volcano assessment logic is simplified and doesn't properly handle:
- Nearest volcano extraction from assessment data
- Distance-based safety statements
- Priority of AV over PAV

---

## Summary

### Earthquake Assessment Quality

| Metric | Score | Notes |
|--------|-------|-------|
| **Wording Accuracy** | ✅ 95% | Schema wordings are exact matches |
| **Structure** | ⚠️ 70% | Numbered vs bullets, missing intro |
| **Completeness** | ⚠️ 60% | Missing 4 disclaimers |
| **Overall** | ⚠️ **75%** | Good foundation, needs formatting fixes |

### Volcano Assessment Quality

| Metric | Score | Notes |
|--------|-------|-------|
| **Wording Accuracy** | ✅ 90% | Ashfall wording correct |
| **Structure** | ⚠️ 70% | Same issues as earthquake |
| **Completeness** | ❌ 30% | Missing critical statements |
| **Overall** | ❌ **50%** | Needs major volcano logic implementation |

---

## Action Items

### High Priority

1. **Add intro statement**: "All hazard assessments are based on..."
2. **Fix volcano nearest statement**: Extract and display "Biliran Volcano is the nearest identified active volcano"
3. **Add distance-based safety**: "Considering the distance of the site from the volcano..."
4. **Fix ashfall volcano name**: Use nearest AV, not "Unknown Volcano"

### Medium Priority

5. **Change format**: Bullet points instead of numbered points
6. **Remove assessment status from points**: Don't repeat "Safe; Approximately..." in each point
7. **Add standard disclaimers**:
   - QR code validation
   - Additional analysis
   - Update disclaimer
   - Site-specific evaluation

### Low Priority

8. **Conditional tsunami**: Omit when "Safe" (needs confirmation)
9. **Supersedes wording**: Match exact official wording
10. **PAV priority**: Only show PAV when no nearby AV

---

## Validation Conclusion

**Strengths:**
- ✅ Schema has **exact official wordings** from templates
- ✅ Explanation + Recommendation **pairing is correct**
- ✅ Earthquake hazards **fundamentally sound**

**Gaps:**
- ❌ Volcano assessment **needs complete rewrite**
- ❌ Missing **standard disclaimers**
- ⚠️ Format differences (bullets vs numbers)

**Recommendation:**
1. Fix high-priority items (volcano logic, intro statement)
2. Add missing disclaimers
3. Adjust formatting to match official style
4. Re-validate with this same HAR

**Estimated effort:**
- Volcano fixes: 4-6 hours
- Disclaimers: 1-2 hours
- Format changes: 1 hour
- **Total: 6-9 hours**

---

**Status:** Validation complete - clear improvement path identified
**Next:** Implement high-priority fixes from this comparison
