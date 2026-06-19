import json
import os
from typing import Optional
from collections import Counter

_LEARNING_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "learning_state")
os.makedirs(_LEARNING_DIR, exist_ok=True)


class LearningState:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.filepath = os.path.join(_LEARNING_DIR, f"user_{user_id}.json")
        self.data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "user_id": self.user_id,
            "iteration": 0,
            "topic_weights": {},
            "pattern_accuracy": {},
            "teacher_fingerprint_history": [],
            "feedback_log": [],
            "confidence_evolution": [],
        }

    def save(self):
        self.data["iteration"] += 1
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def get_weight(self, topic: str) -> float:
        w = self.data["topic_weights"].get(topic, {})
        return w.get("current", 50.0)

    def get_pattern_accuracy(self, pattern: str) -> float:
        return self.data["pattern_accuracy"].get(pattern, 50.0)

    def get_confidence_trend(self) -> list[float]:
        return self.data["confidence_evolution"][-10:]

    def register_feedback(self, topic: str, correct: bool, partial: bool = False):
        current = self.data["topic_weights"].get(topic, {"current": 50.0, "history": []})
        prev = current["current"]

        if correct:
            new_weight = min(100, prev + 12)
        elif partial:
            new_weight = prev + 3
        else:
            new_weight = max(5, prev - 15)

        current["current"] = round(new_weight, 1)
        current["history"] = (current.get("history", []) + [round(new_weight, 1)])[-20:]
        self.data["topic_weights"][topic] = current
        self.data["feedback_log"].append({
            "topic": topic, "correct": correct, "partial": partial,
            "weight_before": prev, "weight_after": new_weight,
        })
        if len(self.data["feedback_log"]) > 200:
            self.data["feedback_log"] = self.data["feedback_log"][-200:]

    def register_pattern_feedback(self, pattern: str, accurate: bool):
        current = self.data["pattern_accuracy"].get(pattern, 50.0)
        new_val = min(100, current + 8) if accurate else max(5, current - 10)
        self.data["pattern_accuracy"][pattern] = round(new_val, 1)

    def record_confidence(self, confidence: float):
        self.data["confidence_evolution"].append(round(confidence, 1))
        if len(self.data["confidence_evolution"]) > 50:
            self.data["confidence_evolution"] = self.data["confidence_evolution"][-50:]

    def record_fingerprint(self, fingerprint: dict):
        self.data["teacher_fingerprint_history"].append({
            "style": fingerprint.get("teaching_style", ""),
            "timestamp": len(self.data["teacher_fingerprint_history"]) + 1,
        })
        if len(self.data["teacher_fingerprint_history"]) > 30:
            self.data["teacher_fingerprint_history"] = self.data["teacher_fingerprint_history"][-30:]

    def get_learning_report(self) -> dict:
        weights = self.data["topic_weights"]
        patterns = self.data["pattern_accuracy"]
        feedback = self.data["feedback_log"]

        boosted = []
        decreased = []
        for topic, w in weights.items():
            history = w.get("history", [])
            if len(history) >= 2 and history[-1] > history[0]:
                boosted.append({"topic": topic, "weight": w["current"], "improvement": round(history[-1] - history[0], 1)})
            elif len(history) >= 2 and history[-1] < history[0]:
                decreased.append({"topic": topic, "weight": w["current"], "drop": round(history[0] - history[-1], 1)})

        boosted.sort(key=lambda x: x["improvement"], reverse=True)
        decreased.sort(key=lambda x: x["drop"], reverse=True)

        confidence_trend = self.data["confidence_evolution"]
        avg_recent = sum(confidence_trend[-5:]) / max(len(confidence_trend[-5:]), 1) if confidence_trend else 50

        style_changes = []
        fp_history = self.data["teacher_fingerprint_history"]
        if len(fp_history) >= 2:
            first = fp_history[0].get("style", "")
            last = fp_history[-1].get("style", "")
            if first != last:
                style_changes.append({"from": first, "to": last, "confidence": "Style stabilized" if len(fp_history) >= 5 else "Still learning"})

        return {
            "iteration": self.data["iteration"],
            "total_feedback_entries": len(feedback),
            "updated_high_value_topics": boosted[:8],
            "decreased_topics": decreased[:5],
            "new_detected_patterns": [{"pattern": p, "accuracy": a} for p, a in patterns.items() if a > 60][:6],
            "confidence_trend": {
                "recent_avg": round(avg_recent, 1),
                "samples": len(confidence_trend),
                "trend": "improving" if len(confidence_trend) >= 3 and confidence_trend[-1] > confidence_trend[0] else "stable",
            },
            "teacher_fingerprint_update": {
                "style_changes": style_changes,
                "iterations_observed": len(fp_history),
            },
        }

    def apply_learning_to_topics(self, base_topics: list[dict]) -> list[dict]:
        adjusted = []
        for topic in base_topics:
            name = topic.get("concept", topic.get("concept", ""))
            base_score = topic.get("prediction_score", topic.get("intensity", 50))
            learned_weight = self.get_weight(name)
            adjustment = (learned_weight - 50) * 0.3
            new_score = max(5, min(100, base_score + adjustment))

            topic_copy = dict(topic)
            topic_copy["prediction_score"] = round(new_score)
            topic_copy["learning_adjustment"] = round(adjustment, 1)
            topic_copy["feedback_weight"] = learned_weight
            adjusted.append(topic_copy)

        return sorted(adjusted, key=lambda x: x["prediction_score"], reverse=True)
