# Failed Experiments & Development Journey

This document chronicles all experimental approaches attempted during development of the Skinopathy Atopic Dermatitis v2 system. Understanding what didn't work is as important as knowing what does.

**Current Production System** (Dec 11, 2025):
- **Core**: Streamlined 2-agent architecture (CNN + Vision AI) with simplified reporting
- **Features**: PDF export, activation channel saliency visualization, HCP UI improvements
- **Performance**: 2-3 minutes total analysis time (down from 7-9 minutes with EASI agent)
- **Status**: ✅ Main branch stable, develop branch with all features + timer fix

---

## Summary of Failed Experiments

| Experiment | Status | Reason for Removal | Performance Impact |
|-----------|--------|-------------------|-------------------|
| **EASI Scoring Agent** | ❌ Removed | Too slow (7-9 min), added complexity without proportional value | +60-70% speed improvement after removal |
| **2-Stage Analysis Pipeline** | ❌ Abandoned | Overly complex, no clear benefit, maintenance burden | - |
| **Activation Channel Maps** | ❌ Replaced | Experimental alternative to GradCAM, unclear advantage | - |
| **Custom PostgreSQL Changes** | ❌ Reverted | Database-specific optimizations didn't significantly improve performance | - |
| **VLM Service** | ❌ Deprecated | Replaced by direct Gemini vision agent integration | - |
| **Separate Clinical Note Service** | ❌ Removed | Now integrated directly into report generation | - |

---

## Detailed Experiment Analysis

### 1. EASI Scoring Agent (REMOVED)

**Duration**: Nov 2024 - Dec 2024
**Status**: ❌ Failed - Removed in final cleanup
**Files Removed**:
- `backend/app/agents/easi_agent.py`
- `backend/app/prompts/easi_agent_prompts.py`

#### What We Tried
- Created a dedicated Gemini 1.5 Pro agent to calculate formal EASI scores
- Agent would analyze CNN results + Vision AI findings + questionnaire data
- Attempted to provide region-specific EASI breakdowns (head/neck, trunk, upper/lower extremities)
- Used RAG to enhance EASI scoring accuracy with medical literature

#### Why It Failed
1. **Performance Impact**: Added 3-5 minutes to total processing time
   - Pipeline was taking 7-9+ minutes with EASI agent
   - After removal: 2-3 minutes expected
   - **60-70% speed improvement**

2. **Diminishing Returns**: EASI score didn't add enough value for the cost
   - CNN already provides severity score (0-100)
   - Vision AI already provides clinical assessment
   - EASI score was essentially redundant for MVP purposes

3. **User Feedback**: Users explicitly requested simpler, faster results
   - Direct quote: "Lets show only the results of the CNN and Vision AI... No EASI score"
   - Focus shifted to speed and actionability over comprehensive clinical scoring

4. **API Costs**: Additional Gemini API call per analysis
   - Estimated $0.001-0.002 per EASI scoring call
   - Adds up at scale

#### Lessons Learned
- **Speed matters more than completeness** for user engagement
- **Redundant metrics confuse rather than help** end users
- **Consider MVP scope carefully** - full clinical scoring can wait for v2

#### Configuration Reference
Agent configuration preserved in `backend/app/config/agent_config.py` (lines 89-102):
```python
EASI_AGENT_CONFIG_GEMINI = AgentConfig(
    name="EASI Scoring Specialist",
    role=AgentRole.EASI,
    model="gemini-2.5-flash",
    temperature=0.1,  # Very deterministic for scoring
    max_tokens=6000,
    cost_per_1m_input=0.075,
    cost_per_1m_output=0.30,
    ...
)
```

---

### 2. Two-Stage Analysis Pipeline (ABANDONED)

**Duration**: Oct-Nov 2024
**Status**: ❌ Abandoned early
**Files**: No trace remaining (cleaned up before final version)

#### What We Tried
- Attempted a two-stage processing approach:
  1. **Stage 1**: Quick preliminary analysis (CNN only)
  2. **Stage 2**: Deep analysis (Vision AI + EASI + full report)
- Goal was to provide "fast preview" to users while deep analysis continued

#### Why It Failed
1. **Complexity without benefit**: Added state management complexity
   - Had to track which stage each session was in
   - Polling logic became complicated
   - Error handling was nightmarish

2. **User confusion**: Two different results confused users
   - "Is this my final result or preliminary?"
   - Led to support questions and trust issues

3. **No real speed benefit**: Stage 1 wasn't actually that fast
   - CNN alone: ~20-30 seconds
   - Full pipeline (after optimization): 2-3 minutes
   - The "preview" didn't save enough time to justify complexity

#### Lessons Learned
- **Simple is better than clever** for MVP
- **User experience trumps technical elegance**
- **Don't optimize prematurely** - get baseline working first

