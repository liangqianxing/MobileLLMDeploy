# Task Classification Experiment Playbook

This guide describes how to design, run, and iterate on the task classification experiment that powers the edge/cloud dispatcher. It turns the high-level idea (“decide whether a user request should stay on-device or go to the cloud”) into a reproducible workflow with well-defined artefacts.

## 1. Taxonomy Design

1. **Dimension list**: complexity (simple/complex), latency sensitivity (realtime/relaxed), privacy sensitivity (public/private), external knowledge dependency (low/high), device capability guard (light/heavy).
2. **Definition sheet**: write a one-page table that explains each label with positive/negative examples from the mobile app domain (≥5 per label). Store the sheet at `docs/task_labels_reference.md`.
3. **Labeling rubric**: convert the definition sheet into bullet rules that annotators and LLM prompts can follow verbatim.

## 2. Dataset Construction

1. **Public corpora**: pull XSum (summarization) and CoNLL‑2014 test (grammar correction) via `datasets`. Keep raw fields plus a normalised `{"query","context","reference"}` triple.
2. **In-app traffic**: export anonymised user queries from the mobile app (strip identifiers, truncate sensitive spans). Store each record as JSON with `{"query","context","metadata"}` where `metadata` includes flags such as channel, language, device.
3. **Balancing**: ensure each taxonomy label has ~200 examples minimum; oversample under-represented categories by data augmentation (paraphrasing) if needed.

## 3. Label Generation Workflow

1. **Golden set**: randomly sample 10% of the corpus (min 300 items) and run human annotation using the rubric. Store in `data/task_labels_golden.jsonl`.
2. **Prompted expansion**: call a high-quality cloud LLM with a structured prompt (see Appendix A) to label the remaining data. Collect both the predicted label per dimension and a self-reported confidence 0–1.
3. **Disagreement loop**: compare LLM labels with a lightweight heuristic classifier (Section 4). For items where `confidence < 0.55` or the heuristic disagrees, send them to human review.
4. **Audit log**: append every labeling action (model/human, timestamp, annotator id) to `data/task_labels_audit.csv` for compliance.

## 4. Feature Engineering & Heuristic Baseline

1. **Textual metrics**: token count, sentence count, Flesch reading ease, presence of question marks, time-sensitive phrases (`today`, `now`), named entity count (via `spacy` or `stanza`).
2. **Intent signals**: embed the query with `sentence-transformers` and cluster to derive coarse intents (“translation”, “summarise”, “chat”). Use cluster ids as categorical features.
3. **External knowledge proxy**: compute cosine similarity to a curated FAQ embedding bank; high similarity may indicate low knowledge dependency.
4. **Heuristic classifier**: start with logistic regression and gradient boosted tree (LightGBM / XGBoost optional) to get fast baselines. Track precision/recall per dimension, especially for `complex → simple` false negatives.

## 5. Model Training and Selection

1. **Split**: 70/15/15 (train/validation/test) stratified on each dimension; maintain a separate hold-out drawn purely from the mobile app traffic.
2. **Models**:
   - Traditional: logistic regression (L2), gradient boosted tree (histogram-based GBM).
   - Lightweight neural: distilled mini transformer (DistilBERT) fine-tuned for multi-label classification.
   - On-device LLM few-shot: evaluate Qwen2.5-1.5B with a 5-shot prompt to see zero-dependency performance.
3. **Metrics**: report micro/macro F1, confusion matrices, latency per model on target device, and memory footprint. Set acceptance guardrail: recall for `complex` ≥0.92, overall latency <50 ms on Snapdragon 8+ Gen1 class hardware.
4. **Model card**: for each candidate, draft a short model card capturing training data, metrics, hardware footprint, and known failure modes.

## 6. Deployment-Oriented Evaluation

1. **Shadow test**: deploy the classifier in “observe only” mode inside the Android app. Log the predicted label, confidence, chosen routing decision, and the actual model used.
2. **A/B buckets**: create three buckets—(A) heuristic-only, (B) classifier + rules, (C) cloud fallback baseline—and roll out to small user cohorts.
3. **Success monitoring**: for misrouted tasks (user feedback negative, manual override), capture ground-truth label and add to the retraining pool.
4. **Energy tracking**: correlate device power stats (via `scripts/android_collect_batterystats.ps1`) with routing decisions to validate energy savings claims.

## 7. Reporting Template

Include the following elements in each iteration report:

- Experiment setup table (models, thresholds, datasets, hardware).
- Aggregate metrics per dimension and overall routing accuracy.
- Latency / energy / network transfer plots (P50, P95).
- Error analysis notes with example misclassifications and remediation ideas.
- Backlog of improvements (prompt tuning, new features, privacy guardrails).

## 8. Implementation Checklist

1. Prepare dataset folders: `data/raw/`, `data/processed/`, `data/labels/`, `models/task_classifier/`.
2. Run `python scripts/task_classification_pipeline.py --stage fetch` to download public corpora.
3. Import anonymised app logs into `data/raw/app_requests.jsonl`.
4. Execute `--stage label` to generate LLM labels and produce review queues.
5. Use `--stage train` with `--model logistic_regression` or `--model gradient_boosting` to fit baselines.
6. Evaluate on hold-out via `--stage evaluate` to emit metrics JSON (`reports/task_classifier_metrics.json`).
7. Package the selected classifier into an Android-friendly format (ONNX or TFLite) using the conversion helpers (to be added in a follow-up).

## Appendix A – LLM Labeling Prompt (Skeleton)

```
System prompt:
You are a senior annotation assistant. Follow the taxonomy definitions exactly. Reply with valid JSON.

User prompt:
### TAXONOMY
<paste rubric from docs/task_labels_reference.md>

### SAMPLE
Query: "{query}"
Context: "{context}"

### OUTPUT FORMAT
{"complexity": "simple|complex",
 "latency": "realtime|relaxed",
 "privacy": "public|private",
 "knowledge": "low|high",
 "device_load": "light|heavy",
 "confidence": float between 0 and 1,
 "justification": short reason}
```

This appendix should be updated once the rubric document is finalised.

