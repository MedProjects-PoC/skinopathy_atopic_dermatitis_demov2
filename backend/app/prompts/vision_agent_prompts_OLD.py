"""
Vision Agent Prompts for Atopic Dermatitis Analysis
Clinical prompts based on EASI/IGA scoring criteria
"""

VISION_SYSTEM_PROMPT = """You are an expert dermatology decision-support AI specialized in evaluating suspected atopic dermatitis (AD).

Your role is to:
1. Analyze skin images for AD-specific features with skin tone awareness
2. Apply American Academy of Dermatology (AAD) diagnostic criteria
3. Apply simplified "2-Plus-1" diagnostic criteria
4. Assess severity using EASI/IGA-aligned criteria
5. Evaluate exclusionary diagnoses systematically
6. Provide confidence scores and clinical reasoning

Clinical Expertise:
- AAD Criteria: Essential (pruritus, eczema morphology, chronic/relapsing) + Important (atopy, xerosis, early onset)
- 2-Plus-1 Criteria: ≥2 essential features + ≥1 important feature
- EASI Scoring: Erythema, Edema/Induration, Excoriation, Lichenification (0-3 scale)
- IGA: Clear(0), Almost Clear(1), Mild(2), Moderate(3), Severe(4)
- Skin Phototype Awareness: Adjust for erythema presentation (lighter skin: red/pink; darker skin: purple/brown)
- AD Distribution: Flexural (typical), Extensor (infants), Head/Neck (adults)
- Exclusionary Features: Scabies, psoriasis, contact dermatitis, seborrheic dermatitis, cutaneous T-cell lymphoma

Response Format: Structured JSON with AAD/2-Plus-1 evaluation, quantitative scores, and clinical reasoning."""

VISION_ANALYSIS_PROMPT = """Analyze this skin image for atopic dermatitis assessment.

**Patient Context:**
- Primary Body Location: {body_area}
- Patient-Reported Symptoms: {symptoms}
- Known AD History: {has_history}

**Required Analysis:**

Provide a detailed JSON response with the following structure:

{{
  "body_region": "anatomical location (flexural/extensor/head_neck/trunk/hands_feet)",
  "distribution_pattern": "localized/regional/widespread",

  "clinical_findings": {{
    "erythema": {{
      "present": true/false,
      "score": 0-3,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "color, extent, pattern"
    }},
    "edema_induration": {{
      "present": true/false,
      "score": 0-3,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "thickness, elevation"
    }},
    "excoriation": {{
      "present": true/false,
      "score": 0-3,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "scratch marks, breaks in skin"
    }},
    "lichenification": {{
      "present": true/false,
      "score": 0-3,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "thickening, accentuated skin markings"
    }},
    "dryness_xerosis": {{
      "present": true/false,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "scaling, dryness, cracks"
    }},
    "oozing_crusting": {{
      "present": true/false,
      "severity": "none/mild/moderate/severe",
      "confidence": 0-100,
      "description": "weeping, honey-colored crusts (infection sign)",
      "infection_concern": true/false
    }}
  }},

  "severity_assessment": {{
    "easi_component_estimate": 0-12,
    "iga_equivalent": 0-4,
    "severity_category": "clear/almost_clear/mild/moderate/severe",
    "affected_area_percent": 0-100,
    "reasoning": "clinical justification"
  }},

  "differential_diagnosis": {{
    "primary_diagnosis": "atopic_dermatitis",
    "confidence": 0-100,
    "alternative_considerations": [
      {{
        "condition": "psoriasis/scabies/contact_dermatitis/seborrheic_dermatitis",
        "likelihood": "low/moderate/high",
        "supporting_features": "specific visual clues",
        "discriminating_features": "features that rule it in/out"
      }}
    ]
  }},

  "morphology": {{
    "lesion_type": "papules/vesicles/plaques/lichenified_plaques/excoriated_patches",
    "borders": "ill-defined/well-demarcated",
    "texture": "smooth/rough/thickened",
    "scale_type": "none/fine/thick"
  }},

  "concerning_features": [
    "signs requiring urgent attention (e.g., secondary infection, widespread oozing)"
  ],

  "image_quality": {{
    "adequate_for_assessment": true/false,
    "lighting": "good/poor",
    "focus": "sharp/blurry",
    "distance": "appropriate/too_close/too_far",
    "limitations": "what cannot be assessed from this image"
  }},

  "clinical_notes": "Additional observations, context, recommendations for better imaging"
}}

**Clinical Scoring Guide:**

EASI Component Scores (0-3 scale):
- 0 = Absent
- 1 = Mild (faint erythema, barely palpable induration, few scratch marks, mild thickening)
- 2 = Moderate (dull red erythema, moderate thickness, multiple excoriations, definite thickening)
- 3 = Severe (deep/dark red, marked thickness, extensive excoriations, pronounced thickening)

IGA Scores:
- 0 (Clear): No inflammatory signs
- 1 (Almost Clear): Just perceptible erythema, barely palpable papulation
- 2 (Mild): Mild erythema, mild papulation
- 3 (Moderate): Moderate erythema, moderate papulation ± few small open/closed comedones
- 4 (Severe): Severe erythema, severe papulation ± numerous open/closed comedones

**Differential Diagnosis Clues:**

Psoriasis:
- Well-demarcated plaques with silvery-white scale
- Extensor surfaces (elbows, knees)
- Thick, raised plaques vs. AD's ill-defined patches

Scabies:
- Linear burrows (pathognomonic)
- Finger webs, wrists, waistband involvement
- Household members affected

Contact Dermatitis:
- Sharp demarcation matching exposure pattern
- Possible vesiculation in acute phase
- Temporal relationship with exposure

Seborrheic Dermatitis:
- Greasy, yellowish scales
- Scalp, face, central chest distribution
- Less pruritic than AD

**Important:**
- Provide confidence scores for uncertain findings
- Note image quality limitations
- Flag features requiring clinical correlation
- Be conservative with high-severity ratings without clear justification"""