---

### 3. Activation Channel Maps (REPLACED)

**Duration**: Nov 2024
**Status**: ❌ Replaced with simplified approach
**File Removed**: `backend/app/services/activation_map_service.py`

#### What We Tried
- Experimented with different CNN visualization techniques
- Tried "activation channel" approach as alternative to Grad-CAM
- Goal was to provide better saliency maps for explainability

#### Why It Failed
1. **Unclear advantage** over standard Grad-CAM
   - Activation channels didn't provide meaningfully better visualizations
   - Harder to interpret for non-technical users

2. **Implementation complexity**
   - Required different model architecture considerations
   - More computation required

3. **Grad-CAM was "good enough"**
   - Standard Grad-CAM already well-understood
   - Better tooling and community support
   - Easier to maintain

#### Current Approach
- Simplified saliency map generation
- Standard Grad-CAM approach
- Saliency map generation no longer blocks report delivery

#### Lessons Learned
- **Standard approaches exist for a reason** - battle-tested
- **User-facing explainability** doesn't need cutting-edge techniques
- **Good enough is often perfect** for MVP scope

#### References Kept
Config file still has reference to activation maps (backward compatibility):
- `backend/app/core/config.py` line 100: `ACTIVATION_MAP_LAYER_NAME`

---

### 4. Custom PostgreSQL Optimizations (REVERTED)

**Duration**: Nov 2024
**Status**: ❌ Reverted
**Files Affected**: Database schema, query patterns

#### What We Tried
- Custom indexes for session/report lookups
- Attempted to use PostgreSQL JSON columns more heavily
- Experimented with materialized views for report aggregation

#### Why It Failed
1. **Premature optimization**: Database wasn't the bottleneck
   - API calls to Gemini were 95% of latency
   - Database queries were <50ms even without optimization

2. **Increased complexity**
   - Made migrations more complicated
   - Hard to debug issues
   - No measurable performance gain

3. **Cloud SQL defaults were fine**
   - Google's managed PostgreSQL handles our scale well
   - Connection pooling was sufficient

#### Current Approach
- Standard PostgreSQL setup with simple schema
- Let Cloud SQL handle optimization
- Focus optimization efforts on agent calls, not database

#### Lessons Learned
- **Measure before optimizing** - don't guess where bottlenecks are
- **Managed services** like Cloud SQL are already well-optimized
- **Focus on actual bottlenecks** (API calls in our case)

---

### 5. VLM Service Layer (DEPRECATED)

**Duration**: Oct-Nov 2024
**Status**: ❌ Deprecated and removed
**File Removed**: `backend/app/services/vlm_service.py`

#### What We Tried
- Created abstraction layer for vision-language models
- Supported both local (Qwen) and cloud (Gemini) VLM options
- Goal was flexibility to swap VLM providers

#### Why It Failed
1. **Over-engineered for MVP**
   - Only ever used Gemini in production
   - Local Qwen model was too slow and less accurate
   - Abstraction layer added complexity without value

2. **Direct Gemini integration simpler**
   - Gemini Vision Agent can call Gemini API directly
   - One less layer of indirection
   - Easier to debug and maintain

3. **Provider flexibility not needed**
   - Gemini 1.5 Pro/Flash was sufficient for all use cases
   - Cost was acceptable ($0.001-0.003 per analysis)
   - No compelling reason to switch providers

#### Current Approach
- Direct Vertex AI Gemini integration in Vision Agent
- No VLM abstraction layer
- Simple, straightforward API calls

