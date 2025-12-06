"""
Clinical Note Generation Service
Generates formatted SOAP notes for HCP reports
"""
from typing import Dict, Any
from loguru import logger


class ClinicalNoteService:
    """Service for generating formatted clinical notes"""

    def generate_soap_note(
        self,
        cnn_results: Dict[str, Any],
        vision_findings: Dict[str, Any],
        easi_results: Dict[str, Any],
        questionnaire: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate SOAP-formatted clinical note

        Args:
            cnn_results: CNN analysis output
            vision_findings: Vision agent analysis
            easi_results: EASI scoring results
            questionnaire: Patient questionnaire responses

        Returns:
            Dict with structured clinical note sections
        """
        try:
            # Extract key data
            easi_calc = easi_results.get("easi_calculation", {})
            total_easi = easi_calc.get("total_easi", 0)
            severity_cat = easi_calc.get("severity_category", "Unknown")
            cnn_severity = cnn_results.get('severity_score', 0)
            affected_area = cnn_results.get('affected_area_pct', 0)

            # Build SOAP note sections
            soap_note = {
                "chief_complaint": self._generate_chief_complaint(questionnaire),
                "history_present_illness": self._generate_hpi(questionnaire, cnn_results),
                "objective_findings": self._generate_objective(cnn_results, vision_findings, easi_calc),
                "assessment": self._generate_assessment(total_easi, severity_cat, cnn_severity, easi_calc),
                "plan": self._generate_plan(total_easi, severity_cat, questionnaire),
                "ai_insights": self._generate_ai_insights(cnn_results, vision_findings, easi_results)
            }

            logger.info(f"Generated SOAP note for EASI={total_easi:.1f}, Severity={severity_cat}")
            return soap_note

        except Exception as e:
            logger.error(f"Error generating clinical note: {e}")
            return self._get_fallback_note()

    def _generate_chief_complaint(self, questionnaire: Dict) -> str:
        """Generate chief complaint section"""
        itch = questionnaire.get('itch_intensity', 0)
        primary_location = questionnaire.get('primary_location', 'not specified')

        # Format location
        location_map = {
            'flexural': 'flexural areas (inside elbows, behind knees)',
            'extensor': 'extensor surfaces',
            'face_neck': 'face and neck',
            'hands_feet': 'hands and feet',
            'trunk': 'trunk',
            'widespread': 'widespread distribution',
            'scalp_hairline': 'scalp and hairline',
            'webs_waistband': 'finger/toe webs, waistband'
        }
        location_text = location_map.get(primary_location, primary_location)

        return f"Patient presents with pruritic rash affecting {location_text}. Itch severity rated {itch}/10."

    def _generate_hpi(self, questionnaire: Dict, cnn_results: Dict) -> str:
        """Generate history of present illness"""
        sections = []

        # Duration/chronicity
        if questionnaire.get('chronic_relapsing'):
            sections.append("This is a chronic, relapsing condition with periods of exacerbation and remission.")
        else:
            sections.append("This appears to be an acute presentation.")

        # Atopic history
        if questionnaire.get('atopic_triad_history'):
            sections.append("Patient reports personal or family history of atopic conditions (asthma, hay fever, or eczema).")

        # Sleep impact
        nights_disturbed = questionnaire.get('nights_sleep_disturbed', 0)
        if nights_disturbed > 0:
            sections.append(f"Sleep is disturbed {nights_disturbed} nights per week due to itching.")

        # Triggers/exacerbating factors
        if questionnaire.get('new_exposure_trigger'):
            sections.append("Patient reports recent exposure to potential trigger (new soap, jewelry, plants, or chemicals).")

        if questionnaire.get('household_itchy_or_nighttime_worse'):
            sections.append("Others in household have similar symptoms, or symptoms worsen at night (may suggest scabies differential).")

        # Current treatments
        if questionnaire.get('steroid_use_last_2weeks'):
            sections.append("Topical corticosteroids have been used in the last 2 weeks.")

        # Moisturizer use
        moisture = questionnaire.get('moisturizer_frequency', 'none')
        moisture_map = {
            'none': "No moisturizer currently used.",
            'once_daily': "Moisturizes once daily.",
            'twice_daily': "Moisturizes twice daily.",
            'more': "Moisturizes more than twice daily."
        }
        sections.append(moisture_map.get(moisture, "Moisturizer frequency not specified."))

        # Stress
        stress = questionnaire.get('recent_stress_level', 0)
        if stress >= 7:
            sections.append(f"Reports high stress levels ({stress}/10), which may be exacerbating condition.")

        # Flare status from CNN
        flare_status = cnn_results.get('flare_status', 'unknown')
        if flare_status == 'active_flare':
            sections.append("AI analysis indicates active flare state.")
        elif flare_status == 'pre_flare':
            sections.append("AI analysis detects pre-flare indicators.")

        return " ".join(sections)

    def _generate_objective(self, cnn_results: Dict, vision_findings: Dict, easi_calc: Dict) -> str:
        """Generate objective findings section"""
        sections = []

        # CNN Analysis
        cnn_sev = cnn_results.get('severity_score', 0)
        affected = cnn_results.get('affected_area_pct', 0)
        sections.append(f"**CNN Analysis:** Severity {cnn_sev:.1f}/100, affected area {affected:.1f}%.")

        inflammation = cnn_results.get('inflammation_score', 0)
        dryness = cnn_results.get('dryness_score', 0)
        lichen = cnn_results.get('lichenification_score', 0)
        excoriation = cnn_results.get('excoriation_detected', False)

        features = []
        if inflammation > 50:
            features.append(f"moderate-severe inflammation ({inflammation:.0f}/100)")
        elif inflammation > 25:
            features.append(f"mild inflammation ({inflammation:.0f}/100)")

        if dryness > 50:
            features.append(f"significant xerosis ({dryness:.0f}/100)")
        elif dryness > 25:
            features.append(f"mild xerosis ({dryness:.0f}/100)")

        if lichen > 25:
            features.append(f"lichenification present ({lichen:.0f}/100)")

        if excoriation:
            features.append("excoriations detected")

        if features:
            sections.append(f"Notable features: {', '.join(features)}.")

        # EASI Breakdown
        total_easi = easi_calc.get("total_easi", 0)
        severity_cat = easi_calc.get("severity_category", "Unknown")
        sections.append(f"\n\n**EASI Score:** {total_easi:.1f}/72 ({severity_cat} severity).")

        # Regional breakdown
        regions = []
        for region_name, region_key in [
            ("Head/Neck", "head_neck"),
            ("Trunk", "trunk"),
            ("Upper Limbs", "upper_limbs"),
            ("Lower Limbs", "lower_limbs")
        ]:
            if region_key in easi_calc:
                region_data = easi_calc[region_key]
                regional_easi = region_data.get("regional_easi", 0)
                if regional_easi > 0:
                    erythema = region_data.get("erythema", 0)
                    induration = region_data.get("induration", 0)
                    excoriation_score = region_data.get("excoriation", 0)
                    lichen_score = region_data.get("lichenification", 0)
                    area_score = region_data.get("area_score", 0)

                    features_list = []
                    if erythema >= 2:
                        features_list.append("erythema")
                    if induration >= 2:
                        features_list.append("induration")
                    if excoriation_score >= 2:
                        features_list.append("excoriation")
                    if lichen_score >= 2:
                        features_list.append("lichenification")

                    feature_text = f" ({', '.join(features_list)})" if features_list else ""
                    area_pct = ["0%", "1-9%", "10-29%", "30-49%", "50-69%", "70-89%", "90-100%"][min(area_score, 6)]
                    regions.append(f"  - {region_name}: {regional_easi:.1f} (area: {area_pct}{feature_text})")

        if regions:
            sections.append("\nRegional breakdown:\n" + "\n".join(regions))

        # Vision Agent Findings (if available)
        if vision_findings:
            skin_tone = vision_findings.get("skin_tone_assessment", {})
            if skin_tone:
                fitzpatrick = skin_tone.get("fitzpatrick_scale", "")
                monk = skin_tone.get("monk_skin_tone_scale", "")
                if fitzpatrick or monk:
                    sections.append(f"\n\n**Skin Tone:** Fitzpatrick {fitzpatrick}, Monk Scale {monk}.")

        return "\n".join(sections)

    def _generate_assessment(self, total_easi: float, severity_cat: str, cnn_severity: float, easi_calc: Dict) -> str:
        """Generate assessment section"""
        sections = []

        # Primary diagnosis
        sections.append(f"**Primary Diagnosis:** Atopic Dermatitis, {severity_cat.lower()} severity.")

        # Severity classification
        sections.append(f"- EASI Score: {total_easi:.1f}/72")
        sections.append(f"- CNN Severity: {cnn_severity:.1f}/100")

        # Agent consensus
        consensus_diff = abs(cnn_severity - total_easi)
        if consensus_diff < 15:
            sections.append(f"- AI agent consensus: CNN and EASI scoring aligned (Δ{consensus_diff:.1f})")
        else:
            sections.append(f"- AI agent discrepancy noted: CNN={cnn_severity:.1f}, EASI={total_easi:.1f} (Δ{consensus_diff:.1f})")

        # Disease phase
        disease_phase = easi_calc.get("clinical_interpretation", {}).get("disease_phase", "")
        if disease_phase:
            sections.append(f"- Disease phase: {disease_phase}")

        # Most affected region
        most_affected = easi_calc.get("clinical_interpretation", {}).get("most_affected_region", "")
        if most_affected:
            sections.append(f"- Most affected: {most_affected}")

        return "\n".join(sections)

    def _generate_plan(self, total_easi: float, severity_cat: str, questionnaire: Dict) -> str:
        """Generate plan section"""
        sections = []

        # Treatment recommendations based on severity
        if total_easi < 7.1:  # Mild
            sections.append("**Treatment Approach:**")
            sections.append("- Continue regular emollient use (at least twice daily)")
            sections.append("- Low-potency topical corticosteroid for active lesions")
            sections.append("- Topical calcineurin inhibitor (TCI) for sensitive areas")

        elif total_easi < 21.1:  # Moderate
            sections.append("**Treatment Approach:**")
            sections.append("- Intensive emollient therapy (multiple times daily)")
            sections.append("- Medium-potency topical corticosteroid for body")
            sections.append("- Low-potency TCS or TCI for face/neck")
            sections.append("- Consider proactive therapy for frequently affected areas")
            sections.append("- Wet wrap therapy if severe flare")

        else:  # Severe
            sections.append("**Treatment Approach:**")
            sections.append("- High-intensity topical therapy (high-potency TCS for body)")
            sections.append("- Consider systemic therapy:")
            sections.append("  - First-line: Dupilumab (IL-4/IL-13 inhibitor)")
            sections.append("  - Alternatives: JAK inhibitors (upadacitinib, abrocitinib)")
            sections.append("  - Short-term: oral corticosteroids for severe flare control")
            sections.append("- Intensive emollient therapy")
            sections.append("- Address quality of life impact")

        # Secondary infection check
        oozing = questionnaire.get('oozing_honey_crusts', False)
        if oozing:
            sections.append("\n**Infection Concern:**")
            sections.append("- Honey-colored crusting suggests secondary bacterial infection")
            sections.append("- Consider topical/oral antibiotics (anti-staph coverage)")
            sections.append("- Culture if not responding to empiric therapy")

        # Follow-up
        if total_easi < 7.1:
            sections.append("\n**Follow-up:** 4-6 weeks, or sooner if worsening.")
        elif total_easi < 21.1:
            sections.append("\n**Follow-up:** 2-4 weeks to assess response.")
        else:
            sections.append("\n**Follow-up:** 1-2 weeks, consider dermatology referral if not already established.")

        # Patient education
        sections.append("\n**Patient Education:**")
        sections.append("- Trigger avoidance (identify and avoid personal triggers)")
        sections.append("- Proper moisturizer application technique")
        sections.append("- When to seek urgent care (signs of infection, severe flare)")

        return "\n".join(sections)

    def _generate_ai_insights(self, cnn_results: Dict, vision_findings: Dict, easi_results: Dict) -> str:
        """Generate AI-specific insights section"""
        sections = []

        sections.append("**AI Multi-Agent Analysis:**")

        # CNN insights
        cnn_conf = cnn_results.get('cnn_confidence', 0)
        sections.append(f"- CNN confidence: {cnn_conf:.1%}")

        # Vision agent confidence
        vision_conf = vision_findings.get("confidence", 0) if vision_findings else 0
        if vision_conf:
            sections.append(f"- Vision agent confidence: {vision_conf}/100")

        # EASI calculation confidence
        easi_conf = easi_results.get("easi_calculation", {}).get("calculation_confidence", 0)
        if easi_conf:
            sections.append(f"- EASI calculation confidence: {easi_conf}/100")

        # RAG usage
        sections.append("- Clinical knowledge base: RAG-enhanced prompts")

        return "\n".join(sections)

    def _get_fallback_note(self) -> Dict[str, str]:
        """Return fallback note if generation fails"""
        return {
            "chief_complaint": "Clinical note generation error.",
            "history_present_illness": "Unable to generate HPI.",
            "objective_findings": "Unable to generate objective findings.",
            "assessment": "Unable to generate assessment.",
            "plan": "Unable to generate plan.",
            "ai_insights": "AI insights unavailable."
        }


# Global instance
clinical_note_service = ClinicalNoteService()
