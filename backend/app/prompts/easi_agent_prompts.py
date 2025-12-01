"""
EASI Scoring Agent Prompts
Structured prompts for calculating EASI scores following official methodology
"""

EASI_SYSTEM_PROMPT = """You are an expert dermatology AI specialized in calculating EASI (Eczema Area and Severity Index) scores for atopic dermatitis.

Your role is to:
1. Calculate accurate EASI scores following the official methodology
2. Score each body region independently
3. Validate all scores are within proper ranges
4. Provide transparent reasoning for each calculation
5. Flag any uncertainties or edge cases

EASI Methodology Expertise:
- Body regions: Head/Neck (10%), Trunk (30%), Upper Limbs (20%), Lower Limbs (40%)
- Clinical signs: Erythema, Induration/Papulation, Excoriation, Lichenification (each 0-3)
- Area involvement: 0-6 scale per region
- Formula: Region EASI = (Sum of 4 signs) × Area × Multiplier
- Total EASI: Sum of 4 regions (0-72 range)

Response Format: Structured JSON with detailed calculations and reasoning."""

EASI_CALCULATION_PROMPT = """Calculate the EASI score based on the following assessment data.

**Vision Analysis Results:**
{vision_findings}

**Questionnaire Data:**
{questionnaire_data}

**Body Region Information:**
{body_regions}

**Required Output (JSON):**

{{
  "easi_calculation": {{
    "head_neck": {{
      "erythema": 0-3,
      "induration": 0-3,
      "excoriation": 0-3,
      "lichenification": 0-3,
      "area_score": 0-6,
      "sum_of_signs": "sum of 4 clinical signs",
      "multiplier": 0.1,
      "regional_easi": "calculated score",
      "reasoning": "explain scoring for each parameter"
    }},
    "trunk": {{
      "erythema": 0-3,
      "induration": 0-3,
      "excoriation": 0-3,
      "lichenification": 0-3,
      "area_score": 0-6,
      "sum_of_signs": "sum",
      "multiplier": 0.3,
      "regional_easi": "calculated score",
      "reasoning": "explain"
    }},
    "upper_limbs": {{
      "erythema": 0-3,
      "induration": 0-3,
      "excoriation": 0-3,
      "lichenification": 0-3,
      "area_score": 0-6,
      "sum_of_signs": "sum",
      "multiplier": 0.2,
      "regional_easi": "calculated score",
      "reasoning": "explain"
    }},
    "lower_limbs": {{
      "erythema": 0-3,
      "induration": 0-3,
      "excoriation": 0-3,
      "lichenification": 0-3,
      "area_score": 0-6,
      "sum_of_signs": "sum",
      "multiplier": 0.4,
      "regional_easi": "calculated score",
      "reasoning": "explain"
    }},
    "total_easi": "sum of all 4 regional scores (0-72)",
    "severity_category": "Clear/Almost Clear/Mild/Moderate/Severe/Very Severe",
    "calculation_confidence": 0-100,
    "calculation_notes": "any assumptions, limitations, or edge cases"
  }},

  "clinical_interpretation": {{
    "severity_classification": "based on EASI ranges",
    "dominant_features": ["list primary clinical features"],
    "most_affected_region": "region with highest EASI",
    "disease_phase": "acute/subacute/chronic",
    "treatment_implications": "severity-appropriate recommendations"
  }},

  "scoring_rationale": {{
    "erythema_basis": "how redness scores were determined",
    "induration_basis": "how thickness scores were determined",
    "excoriation_basis": "how scratch mark scores were determined",
    "lichenification_basis": "how thickening scores were determined",
    "area_estimation_method": "how body surface area was estimated",
    "uncertainties": ["list any scoring uncertainties"]
  }}
}}

**EASI Scoring Criteria:**

**Erythema (Redness) - Score 0-3:**
- 0 = None
- 1 = Mild (faint pink)
- 2 = Moderate (dull red)
- 3 = Severe (deep/dark red)

**Induration/Papulation (Thickness) - Score 0-3:**
- 0 = None (flat)
- 1 = Mild (barely palpable, slight elevation)
- 2 = Moderate (definite thickening, clear elevation)
- 3 = Severe (marked thickness, pronounced elevation)

**Excoriation (Scratch marks) - Score 0-3:**
- 0 = None
- 1 = Mild (few scattered scratch marks)
- 2 = Moderate (multiple scratch marks, some breaks in skin)
- 3 = Severe (extensive scratching, many excoriated areas)

**Lichenification (Thickening with skin line accentuation) - Score 0-3:**
- 0 = None
- 1 = Mild (slightly visible thickening, subtle skin lines)
- 2 = Moderate (definitely visible, clear accentuated markings)
- 3 = Severe (prominent widespread thickening, exaggerated skin lines)

**Area Involvement - Score 0-6 per region:**
- 0 = No involvement (0%)
- 1 = 1-9%
- 2 = 10-29%
- 3 = 30-49%
- 4 = 50-69%
- 5 = 70-89%
- 6 = 90-100%

**EASI Severity Interpretation:**
- 0-1: Clear
- 1.1-7: Almost Clear / Mild
- 7.1-21: Moderate
- 21.1-50: Severe
- >50: Very Severe

**Important:**
- All scores must be integers (0, 1, 2, or 3 for signs; 0-6 for area)
- Total EASI must be ≤72
- Regional EASI = (E + I + Ex + L) × Area × Multiplier
- Be conservative when uncertain - document assumptions
- If region not assessed, note as "not_assessed" in reasoning"""

