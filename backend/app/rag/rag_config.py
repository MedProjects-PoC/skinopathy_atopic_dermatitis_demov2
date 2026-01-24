"""
RAG (Retrieval-Augmented Generation) Configuration for AD Clinical Knowledge
Uses GCP Vertex AI Vector Search + Text Embeddings
"""

from typing import Dict, Any, List
from pydantic import BaseModel
import os


class RAGConfig(BaseModel):
    """Configuration for RAG system"""

    # GCP Vertex AI Vector Search
    project_id: str = os.getenv("GCP_PROJECT_ID", "skin-demos")
    region: str = os.getenv("GCP_REGION", "us-central1")
    vector_search_index_endpoint: str = ""  # Will be created during setup

    # Embedding model
    embedding_model: str = "text-embedding-005"  # Latest Vertex AI embedding model
    embedding_dimension: int = 768
    embedding_cost_per_1k_chars: float = 0.00001  # $0.00001 per 1k characters

    # Vector search parameters
    num_neighbors: int = 5  # Top-K similar documents to retrieve
    distance_measure: str = "DOT_PRODUCT_DISTANCE"

    # Document chunking
    chunk_size: int = 1000  # Characters per chunk
    chunk_overlap: int = 200

    # Cloud Storage for knowledge base
    knowledge_base_bucket: str = os.getenv("MODELS_BUCKET", "skin-demos-models")
    knowledge_base_path: str = "ad_knowledge_base/"


class KnowledgeSource(BaseModel):
    """Metadata for a knowledge source"""
    source_id: str
    title: str
    source_type: str  # "guideline", "paper", "textbook", "clinical_trial"
    publication_year: int
    relevance_score: float  # 0-1, manually assigned
    content: str
    metadata: Dict[str, Any] = {}