#### Lessons Learned
- **YAGNI (You Aren't Gonna Need It)** - don't build for flexibility you don't need
- **Abstractions have costs** - maintenance, complexity, debugging
- **Commit to good providers** - Gemini works, stop hedging

---

### 6. Separate Clinical Note Service (REMOVED)

**Duration**: Nov 2024
**Status**: ❌ Removed and integrated
**File Removed**: `backend/app/services/clinical_note_service.py`

#### What We Tried
- Dedicated service for generating SOAP notes
- Separate from main report generation
- Would combine all agent outputs into clinical documentation

#### Why It Failed
1. **Unnecessary separation**
   - SOAP note generation is simple enough to inline
   - No benefit from separate service
   - Just added more files to maintain

2. **Tightly coupled anyway**
   - Always used the same data as HCP report
   - No independent use case
   - Better to keep it in report generation

3. **Simpler approach worked**
   - Integrated SOAP note generation into `_generate_hcp_report()`
   - Single method, clear flow
   - Lines 238-247 in `analysis_service_multiagent.py`

#### Current Approach
```python
def _generate_soap_note(self, cnn_results, vision_findings, questionnaire):
    """Generate SOAP-formatted clinical note"""
    return {
        "subjective": f"Patient reports...",
        "objective": f"CNN Analysis...",
        "assessment": vision_findings.get("assessment", ...),
        "plan": "Continue emollients..."
    }
```

#### Lessons Learned
- **Inline simple logic** - don't create services for everything
- **Composition over distribution** - keep related code together
- **Fewer files = easier navigation**

---

## Current Simplified Architecture (FINAL)

After all experiments, we landed on this production architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Upload Endpoint                       │
│  (Image + 12-question Questionnaire) → /api/v1/upload  │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│          Background Analysis Pipeline (Async)           │
│                                                          │
│  [1/3] CNN + Vision Agent (PARALLEL) ▶ 2-3 minutes    │
│  [2/3] Save AI Results                                  │
│  [3/3] Generate Reports                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   Dual Reports                           │
│                                                          │
│  USER REPORT: CNN severity, lesion count, erythema,    │
│               Vision AI analysis, recommendations        │
│                                                          │
│  HCP REPORT: CNN + Vision AI assessment + SOAP note     │
└─────────────────────────────────────────────────────────┘
```

### Key Features
- **2 agents only**: CNN (EfficientNet-B7) + Vision AI (Gemini 1.5 Pro)
- **Parallel execution**: CNN and Vision AI run concurrently via `asyncio.gather()`
- **Fast**: 2-3 minutes total (down from 7-9 minutes)
- **Simple reports**: User-friendly + HCP clinical (with SOAP note)
- **No EASI**: Removed for speed
- **No 2-stage**: Single coherent pipeline
- **No activation maps blocking**: Saliency maps generated but don't block reports

---

## Performance Metrics (Before vs After)

| Metric | Before (with EASI) | After (Simplified) | Improvement |
|--------|-------------------|-------------------|-------------|
| **Total Time** | 7-9 minutes | 2-3 minutes (est.) | **60-70%** |
| **Agent Count** | 3 (CNN+Vision+EASI) | 2 (CNN+Vision) | -33% |
| **API Calls** | 2-3 Gemini calls | 1 Gemini call | -50 to -66% |
| **Code Complexity** | 8+ service files | 4 service files | -50% |
| **User Confusion** | High (too much info) | Low (focused) | Qualitative |

---

## Lessons Learned (Summary)

1. **Speed > Completeness** for user engagement
2. **Simple > Clever** for maintainability
3. **Measure first**, optimize second
4. **YAGNI** - build what you need, not what you might need
5. **Listen to users** - they told us EASI was too slow
6. **Parallel processing matters** - `asyncio.gather()` gave significant speedup
7. **Good enough is perfect** for MVP scope
8. **Commit to good tools** - Gemini works, stop hedging
9. **Managed services** (Cloud SQL, Cloud Run) handle optimization for you
10. **Document failures** - this file exists because learning matters

---

## Files Cleaned Up

**Deleted in final cleanup (Dec 2024)**:
- `backend/app/agents/easi_agent.py`
- `backend/app/prompts/easi_agent_prompts.py`
- `backend/app/services/activation_map_service.py`
- `backend/app/services/analysis_service.py` (old version)
- `backend/app/services/vlm_service.py`
- `backend/app/services/clinical_note_service.py`
- `backend/app/core/config_gcp.py` (duplicate config)
- `backend/app/prompts/vision_agent_prompts_OLD.py`
- `IMPLEMENTATION_SUMMARY.md` (archived - described pre-v2.0 template-based architecture)
- `DEPLOYMENT_GUIDE.md` (duplicate deployment guide)
- `GCP_DEPLOYMENT.md` (duplicate deployment guide)

**Updated**:
- `backend/app/agents/__init__.py` - removed EASI imports
- `backend/app/services/analysis_service_multiagent.py` - streamlined pipeline

**Kept for reference**:
- `backend/app/config/agent_config.py` - EASI config preserved but not used

---

## Future Considerations

If we revisit these experiments in v2:

1. **EASI Scoring**: Could add as *optional* deep analysis for clinical users
   - Make it opt-in
   - Run it truly async (don't block basic report)
   - Use for research/validation purposes

2. **Two-Stage Analysis**: Could work with better UX
   - Clear messaging: "Quick result ready, detailed analysis in progress"
   - Make stage 2 truly optional (user can get full result or quick result)

3. **Advanced Visualizations**: Revisit when user base requests it
   - Let users tell us what they need
   - A/B test different approaches

4. **Database Optimization**: Only if we hit scale issues
   - Current setup handles 100s of concurrent users fine
   - Revisit at 1000+ concurrent users

---

**Last Updated**: December 7, 2024
**System Version**: v2.0 (Streamlined)
**Deployed**: Cloud Run revision 00019-lh9