TREATMENT_RECOMMENDATION_PROMPT = """Based on the EASI score and clinical assessment, provide treatment recommendations.

**EASI Score:** {easi_score}
**Severity:** {severity}
**Affected Regions:** {affected_regions}
**Questionnaire Data:** {questionnaire_data}
**Current Treatments:** {current_treatments}

Provide structured treatment recommendations in JSON format:

{{
  "treatment_recommendation": {{
    "severity_level": "EASI-based severity",
    "treatment_step": 1-4,
    "recommended_approach": {{
      "emollients": "specific recommendations",
      "topical_therapy": {{
        "type": "TCS/TCI/JAK inhibitor",
        "potency": "low/mid/high",
        "regions": ["specific areas"],
        "frequency": "application schedule",
        "duration": "recommended course"
      }},
      "systemic_therapy": {{
        "indicated": true/false,
        "options": ["if EASI >21 or treatment failure"],
        "rationale": "why systemic therapy considered"
      }},
      "adjunctive_therapy": ["antihistamines, wet wraps, phototherapy, etc."]
    }},
    "special_considerations": {{
      "infection_concern": true/false,
      "steroid_sparing_needed": true/false,
      "maintenance_therapy": "proactive approach recommendations"
    }},
    "monitoring": {{
      "reassessment_timing": "when to re-evaluate",
      "success_criteria": "treatment goals",
      "escalation_triggers": "when to escalate therapy"
    }}
  }}
}}"""

PROGRESSION_ANALYSIS_PROMPT = """Analyze disease progression based on current and historical EASI scores.

**Current Assessment:** {current_data}
**Historical Assessments:** {historical_assessments}
**Timeline:** {timeline}

Provide progression analysis in JSON:

{{
  "progression_analysis": {{
    "trend": "improving/stable/worsening",
    "easi_change": {{
      "absolute_change": "current - previous EASI",
      "percent_change": "percentage",
      "clinically_significant": true/false,
      "mcid_threshold": "≥6.6 points or 50% for EASI"
    }},
    "regional_changes": {{
      "head_neck": "trend",
      "trunk": "trend",
      "upper_limbs": "trend",
      "lower_limbs": "trend"
    }},
    "trajectory_assessment": {{
      "short_term": "1-2 weeks trend",
      "medium_term": "1-3 months trend",
      "flare_pattern": "frequency and severity"
    }},
    "treatment_response": {{
      "current_regimen_effectiveness": "assessment",
      "optimization_opportunities": ["suggestions"],
      "concerns": ["treatment failures, side effects"]
    }}
  }}
}}"""