# Predefined AD Clinical Knowledge Base
AD_CLINICAL_KNOWLEDGE = [
    {
        "source_id": "hanifin_rajka_criteria",
        "title": "Hanifin and Rajka Diagnostic Criteria for Atopic Dermatitis",
        "source_type": "guideline",
        "publication_year": 1980,
        "relevance_score": 1.0,
        "content": """
HANIFIN AND RAJKA DIAGNOSTIC CRITERIA FOR ATOPIC DERMATITIS

Major Features (Must have 3 or more):
1. Pruritus (itching)
2. Typical morphology and distribution:
   - Flexural lichenification in adults
   - Facial and extensor involvement in infancy
3. Chronic or chronically relapsing dermatitis
4. Personal or family history of atopy (asthma, allergic rhinitis, atopic dermatitis)

Minor Features (Must have 3 or more):
1. Xerosis (dry skin)
2. Ichthyosis / palmar hyperlinearity / keratosis pilaris
3. Immediate (Type I) skin test reactivity
4. Elevated serum IgE
5. Early age of onset
6. Tendency toward cutaneous infections (especially S. aureus and HSV)
7. Tendency toward nonspecific hand or foot dermatitis
8. Nipple eczema
9. Cheilitis
10. Recurrent conjunctivitis
11. Dennie-Morgan infraorbital fold
12. Keratoconus
13. Anterior subcapsular cataracts
14. Orbital darkening
15. Facial pallor/facial erythema
16. Pityriasis alba
17. Anterior neck folds
18. Itch when sweating
19. Intolerance to wool and lipid solvents
20. Perifollicular accentuation
21. Food hypersensitivity
22. Course influenced by environmental/emotional factors
23. White dermographism/delayed blanch

Diagnosis requires: 3+ major features AND 3+ minor features
        """,
        "metadata": {
            "clinical_use": "diagnostic_criteria",
            "sensitivity": 0.96,
            "specificity": 0.93
        }
    },
    {
        "source_id": "easi_scoring",
        "title": "EASI (Eczema Area and Severity Index) Scoring System",
        "source_type": "guideline",
        "publication_year": 2001,
        "relevance_score": 1.0,
        "content": """
EASI SCORING SYSTEM FOR ATOPIC DERMATITIS SEVERITY

Body Regions and Weighting:
- Head/Neck: 10% (multiplier: 0.1)
- Trunk: 30% (multiplier: 0.3)
- Upper Extremities: 20% (multiplier: 0.2)
- Lower Extremities: 40% (multiplier: 0.4)

Clinical Signs (Score 0-3 for each):
1. ERYTHEMA (Redness)
   - 0 = None
   - 1 = Mild (faint pink)
   - 2 = Moderate (dull red)
   - 3 = Severe (deep/dark red)

2. INDURATION/PAPULATION (Thickness/Swelling/Edema)
   - 0 = None
   - 1 = Mild (barely palpable)
   - 2 = Moderate (definite thickening)
   - 3 = Severe (marked thickness)

3. EXCORIATION (Scratch marks)
   - 0 = None
   - 1 = Mild (few)
   - 2 = Moderate (multiple)
   - 3 = Severe (extensive)

4. LICHENIFICATION (Thickening with accentuated skin markings)
   - 0 = None
   - 1 = Mild (slightly visible)
   - 2 = Moderate (definitely visible)
   - 3 = Severe (prominent and widespread)

Area Involvement (0-6 scale per region):
- 0 = No involvement
- 1 = 1-9%
- 2 = 10-29%
- 3 = 30-49%
- 4 = 50-69%
- 5 = 70-89%
- 6 = 90-100%

Formula for each region:
Region EASI = (Erythema + Induration + Excoriation + Lichenification) × Area × Multiplier

Total EASI Score = Sum of all 4 regions (0-72 range)

Severity Interpretation:
- 0-1: Clear
- 1.1-7: Almost clear / Mild
- 7.1-21: Moderate
- 21.1-50: Severe
- >50: Very severe
        """,
        "metadata": {
            "clinical_use": "severity_assessment",
            "validated": True,
            "inter_rater_reliability": "high"
        }
    },
    {
        "source_id": "iga_scoring",
        "title": "IGA (Investigator's Global Assessment) for Atopic Dermatitis",
        "source_type": "guideline",
        "publication_year": 2004,
        "relevance_score": 1.0,
        "content": """
IGA (INVESTIGATOR'S GLOBAL ASSESSMENT) SCORING

5-Point IGA Scale:
0 = CLEAR
- No inflammatory signs of AD
- Residual hyperpigmentation/hypopigmentation may be present

1 = ALMOST CLEAR
- Just perceptible erythema (faint pink)
- Barely palpable papulation
- No oozing/crusting

2 = MILD
- Mild erythema
- Mild papulation
- No oozing/crusting

3 = MODERATE
- Moderate erythema
- Moderate papulation
- ± Few small open/closed comedones
- ± Mild oozing/crusting

4 = SEVERE
- Severe erythema (deep/dark red)
- Severe papulation (marked induration)
- ± Numerous open/closed comedones
- ± Moderate to severe oozing/crusting

Clinical Interpretation:
- Treatment success often defined as IGA 0-1 (clear or almost clear)
- IGA 2 requires topical therapy
- IGA 3-4 may require systemic therapy
- Change of ≥2 points considered clinically significant

Key Considerations:
- Global assessment across all affected areas
- Presence of oozing/crusting indicates acute phase
- Absence of oozing with lichenification indicates chronic phase
        """,
        "metadata": {
            "clinical_use": "severity_assessment",
            "validated": True,
            "common_in_trials": True
        }
    },
    {
        "source_id": "differential_diagnosis_psoriasis",
        "title": "Differentiating Atopic Dermatitis from Psoriasis",
        "source_type": "clinical_guide",
        "publication_year": 2020,
        "relevance_score": 0.95,
        "content": """
DIFFERENTIAL DIAGNOSIS: ATOPIC DERMATITIS vs. PSORIASIS

Key Distinguishing Features:

DISTRIBUTION:
AD: Flexural surfaces (elbows, knees, neck folds)
Psoriasis: Extensor surfaces (elbows, knees), scalp, sacrum

MORPHOLOGY:
AD: Ill-defined erythematous patches with excoriations
Psoriasis: Well-demarcated erythematous plaques with silvery-white scale

SCALE TYPE:
AD: Fine, dry scale or no scale (weeping if acute)
Psoriasis: Thick, silvery-white, micaceous scale (Auspitz sign when removed)

PRURITUS:
AD: Intense, primary complaint
Psoriasis: Variable, less prominent

BORDERS:
AD: Poorly defined, irregular
Psoriasis: Sharply demarcated

AGE OF ONSET:
AD: Usually infancy/early childhood (60% by age 1)
Psoriasis: Bimodal (15-30 years or 50-60 years)

ASSOCIATED CONDITIONS:
AD: Atopic triad (asthma, allergic rhinitis, food allergies)
Psoriasis: Metabolic syndrome, psoriatic arthritis

NAIL CHANGES:
AD: Rare (may see polished nails from rubbing)
Psoriasis: Common (pitting, oil spots, onycholysis)

KOEBNER PHENOMENON:
AD: Uncommon
Psoriasis: Common (lesions at sites of trauma)

RED FLAGS FOR PSORIASIS (when AD suspected):
- Thick, well-demarcated plaques
- Silvery scale
- Extensor predominance
- Nail involvement
- Positive family history of psoriasis
        """,
        "metadata": {
            "clinical_use": "differential_diagnosis",
            "evidence_level": "expert_consensus"
        }
    },
    {
        "source_id": "differential_diagnosis_scabies",
        "title": "Differentiating Atopic Dermatitis from Scabies",
        "source_type": "clinical_guide",
        "publication_year": 2019,
        "relevance_score": 0.95,
        "content": """
DIFFERENTIAL DIAGNOSIS: ATOPIC DERMATITIS vs. SCABIES

PATHOGNOMONIC FEATURES OF SCABIES:
1. Linear burrows (2-10mm threadlike lesions)
2. Characteristic distribution: finger webs, wrists, waistband, genitals
3. Household contacts affected
4. Intense nocturnal pruritus

DISTRIBUTION PATTERNS:
AD: Flexural areas, face (infants), hands
Scabies: Finger webs*, wrists*, axillae, waist, genitals, feet
(*Most specific locations)

PRURITUS:
AD: Constant, worsens with triggers (heat, stress, allergens)
Scabies: Markedly worse at night (mite activity)

MORPHOLOGY:
AD: Erythematous patches/plaques, lichenification
Scabies: Burrows (linear), papules, vesicles, nodules

SECONDARY INFECTION:
AD: Common (S. aureus), honey-colored crusts
Scabies: Common (excoriated lesions), impetiginization

FAMILY/HOUSEHOLD:
AD: Family history of atopy common
Scabies: Simultaneous household involvement characteristic

RESPONSE TO TREATMENT:
AD: Improves with topical steroids
Scabies: Does NOT improve with steroids (may worsen)

RED FLAGS FOR SCABIES (when AD suspected):
- New onset intense itching in multiple family members
- Predominant involvement of hands (especially finger webs)
- Linear burrows present
- Nocturnal itch predominance
- Genital lesions (in adults)
- No improvement or worsening with topical steroids
- Pruritus in caregivers/family members

DIAGNOSTIC CONFIRMATION:
- Skin scraping with microscopy (mites, eggs, feces)
- Dermoscopy (burrow visualization)
- Empiric treatment trial if high suspicion
        """,
        "metadata": {
            "clinical_use": "differential_diagnosis",
            "evidence_level": "expert_consensus",
            "public_health_significance": "high"
        }
    },
    {
        "source_id": "treatment_stepwise",
        "title": "Stepwise Treatment Approach for Atopic Dermatitis",
        "source_type": "guideline",
        "publication_year": 2023,
        "relevance_score": 1.0,
        "content": """
STEPWISE TREATMENT APPROACH FOR ATOPIC DERMATITIS (2023)

ALL PATIENTS (Baseline):
- Emollients: Liberal use, 2-4x daily, ointment-based preferred
- Trigger avoidance: Harsh soaps, hot water, known allergens
- Patient education: Itch-scratch cycle, treatment adherence

STEP 1: MILD AD (IGA 1-2, EASI <7)
- Daily emollients (cornerstone)
- Low-potency topical corticosteroids (hydrocortisone 1-2.5%)
  - Face/intertriginous: Use cautiously, limit duration
- Alternative: Topical calcineurin inhibitors (tacrolimus 0.03%, pimecrolimus 1%)
  - Steroid-sparing, safe for face/eyelids
  - No atrophy risk

STEP 2: MODERATE AD (IGA 2-3, EASI 7-21)
- Continue emollients
- Mid-to-high potency topical corticosteroids
  - Body: Triamcinolone 0.1%, fluocinonide 0.05%
  - Face: Desonide 0.05%, hydrocortisone butyrate 0.1%
- Topical calcineurin inhibitors for maintenance
- Consider: Wet wrap therapy for acute flares
- Address secondary infection if present (topical/oral antibiotics)

STEP 3: SEVERE AD (IGA 4, EASI >21)
- Continue emollients + topical therapy
- Phototherapy (nb-UVB) - if available and appropriate
- Systemic therapy options:
  a) Dupilumab (IL-4/IL-13 inhibitor) - First-line biologic
     - FDA approved ≥6 months age
     - Well-tolerated, high efficacy
  b) Oral immunosuppressants (steroid-sparing):
     - Cyclosporine (rapid onset, short-term use)
     - Methotrexate
     - Azathioprine
     - Mycophenolate mofetil
  c) JAK inhibitors:
     - Upadacitinib, abrocitinib (oral)
     - Ruxolitinib (topical)
  d) Tralokinumab (IL-13 inhibitor) - Alternative biologic

STEP 4: REFRACTORY SEVERE AD
- Combination systemic therapies
- Clinical trial consideration
- Multidisciplinary management

SPECIAL CONSIDERATIONS:
- Infection:
  - Impetiginization: Topical mupirocin or systemic antibiotics
  - Eczema herpeticum: Oral acyclovir/valacyclovir
- Pruritus: Antihistamines (sedating for nighttime), gabapentin
- Stress/psychosocial: CBT, stress management
- Maintenance: Proactive therapy (intermittent TCS to healed lesions)

TREATMENT GOALS:
- Achieve IGA 0-1 (clear or almost clear)
- Minimize itch and sleep disruption
- Prevent flares
- Improve quality of life
        """,
        "metadata": {
            "clinical_use": "treatment_guidelines",
            "evidence_level": "high",
            "guideline_source": "AAD_2023"
        }
    }
]


DEFAULT_RAG_CONFIG = RAGConfig()
