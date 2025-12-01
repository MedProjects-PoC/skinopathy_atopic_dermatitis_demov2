"""
VLM Service for Dual Report Generation
Uses QWEN VLM or Claude/OpenAI as fallback
"""
from typing import Dict, Tuple
from loguru import logger
import os


class VLMService:
    """Vision Language Model service for generating dual reports"""

    def __init__(self, use_local: bool = True):
        """
        Initialize VLM service

        Args:
            use_local: Whether to use local QWEN model or API fallback
        """
        self.use_local = use_local
        self.model = None
        self.processor = None
        self.is_loaded = False

    def load_model(self):
        """Load QWEN VLM model"""
        try:
            if not self.use_local:
                logger.info("Using API-based VLM (no local model loading needed)")
                self.is_loaded = True
                return

            # Try to load QWEN model
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

            logger.info("Loading QWEN VLM model...")
            model_name = "Qwen/Qwen2-VL-2B-Instruct"  # Using smaller 2B model for faster inference

            self.processor = AutoProcessor.from_pretrained(model_name)
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype="auto"
            )
            self.is_loaded = True
            logger.success("QWEN VLM model loaded successfully!")

        except ImportError as e:
            logger.warning(f"Transformers not available: {e}. Using template-based reports.")
            self.is_loaded = False
        except Exception as e:
            logger.error(f"Error loading VLM model: {e}. Using template-based reports.")
            self.is_loaded = False

    def generate_dual_reports(
        self,
        image_path: str,
        cnn_results: Dict,
        questionnaire: Dict,
        saliency_map_path: str
    ) -> Tuple[Dict, Dict]:
        """
        Generate both user and HCP reports

        Args:
            image_path: Path to uploaded image
            cnn_results: CNN analysis results
            questionnaire: Questionnaire responses
            saliency_map_path: Path to saliency map

        Returns:
            Tuple of (user_report, hcp_report) dictionaries
        """
        try:
            if not self.is_loaded:
                self.load_model()

            # Generate reports (using templates for now, will add VLM inference later)
            user_report = self._generate_user_report(cnn_results, questionnaire)
            hcp_report = self._generate_hcp_report(cnn_results, questionnaire, saliency_map_path)

            logger.success("Dual reports generated successfully")
            return user_report, hcp_report

        except Exception as e:
            logger.error(f"Error generating reports: {e}")
            raise

    def _generate_user_report(self, cnn_results: Dict, questionnaire: Dict) -> Dict:
        """Generate user-friendly report"""

        severity_score = cnn_results['severity_score']

        # Determine severity level
        if severity_score < 30:
            severity = "Mild"
            severity_desc = "Your skin condition is showing mild activity"
        elif severity_score < 50:
            severity = "Moderate"
            severity_desc = "Your skin condition is showing moderate activity"
        elif severity_score < 70:
            severity = "Moderate to Severe"
            severity_desc = "Your skin condition is showing moderate to severe activity"
        else:
            severity = "Severe"
            severity_desc = "Your skin condition is showing severe activity"

        # Build summary
        location_map = {
            'flexural': 'inner elbows/knees',
            'extensor': 'outer elbows/knees',
            'scalp_hairline': 'scalp and hairline',
            'webs_waistband': 'finger webs and waistband area'
        }
        location = location_map.get(questionnaire.get('primary_location', 'flexural'), 'affected areas')

        summary = f"{severity_desc} with lesions primarily on your {location}."

        # Add context about flare status
        flare_status = cnn_results.get('flare_status', 'active')
        if flare_status == 'pre_flare':
            summary += " Early warning signs suggest a flare may be developing."
        elif flare_status == 'active':
            summary += " You are currently experiencing an active flare."
        elif flare_status == 'improving':
            summary += " Your condition appears to be improving."

        # Key findings
        key_findings = [
            f"Severity score: {severity_score:.1f}/100 ({severity})",
            f"Areas affected: {location} ({cnn_results['affected_area_pct']:.1f}% of skin)",
            f"Inflammation level: {self._score_to_level(cnn_results['inflammation_score'])}"
        ]

        if cnn_results['dryness_score'] > 50:
            key_findings.append(f"Significant dryness detected")

        if cnn_results['excoriation_detected']:
            key_findings.append("Scratch marks visible - try to minimize scratching")

        # Generate recommendations
        recommendations = self._generate_user_recommendations(cnn_results, questionnaire)

        # When to seek help
        seek_help = self._generate_seek_help_message(cnn_results, questionnaire)

        # Positive reinforcement
        positive_note = self._generate_positive_note(questionnaire)

        return {
            "type": "user",
            "severity": severity,
            "summary": summary,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "when_to_seek_help": seek_help,
            "positive_note": positive_note,
            "visual_summary": {
                "severity_score": severity_score,
                "affected_area": cnn_results['affected_area_pct']
            }
        }

    def _generate_hcp_report(self, cnn_results: Dict, questionnaire: Dict, saliency_map_path: str) -> Dict:
        """Generate HCP professional report"""

        severity_score = cnn_results['severity_score']

        # IGA/EASI classification
        if severity_score < 25:
            iga = "IGA 1 (Almost Clear)"
            easi_class = "Mild"
        elif severity_score < 50:
            iga = "IGA 2 (Mild)"
            easi_class = "Mild to Moderate"
        elif severity_score < 75:
            iga = "IGA 3 (Moderate)"
            easi_class = "Moderate to Severe"
        else:
            iga = "IGA 4 (Severe)"
            easi_class = "Severe"

        severity_assessment = {
            "overall": iga,
            "easi_equivalent": severity_score,
            "bsa_affected": f"{cnn_results['affected_area_pct']:.1f}%",
            "classification": f"{easi_class} atopic dermatitis, {cnn_results['flare_status'].replace('_', ' ')}"
        }

        # Morphology analysis
        morphology = {
            "acute_features": f"Erythema ({cnn_results['inflammation_score']:.1f}/100)",
            "chronic_features": f"Xerosis ({cnn_results['dryness_score']:.1f}/100), Lichenification ({cnn_results['lichenification_score']:.1f}/100)",
            "distribution": self._analyze_distribution(questionnaire)
        }

        # Body distribution
        body_regions = cnn_results.get('body_regions', {})
        body_distribution = {
            region: severity for region, severity in body_regions.items()
        }

        # Saliency analysis
        saliency_analysis = "GradCAM heat map highlights areas of maximal model attention corresponding to inflammatory changes and lesion distribution patterns."

        # Symptom burden
        itch = questionnaire.get('itch_intensity', 0)
        sleep = questionnaire.get('nights_sleep_disturbed', 0)

        symptom_burden = {
            "pruritus": f"{'Severe' if itch >= 8 else 'Moderate' if itch >= 5 else 'Mild'} ({itch}/10)",
            "sleep_disturbance": f"{sleep} nights in past week",
            "scratch_itch_cycle": "Active" if cnn_results['excoriation_detected'] else "Controlled"
        }

        # Differential diagnosis analysis
        differential = self._analyze_differential(questionnaire)

        # Treatment recommendations
        treatment_recs = self._generate_hcp_recommendations(cnn_results, questionnaire)

        # Prognosis
        prognosis = self._generate_prognosis(cnn_results, questionnaire)

        return {
            "type": "hcp",
            "severity_assessment": severity_assessment,
            "morphology": morphology,
            "body_distribution": body_distribution,
            "saliency_analysis": saliency_analysis,
            "symptom_burden": symptom_burden,
            "trigger_analysis": self._analyze_triggers(questionnaire),
            "treatment_recommendations": treatment_recs,
            "prognosis": prognosis,
            "differential_considerations": differential,
            "saliency_map_url": f"/storage/saliency_maps/{os.path.basename(saliency_map_path)}" if saliency_map_path else "",
            "next_assessment_recommended": "7-10 days or sooner if worsening"
        }

    def _score_to_level(self, score: float) -> str:
        """Convert numeric score to severity level"""
        if score < 30:
            return "Mild"
        elif score < 60:
            return "Moderate"
        else:
            return "Severe"

    def _generate_user_recommendations(self, cnn_results: Dict, questionnaire: Dict) -> list:
        """Generate user-friendly recommendations"""
        recs = []

        # Moisturizer recommendation
        freq = questionnaire.get('moisturizer_frequency', 'none')
        if freq == 'none':
            recs.append("Start applying moisturizer at least twice daily - this is essential for managing AD")
        elif freq in ['once_daily', 'twice_daily']:
            recs.append(f"Continue your {freq.replace('_', ' ')} moisturizer routine consistently")
        else:
            recs.append("Excellent moisturizer adherence - keep it up!")

        # Steroid use
        if questionnaire.get('steroid_use_last_2weeks'):
            if cnn_results['severity_score'] > 60:
                recs.append("Your current treatment may need adjustment - discuss with your doctor")
            else:
                recs.append("Continue your prescribed steroid cream as directed")
        else:
            if cnn_results['severity_score'] > 50:
                recs.append("Consider discussing topical steroid treatment with your healthcare provider")

        # Scratch management
        if cnn_results['excoriation_detected']:
            recs.append("Try to minimize scratching - keep nails short, wear cotton gloves at night if needed")

        # Stress management
        if questionnaire.get('recent_stress_level', 0) > 7:
            recs.append("High stress can trigger flares - consider stress management techniques")

        # Infection risk
        if questionnaire.get('oozing_honey_crusts'):
            recs.append("Signs of possible infection present - contact your doctor promptly")

        return recs[:5]  # Limit to top 5

    def _generate_hcp_recommendations(self, cnn_results: Dict, questionnaire: Dict) -> list:
        """Generate HCP treatment recommendations"""
        recs = []

        severity = cnn_results['severity_score']
        on_steroids = questionnaire.get('steroid_use_last_2weeks')

        # Treatment escalation
        if severity > 70:
            if on_steroids:
                recs.append("Consider treatment escalation: higher potency topical corticosteroid or systemic therapy")
            else:
                recs.append("Initiate mid-to-high potency topical corticosteroid for affected areas")
        elif severity > 40:
            if not on_steroids:
                recs.append("Consider low-to-mid potency topical corticosteroid therapy")

        # Emollient therapy
        if questionnaire.get('moisturizer_frequency') != 'more':
            recs.append("Intensify emollient therapy: recommend 3-4x daily application, ointment-based preferred")

        # Infection management
        if questionnaire.get('oozing_honey_crusts'):
            recs.append("Evaluate for secondary bacterial infection (S. aureus); consider topical/oral antibiotic")

        # Itch-scratch cycle
        if cnn_results['excoriation_detected']:
            recs.append("Address itch-scratch cycle: consider oral antihistamine for nocturnal pruritus")

        # DDx-specific recommendations
        if questionnaire.get('thick_silvery_scales'):
            recs.append("Psoriatic features noted - consider mixed diagnosis or patch testing")
        if questionnaire.get('household_itchy_or_nighttime_worse'):
            recs.append("Red flag for scabies - recommend skin scraping/microscopy")
        if questionnaire.get('new_exposure_trigger'):
            recs.append("Contact dermatitis component suspected - patch testing may be indicated")

        return recs

    def _generate_seek_help_message(self, cnn_results: Dict, questionnaire: Dict) -> str:
        """Generate when to seek help message"""
        urgent_flags = []

        if questionnaire.get('oozing_honey_crusts'):
            urgent_flags.append("signs of infection")
        if cnn_results['severity_score'] > 80:
            urgent_flags.append("severe symptoms")
        if questionnaire.get('nights_sleep_disturbed', 0) >= 6:
            urgent_flags.append("significant sleep disruption")

        if urgent_flags:
            return f"Contact your doctor soon due to {', '.join(urgent_flags)}. "

        return "Contact your doctor if itching becomes unbearable, you see signs of infection (warmth, pus, fever), or if the flare doesn't improve in 7-10 days."

    def _generate_positive_note(self, questionnaire: Dict) -> str:
        """Generate positive reinforcement"""
        if questionnaire.get('moisturizer_frequency') == 'more':
            return "Excellent moisturizer adherence - this is one of the most important things you can do!"
        elif questionnaire.get('moisturizer_frequency') in ['twice_daily', 'once_daily']:
            return "You're doing well with your moisturizer routine - keep it up!"
        else:
            return "Starting a good skincare routine will help manage your condition."

    def _analyze_distribution(self, questionnaire: Dict) -> str:
        """Analyze anatomical distribution pattern"""
        location = questionnaire.get('primary_location', 'flexural')
        if location == 'flexural':
            return "Classic flexural pattern consistent with atopic dermatitis"
        elif location == 'extensor':
            return "Extensor distribution - atypical for AD, consider psoriasis"
        elif location == 'scalp_hairline':
            return "Scalp/facial distribution - consider seborrheic dermatitis component"
        else:
            return "Intertriginous distribution - evaluate for scabies if pruritic"

    def _analyze_triggers(self, questionnaire: Dict) -> Dict:
        """Analyze identified triggers"""
        triggers = []

        if questionnaire.get('new_exposure_trigger'):
            triggers.append("Contact irritant/allergen")
        if questionnaire.get('recent_stress_level', 0) > 7:
            triggers.append("Psychosocial stress")

        pattern = "Acute exacerbation" if questionnaire.get('new_exposure_trigger') else "Chronic relapsing pattern"

        return {
            "identified": triggers if triggers else ["No specific triggers identified"],
            "pattern": pattern
        }

    def _analyze_differential(self, questionnaire: Dict) -> list:
        """Generate differential diagnosis list"""
        ddx = ["Primary: Atopic dermatitis"]

        # Add differentials based on questionnaire
        if questionnaire.get('thick_silvery_scales'):
            ddx.append("Consider: Psoriasis (well-defined plaques with silvery scale)")
        if questionnaire.get('household_itchy_or_nighttime_worse'):
            ddx.append("Rule out: Scabies (household involvement, nocturnal pruritus)")
        if questionnaire.get('new_exposure_trigger'):
            ddx.append("Consider: Allergic contact dermatitis (temporal relationship with exposure)")
        if questionnaire.get('primary_location') == 'scalp_hairline':
            ddx.append("Consider: Seborrheic dermatitis (scalp/facial distribution)")

        # Infection
        if questionnaire.get('oozing_honey_crusts'):
            ddx.append("Rule out: Secondary bacterial infection (impetiginization)")

        return ddx

    def _generate_prognosis(self, cnn_results: Dict, questionnaire: Dict) -> str:
        """Generate prognosis statement"""
        if questionnaire.get('atopic_triad_history') and questionnaire.get('chronic_relapsing'):
            return "Chronic relapsing course expected. Favorable response anticipated with appropriate treatment intensification and trigger avoidance."
        else:
            return "Favorable prognosis with appropriate management. May represent acute episode amenable to treatment."


# Global instance
vlm_service = VLMService(use_local=False)  # Using template-based for now