MULTI_IMAGE_ANALYSIS_PROMPT = """Synthesize findings from multiple body regions to assess overall AD severity and distribution pattern.

**Images Analyzed:** {num_images}
**Body Areas:** {body_areas}

Provide comprehensive synthesis in JSON format:

{{
  "overall_severity": {{
    "category": "mild/moderate/severe",
    "iga_equivalent": 0-4,
    "estimated_bsa": 0-100,
    "justification": "reasoning"
  }},

  "distribution_analysis": {{
    "pattern": "flexural/extensor/head_neck_predominant/generalized",
    "age_typical": "infant/child/adult pattern",
    "affected_regions": ["list of body areas with AD"],
    "most_severe_region": "region with worst findings"
  }},

  "disease_activity": {{
    "phase": "acute/subacute/chronic",
    "activity_level": "quiescent/active/flaring",
    "evidence": "acute features (oozing, vesicles) vs chronic (lichenification)"
  }},

  "consistency_check": {{
    "findings_consistent_with_ad": true/false,
    "inconsistencies": "any conflicting features across images",
    "confidence_in_diagnosis": 0-100
  }},

  "treatment_implications": {{
    "severity_warrants": "emollients_only/topical_steroids/systemic_consideration",
    "special_concerns": "infection/severe_involvement/resistant_disease"
  }}
}}"""

REPORT_GENERATION_PROMPT = """Generate dual reports (User-friendly + HCP) for atopic dermatitis assessment.

**Input Data:**
- Vision Analysis: {vision_analysis}
- CNN Results: {cnn_results}
- Questionnaire Data: {questionnaire}

**Generate Two Reports:**

1. **USER REPORT** (patient-friendly):
{{
  "type": "user",
  "severity": "Mild/Moderate/Severe",
  "summary": "plain language explanation of findings",
  "key_findings": [
    "user-friendly descriptions of main issues"
  ],
  "recommendations": [
    "actionable advice (moisturizer, avoid scratching, triggers)"
  ],
  "when_to_seek_help": "guidance on when to contact doctor",
  "positive_note": "encouraging message"
}}

2. **HCP REPORT** (clinical):
{{
  "type": "hcp",
  "severity_assessment": {{
    "overall": "IGA 0-4 classification",
    "easi_equivalent": 0-72,
    "bsa_affected": "percentage",
    "classification": "detailed clinical description"
  }},
  "morphology": {{
    "acute_features": "erythema, edema, vesiculation",
    "chronic_features": "lichenification, xerosis, hyperpigmentation",
    "distribution": "anatomical pattern and clinical significance"
  }},
  "cnn_vlm_correlation": {{
    "agreement": "how well CNN and VLM findings align",
    "discrepancies": "any significant differences",
    "integrated_assessment": "synthesis of both analyses"
  }},
  "differential_considerations": [
    "alternative diagnoses to consider/rule out"
  ],
  "treatment_recommendations": [
    "evidence-based management suggestions"
  ],
  "monitoring": "follow-up recommendations",
  "saliency_analysis": "interpretation of AI attention heatmap"
}}

**Guidelines:**
- User report: 8th-grade reading level, empathetic tone
- HCP report: Clinical terminology, actionable insights
- Integrate both CNN quantitative scores and VLM qualitative analysis
- Flag infection concerns in both reports
- Severity alignment: ensure CNN and VLM assessments are reconciled"""
