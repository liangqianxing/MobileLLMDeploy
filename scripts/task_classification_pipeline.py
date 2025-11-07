"""End-to-end pipeline for task classification experiment.

Stages:
    fetch   - download and normalise public corpora (XSum, CoNLL-2014)
    label   - merge human labels, optional LLM auto-label, produce review queues
    train   - fit baseline classifiers (logistic regression, gradient boosting)
    evaluate- compute metrics on holdout sets and dump reports
    all     - run fetch -> label -> train -> evaluate sequentially

Usage examples:
    python task_classification_pipeline.py --stage fetch --max-samples 500
    python task_classification_pipeline.py --stage label --llm-config configs/labeler.yaml
    python task_classification_pipeline.py --stage train --model logistic_regression
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from datasets import Dataset, load_dataset
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


LOGGER = logging.getLogger("task_classifier")


DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LABEL_DIR = DATA_DIR / "labels"
MODEL_DIR = Path("models") / "task_classifier"
REPORT_DIR = Path("reports")


TAXONOMY_FIELDS = [
    "complexity",
    "latency",
    "privacy",
    "knowledge",
    "device_load",
]


@dataclass
class SampleRecord:
    """Normalised representation of a task sample."""

    sample_id: str
    source: str
    query: str
    context: Optional[str] = None
    reference: Optional[str] = None


@dataclass
class TaskLabel:
    """Structured label covering all taxonomy axes."""

    complexity: str
    latency: str
    privacy: str
    knowledge: str
    device_load: str
    confidence: float
    source: str
    justification: Optional[str] = None


def ensure_directories() -> None:
    for path in (RAW_DIR, PROCESSED_DIR, LABEL_DIR, MODEL_DIR, REPORT_DIR):
        path.mkdir(parents=True, exist_ok=True)


def save_jsonl(path: Path, records: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_local_samples(
    path: Path,
    source: str,
    query_key: str,
    reference_key: str,
    *,
    max_samples: int = 0,
    id_key: Optional[str] = None,
) -> List[SampleRecord]:
    records = load_jsonl(path)
    if max_samples:
        records = records[: max_samples]
    samples: List[SampleRecord] = []
    for idx, row in enumerate(records):
        sample_id = row.get(id_key) if id_key and row.get(id_key) else f"{source}-{idx}"
        query = row.get(query_key) or row.get("query") or ""
        reference = row.get(reference_key) or row.get("reference")
        samples.append(
            SampleRecord(
                sample_id=str(sample_id),
                source=source,
                query=query,
                context=row.get("context"),
                reference=reference,
            )
        )
    return samples


def fetch_xsum(max_samples: int) -> List[SampleRecord]:
    local_path = RAW_DIR / "xsum_test.jsonl"
    if local_path.exists():
        LOGGER.info("Loading XSum samples from %s", local_path)
        return load_local_samples(
            local_path,
            source="xsum",
            query_key="document",
            reference_key="summary",
            max_samples=max_samples,
            id_key="id",
        )

    LOGGER.info("Local XSum file not found; falling back to Hugging Face Hub")
    dataset = load_dataset("xsum", split="test")
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    samples: List[SampleRecord] = []
    for idx, row in enumerate(dataset):
        samples.append(
            SampleRecord(
                sample_id=f"xsum-{idx}",
                source="xsum",
                query=row["document"],
                context=None,
                reference=row.get("summary"),
            )
        )
    return samples


def fetch_conll(max_samples: int) -> List[SampleRecord]:
    local_candidates = [
        ("conll2014_test.jsonl", "conll2014", "original", "corrected"),
        ("jfleg_test.jsonl", "jfleg", "sentence", "correction"),
    ]
    for filename, source, query_key, reference_key in local_candidates:
        path = RAW_DIR / filename
        if path.exists():
            LOGGER.info("Loading grammar dataset from %s", path)
            return load_local_samples(
                path,
                source=source,
                query_key=query_key,
                reference_key=reference_key,
                max_samples=max_samples,
            )

    LOGGER.info("Local grammar dataset not found; falling back to jfleg on Hugging Face Hub")
    dataset = load_dataset("jfleg", split="test")
    if max_samples:
        dataset = dataset.select(range(min(max_samples, len(dataset))))
    samples: List[SampleRecord] = []
    for idx, row in enumerate(dataset):
        samples.append(
            SampleRecord(
                sample_id=f"jfleg-{idx}",
                source="jfleg",
                query=row.get("sentence") or "",
                context=None,
                reference=row.get("correction"),
            )
        )
    return samples


def merge_samples(
    public_samples: List[SampleRecord], custom_path: Optional[Path]
) -> List[SampleRecord]:
    samples = list(public_samples)
    if custom_path and custom_path.exists():
        for item in load_jsonl(custom_path):
            samples.append(
                SampleRecord(
                    sample_id=item["sample_id"],
                    source=item.get("source", "app"),
                    query=item["query"],
                    context=item.get("context"),
                    reference=item.get("reference"),
                )
            )
    return samples


def run_fetch(max_samples: int, app_data: Optional[Path]) -> None:
    LOGGER.info("Fetching public datasets...")
    xsum_samples = fetch_xsum(max_samples)
    conll_samples = fetch_conll(max_samples)
    combined = merge_samples(xsum_samples + conll_samples, app_data)
    save_jsonl(
        PROCESSED_DIR / "combined_samples.jsonl",
        (asdict(sample) for sample in combined),
    )
    LOGGER.info("Saved %d samples to %s", len(combined), PROCESSED_DIR)


class LabelingStrategy:
    """Base class for auto-labeling strategies."""

    def label(self, sample: SampleRecord) -> Optional[TaskLabel]:
        raise NotImplementedError


class KeywordHeuristicLabeler(LabelingStrategy):
    """Fallback labeler that uses simple heuristics."""

    FAST_KEYWORDS = {"now", "immediately", "urgent", "real-time", "实时"}
    PRIVACY_KEYWORDS = {"privacy", "personal", "密码", "account"}
    KNOWLEDGE_KEYWORDS = {"cite", "source", "reference", "百科", "explain"}

    def label(self, sample: SampleRecord) -> TaskLabel:
        query = sample.query.lower()
        complexity = "complex" if len(query.split()) > 80 else "simple"
        latency = "realtime" if any(word in query for word in self.FAST_KEYWORDS) else "relaxed"
        privacy = "private" if any(word in query for word in self.PRIVACY_KEYWORDS) else "public"
        knowledge = "high" if any(word in query for word in self.KNOWLEDGE_KEYWORDS) else "low"
        device_load = "heavy" if complexity == "complex" else "light"
        return TaskLabel(
            complexity=complexity,
            latency=latency,
            privacy=privacy,
            knowledge=knowledge,
            device_load=device_load,
            confidence=0.35,
            source="heuristic",
            justification="keyword fallback",
        )


def run_label(manual_labels_path: Optional[Path], use_heuristic: bool) -> None:
    samples = [SampleRecord(**row) for row in load_jsonl(PROCESSED_DIR / "combined_samples.jsonl")]

    manual_labels: Dict[str, dict] = {}
    if manual_labels_path and manual_labels_path.exists():
        manual_labels = {row["sample_id"]: row for row in load_jsonl(manual_labels_path)}
        LOGGER.info("Loaded %d manual labels", len(manual_labels))

    heuristic = KeywordHeuristicLabeler() if use_heuristic else None
    label_records: List[dict] = []
    review_queue: List[dict] = []

    for sample in samples:
        if sample.sample_id in manual_labels:
            record = manual_labels[sample.sample_id]
            record["source"] = record.get("source", "human")
            label_records.append({**record, "sample_id": sample.sample_id})
            continue

        label_obj: Optional[TaskLabel] = heuristic.label(sample) if heuristic else None
        if label_obj:
            label_records.append({**asdict(label_obj), "sample_id": sample.sample_id})
        else:
            review_queue.append(asdict(sample))

    save_jsonl(LABEL_DIR / "labels.jsonl", label_records)
    LOGGER.info("Saved %d labels to %s", len(label_records), LABEL_DIR)
    if review_queue:
        save_jsonl(LABEL_DIR / "manual_review_queue.jsonl", review_queue)
        LOGGER.info("Queued %d samples for manual review", len(review_queue))


def _basic_feature_frame(samples: List[SampleRecord]) -> pd.DataFrame:
    records: List[Dict[str, str]] = []
    for sample in samples:
        text = sample.query
        records.append(
            {
                "sample_id": sample.sample_id,
                "source": sample.source,
                "length": len(text.split()),
                "has_question": "?" in text,
                "has_now": "now" in text.lower(),
                "text": text,
            }
        )
    return pd.DataFrame.from_records(records)


def _labels_frame(labels: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(labels)
    if "source" in df.columns:
        df = df.rename(columns={"source": "label_source"})
    return df.set_index("sample_id")


def train_baseline(
    samples: List[SampleRecord],
    labels: List[dict],
    model_name: str,
) -> Tuple[Pipeline, Dict[str, dict]]:
    features = _basic_feature_frame(samples)
    labels_df = _labels_frame(labels)
    merged = features.join(labels_df, on="sample_id", how="inner")

    X = merged[["source", "length", "has_question", "has_now", "text"]]
    reports: Dict[str, dict] = {}
    trained_models: Dict[str, Pipeline] = {}

    for axis in TAXONOMY_FIELDS:
        y = merged[axis]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        numeric_features = ["length"]
        categorical_features = ["source", "has_question", "has_now"]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
            ],
            remainder="drop",
        )

        if model_name == "logistic_regression":
            estimator = LogisticRegression(max_iter=1000)
        elif model_name == "decision_tree":
            estimator = DecisionTreeClassifier(max_depth=8)
        else:
            raise ValueError(f"Unsupported model {model_name}")

        clf = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", estimator),
            ]
        )
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        reports[axis] = report
        trained_models[axis] = clf

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    for axis, clf in trained_models.items():
        path = MODEL_DIR / f"{model_name}_{axis}.joblib"
        try:
            import joblib

            joblib.dump(clf, path)
        except ImportError:
            LOGGER.warning("joblib not installed; skipping model export for %s", axis)

    return clf, reports


def run_train(model_name: str) -> Dict[str, dict]:
    samples = [SampleRecord(**row) for row in load_jsonl(PROCESSED_DIR / "combined_samples.jsonl")]
    labels = load_jsonl(LABEL_DIR / "labels.jsonl")
    _, reports = train_baseline(samples, labels, model_name)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    save_jsonl(
        REPORT_DIR / f"{model_name}_metrics.jsonl",
        ({"axis": axis, **metrics["weighted avg"]} for axis, metrics in reports.items()),
    )
    LOGGER.info("Saved metrics to %s", REPORT_DIR)
    return reports


def run_evaluate(model_name: str) -> None:
    samples = [SampleRecord(**row) for row in load_jsonl(PROCESSED_DIR / "combined_samples.jsonl")]
    labels = load_jsonl(LABEL_DIR / "labels.jsonl")
    _, reports = train_baseline(samples, labels, model_name)
    LOGGER.info("Evaluation complete for %s", model_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Task classification experiment pipeline")
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=["fetch", "label", "train", "evaluate", "all"],
    )
    parser.add_argument("--max-samples", type=int, default=0, help="Limit samples per public dataset")
    parser.add_argument("--app-data", type=Path, default=None, help="Path to app requests JSONL")
    parser.add_argument("--manual-labels", type=Path, default=None, help="Pre-annotated labels JSONL")
    parser.add_argument(
        "--model",
        type=str,
        default="logistic_regression",
        choices=["logistic_regression", "decision_tree"],
        help="Classifier to train/evaluate",
    )
    parser.add_argument(
        "--use-heuristic",
        action="store_true",
        help="Enable heuristic auto-labeling when no manual label is present",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s - %(message)s",
    )
    ensure_directories()

    if args.stage in ("fetch", "all"):
        run_fetch(args.max_samples, args.app_data)
    if args.stage in ("label", "all"):
        run_label(args.manual_labels, args.use_heuristic)
    if args.stage in ("train", "all"):
        run_train(args.model)
    if args.stage in ("evaluate", "all"):
        run_evaluate(args.model)


if __name__ == "__main__":
    main()
