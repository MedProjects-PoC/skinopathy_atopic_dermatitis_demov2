# Skinopathy AD Questionnaire - 12 Clinically Validated Questions

## Differential Diagnosis Questions (7)

### Q1: Pruritus Baseline (DDx)
**Question:** "On a scale of 0 to 10, how intense has the itching been over the last 3 days?"
- **Type:** Integer (0-10)
- **Field:** `itch_intensity`
- **Clinical Purpose:** AD is rarely present without itching ("Itch that rashes"). A score of 0 should flag the clinician to look for non-inflammatory dermatoses.

### Q2: Chronicity & Pattern (DDx)
**Question:** "Has this rash been present for more than 6 months, coming and going in flare-ups?"
- **Type:** Boolean (Yes/No)
- **Field:** `chronic_relapsing`
- **Clinical Purpose:** AD is chronic and relapsing. A "No" suggests acute conditions like Allergic Contact Dermatitis, fungal infection, or drug eruption.

### Q3: Atopic Triad (DDx/History)
**Question:** "Do you or any immediate family members have a history of asthma, hay fever (seasonal allergies), or childhood eczema?"
- **Type:** Boolean (Yes/No)
- **Field:** `atopic_triad_history`
- **Clinical Purpose:** A positive answer strongly supports an AD diagnosis (High Positive Predictive Value).

### Q4: Anatomical Distribution (DDx)
**Question:** "Where is the rash primarily located?"
- **Type:** Single choice
- **Field:** `primary_location`
- **Options:**
  - `flexural` - Inner elbows/knees (Classic AD)
  - `extensor` - Outer elbows/knees (Psoriasis)
  - `scalp_hairline` - Scalp/Hairline (Seborrheic Dermatitis)
  - `webs_waistband` - Webs of fingers/waistband (Scabies)
- **Clinical Purpose:** Distribution pattern helps differentiate AD from other dermatoses.

### Q5: Scabies Differentiator (DDx - Red Flag)
**Question:** "Is anyone else in your household currently itchy, or does the itch get significantly worse specifically at night?"
- **Type:** Boolean (Yes/No)
- **Field:** `household_itchy_or_nighttime_worse`
- **Clinical Purpose:** Household involvement strongly suggests an infestation (Scabies) rather than non-contagious AD.

### Q6: Contact vs. Endogenous (DDx)
**Question:** "Did the rash appear immediately after using a new soap, jewelry, laundry detergent, or exploring outdoors?"
- **Type:** Boolean (Yes/No)
- **Field:** `new_exposure_trigger`
- **Clinical Purpose:** Suggests Allergic Contact Dermatitis (ACD) or Irritant Contact Dermatitis rather than AD.

### Q7: Psoriasis Differentiator (DDx)
**Question:** "Is the rash clearly defined with a thick, silvery-white scale on top?"
- **Type:** Boolean (Yes/No)
- **Field:** `thick_silvery_scales`
- **Clinical Purpose:** Thick silvery scales are the hallmark of Psoriasis, whereas AD typically has "ill-defined" borders and crusting.

---

## Clinical Data Capture Questions (3)

### Q8: Sleep Disruption (Data Capture)
**Question:** "In the last week, how many nights was your sleep disturbed by the skin condition?"
- **Type:** Integer (0-7)
- **Field:** `nights_sleep_disturbed`
- **Clinical Purpose:** A critical quality-of-life metric (POEM score component) that dictates the aggressiveness of treatment (e.g., need for systemic therapy vs. topical).

### Q9: Infection Risk (Data Capture)
**Question:** "Is the skin currently oozing, weeping clear fluid, or developing golden/honey-colored crusts?"
- **Type:** Boolean (Yes/No)
- **Field:** `oozing_honey_crusts`
- **Clinical Purpose:** Signs of Staph aureus superinfection (Impetiginization), requiring antibiotics in addition to anti-inflammatories.

### Q10: Treatment Failure/History (Data Capture)
**Question:** "Have you used hydrocortisone or other steroid creams in the past 2 weeks?"
- **Type:** Boolean (Yes/No)
- **Field:** `steroid_use_last_2weeks`
- **Clinical Purpose:** Clinicians need to know if the patient is "steroid naive" or if the current flare is breaking through active treatment (indicating a need to step up therapy).

---

## AD Management Questions (2)

### Q11: Treatment Adherence Tracking
**Question:** "How often do you apply moisturizer?"
- **Type:** Single choice
- **Field:** `moisturizer_frequency`
- **Options:**
  - `none` - Not using moisturizer
  - `once_daily` - Once per day
  - `twice_daily` - Twice per day
  - `more` - More than twice daily
- **Clinical Purpose:** Tracks treatment adherence, critical for AD management.

### Q12: Stress as AD Trigger
**Question:** "On a scale of 0-10, what has your stress level been recently?"
- **Type:** Integer (0-10)
- **Field:** `recent_stress_level`
- **Clinical Purpose:** Stress is a known AD trigger; tracking helps identify flare patterns.

---

## API Request Format

```json
{
  "image": "base64_encoded_image_data",
  "questionnaire": {
    "itch_intensity": 8,
    "chronic_relapsing": true,
    "atopic_triad_history": true,
    "primary_location": "flexural",
    "household_itchy_or_nighttime_worse": false,
    "new_exposure_trigger": false,
    "thick_silvery_scales": false,
    "nights_sleep_disturbed": 6,
    "oozing_honey_crusts": false,
    "steroid_use_last_2weeks": true,
    "moisturizer_frequency": "twice_daily",
    "recent_stress_level": 7
  }
}
```

## Clinical Decision Support

Based on responses, the AI will:

1. **DDx Analysis:** Rule out/in conditions:
   - Scabies (Q5)
   - Contact Dermatitis (Q6)
   - Psoriasis (Q7)
   - Seborrheic Dermatitis (Q4)

2. **AD Likelihood Score:** Based on:
   - Pruritus (Q1)
   - Chronicity (Q2)
   - Atopic history (Q3)
   - Distribution (Q4)

3. **Severity Assessment:** Based on:
   - Sleep disruption (Q8)
   - Infection risk (Q9)
   - Treatment response (Q10)
   - CNN image analysis

4. **Treatment Recommendations:** Personalized based on:
   - Current treatment (Q10)
   - Adherence (Q11)
   - Stress levels (Q12)
   - DDx results
