
import os
import json
from dotenv import load_dotenv
from groq import Groq
from utils.ingredient_db import lookup

load_dotenv()

MODEL = "openai/gpt-oss-120b"
API_TIMEOUT = 30.0

SYSTEM_PROMPT = """
You are a food ingredient label analysis assistant.

Analyze only the supplied product label text.
Return valid JSON only, with this structure:

{
  "product_summary": "Short product description",
  "overall_verdict": "Moderate",
  "score": 55,
  "ingredients": [
    {
      "name": "Sugar",
      "category": "sweetener",
      "effect": "negative",
      "label": "LIMIT",
      "explanation": "Added sugar contributes to total sugar intake.",
      "body_systems_affected": ["blood_sugar"]
    }
  ],
  "summary": "Explain the main benefits and concerns.",
  "healthy_ingredients": [],
  "ingredients_to_limit": [],
  "allergens": [],
  "healthier_alternatives": [],
  "recommendations": []
}

LABEL RULES:
- GOOD: Ingredients with established nutritional benefits, such as oats,
  nuts, seeds and whole grains.
- LIMIT: Added sugars, glucose syrups and ingredients high in saturated
  fat when relevant.
- CHECK: Ingredients whose effects depend on quantity or individual needs,
  such as salt and certain fats.
- NEUTRAL: Ingredients primarily used for technical purposes, such as
  flavourings or raising agents, when there is no clear basis for concern.

Each ingredient must include name, category, effect, label,
explanation and body_systems_affected.

Use effect="positive" for GOOD, effect="negative" for LIMIT,
and effect="neutral" for CHECK and NEUTRAL.

Identify each distinct ingredient that is readable in the supplied text.
Preserve ingredient names and INS numbers when present.
Never invent ingredients, quantities, allergens or health effects.
Do not call an ingredient harmful merely because it is artificial.
Do not infer quantities from an ingredient list alone.
Explain concerns without exaggeration.
If the text is unreadable, return an empty ingredients list.

Keep explanations simple and understandable.
Return JSON only, without Markdown fences.
"""


def _compute_score(ingredients):
    """Create an approximate project score from ingredient classifications."""
    if not ingredients:
        return None

    weights = {
        "positive": 1,
        "neutral": 0,
        "negative": -1
    }

    total = sum(
        weights.get(item.get("effect", "neutral"), 0)
        for item in ingredients
    )

    score = round(50 + (total / len(ingredients)) * 50)
    return max(0, min(100, score))


def _verdict_from_score(score):
    if score >= 70:
        return "Healthy"
    if score >= 40:
        return "Moderate"
    return "Unhealthy"


def _augment_with_known_data(analysis):
    """Apply known ingredient information and ensure valid display labels."""
    for item in analysis.get("ingredients", []):
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        known = lookup(name) if name else None

        if known:
            for key in (
                "category",
                "effect",
                "explanation",
                "body_systems_affected"
            ):
                if known.get(key) is not None:
                    item[key] = known[key]

        effect = str(item.get("effect", "neutral")).lower()
        label = str(item.get("label", "")).upper()

        if label not in {"GOOD", "LIMIT", "CHECK", "NEUTRAL"}:
            if effect == "positive":
                label = "GOOD"
            elif effect == "negative":
                label = "LIMIT"
            else:
                label = "NEUTRAL"

        item["label"] = label
        item.setdefault("name", "Unknown ingredient")
        item.setdefault("category", "other")
        item.setdefault("explanation", "No explanation available.")
        item.setdefault("body_systems_affected", [])

    analysis["ingredients"] = [
        item for item in analysis.get("ingredients", [])
        if isinstance(item, dict)
    ]

    return analysis


def _build_insights(analysis):
    """Build ingredient lists for the results page."""
    ingredients = analysis.get("ingredients", [])

    analysis["healthy_ingredients"] = [
        {
            "name": item["name"],
            "explanation": item["explanation"]
        }
        for item in ingredients if item.get("label") == "GOOD"
    ]

    analysis["ingredients_to_limit"] = [
        {
            "name": item["name"],
            "explanation": item["explanation"]
        }
        for item in ingredients
        if item.get("label") in {"LIMIT", "CHECK"}
    ]

    return analysis


def _fallback_analysis(message):
    return {
        "product_summary": "Analysis could not be completed",
        "overall_verdict": "Unknown",
        "score": None,
        "ingredients": [],
        "summary": message,
        "healthy_ingredients": [],
        "ingredients_to_limit": [],
        "allergens": [],
        "healthier_alternatives": [],
        "recommendations": []
    }


def analyze_ingredients(extracted_text):
    if not extracted_text or not extracted_text.strip():
        return _fallback_analysis(
            "No readable ingredient text was provided. "
            "Try another image or enter the ingredients manually."
        )

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        return _fallback_analysis(
            "Groq API key is missing. Check your .env configuration."
        )

    try:
        client = Groq(
            api_key=api_key,
            timeout=API_TIMEOUT,
            max_retries=1
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": extracted_text.strip()}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        raw = response.choices[0].message.content

        if not raw:
            return _fallback_analysis(
                "The AI returned an empty response. Please try again."
            )

        analysis = json.loads(raw)

        if not isinstance(analysis, dict):
            raise ValueError("The AI response was not a JSON object.")

        if not isinstance(analysis.get("ingredients"), list):
            raise ValueError("The AI returned an invalid ingredient list.")

        analysis = _augment_with_known_data(analysis)

        score = _compute_score(analysis["ingredients"])
        analysis["score"] = score

        if score is not None:
            analysis["overall_verdict"] = _verdict_from_score(score)
        else:
            analysis["overall_verdict"] = "Unknown"

        analysis.setdefault("product_summary", "Food ingredient analysis")
        analysis.setdefault(
            "summary", "Review the ingredient details below."
        )

        for key in (
            "allergens",
            "healthier_alternatives",
            "recommendations"
        ):
            if not isinstance(analysis.get(key), list):
                analysis[key] = []

        analysis = _build_insights(analysis)

        return analysis

    except json.JSONDecodeError:
        return _fallback_analysis(
            "The AI response could not be read. Please try again."
        )

    except Exception as error:
        print(f"Ingredient analysis failed: {type(error).__name__}")

        error_text = str(error).lower()
        error_type = type(error).__name__.lower()

        if (
            "authentication" in error_type
            or "invalid_api_key" in error_text
            or "401" in error_text
        ):
            message = (
                "The Groq API key was rejected. Check your .env file "
                "and configure a valid API key."
            )
        elif "rate_limit" in error_type or "rate_limit" in error_text:
            message = "The AI rate limit was reached. Please try again later."
        else:
            message = (
                "AI analysis failed. Check your API key, model availability "
                "and internet connection."
            )

        return _fallback_analysis(message)
