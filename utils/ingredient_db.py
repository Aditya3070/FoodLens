# Small static knowledge base for very common ingredients.
# Used as a fast, consistent fallback / supplement to the AI analysis so
# results for well-established ingredients don't depend on the model
# re-reasoning about them every single time.

KNOWN_INGREDIENTS = {
    "sugar": {
        "category": "sweetener",
        "body_systems_affected": ["blood_sugar", "liver", "heart"],
        "effect": "negative",
        "explanation": "Spikes blood sugar quickly; regular high intake is linked to fatty liver and heart disease risk."
    },
    "high fructose corn syrup": {
        "category": "sweetener",
        "body_systems_affected": ["liver", "blood_sugar", "heart"],
        "effect": "negative",
        "explanation": "Processed almost entirely by the liver; heavy use is linked to fatty liver and metabolic issues."
    },
    "sodium": {
        "category": "additive",
        "body_systems_affected": ["blood_pressure", "kidneys", "heart"],
        "effect": "negative",
        "explanation": "Excess sodium raises blood pressure over time and adds strain to the kidneys."
    },
    "salt": {
        "category": "additive",
        "body_systems_affected": ["blood_pressure", "kidneys", "heart"],
        "effect": "negative",
        "explanation": "Same as sodium — moderate amounts are fine, but it adds up quickly across packaged foods."
    },
    "trans fat": {
        "category": "fat",
        "body_systems_affected": ["heart", "blood_vessels"],
        "effect": "negative",
        "explanation": "Raises bad cholesterol and lowers good cholesterol; one of the clearest dietary heart-disease risks."
    },
    "palm oil": {
        "category": "fat",
        "body_systems_affected": ["heart"],
        "effect": "negative",
        "explanation": "High in saturated fat; frequent heavy use is linked to raised LDL cholesterol."
    },
    "extra virgin olive oil": {
        "category": "fat",
        "body_systems_affected": ["heart", "blood_vessels"],
        "effect": "positive",
        "explanation": "Rich in monounsaturated fat and antioxidants that support healthy cholesterol levels."
    },
    "olive oil": {
        "category": "fat",
        "body_systems_affected": ["heart"],
        "effect": "positive",
        "explanation": "A heart-healthy fat source associated with lower cardiovascular risk."
    },
    "tomato": {
        "category": "whole_food",
        "body_systems_affected": ["heart", "eyes", "immune_system"],
        "effect": "positive",
        "explanation": "Rich in lycopene and vitamin C, supporting heart health and antioxidant defense."
    },
    "tomatoes": {
        "category": "whole_food",
        "body_systems_affected": ["heart", "eyes", "immune_system"],
        "effect": "positive",
        "explanation": "Rich in lycopene and vitamin C, supporting heart health and antioxidant defense."
    },
    "basil": {
        "category": "whole_food",
        "body_systems_affected": ["immune_system", "gut"],
        "effect": "positive",
        "explanation": "Contains antioxidants and has mild anti-inflammatory properties."
    },
    "onion": {
        "category": "whole_food",
        "body_systems_affected": ["heart", "immune_system"],
        "effect": "positive",
        "explanation": "Contains flavonoids linked to heart health and immune support."
    },
    "citric acid": {
        "category": "preservative",
        "body_systems_affected": ["gut"],
        "effect": "neutral",
        "explanation": "Common natural preservative and flavor enhancer; generally well tolerated in normal amounts."
    },
    "sodium benzoate": {
        "category": "preservative",
        "body_systems_affected": ["gut", "liver"],
        "effect": "negative",
        "explanation": "Safe in small amounts but can form benzene (a carcinogen) when combined with vitamin C; best in moderation."
    },
    "msg": {
        "category": "additive",
        "body_systems_affected": ["brain", "gut"],
        "effect": "neutral",
        "explanation": "Considered safe for most people in normal amounts, though some report sensitivity (headaches, flushing)."
    },
    "artificial sweetener": {
        "category": "sweetener",
        "body_systems_affected": ["gut", "blood_sugar"],
        "effect": "neutral",
        "explanation": "Avoids blood sugar spikes but emerging research suggests it may affect gut bacteria with regular use."
    },
    "whole wheat": {
        "category": "whole_food",
        "body_systems_affected": ["gut", "blood_sugar", "heart"],
        "effect": "positive",
        "explanation": "Fiber slows sugar absorption and supports digestive and heart health."
    },
    "vitamin c": {
        "category": "vitamin",
        "body_systems_affected": ["immune_system", "skin"],
        "effect": "positive",
        "explanation": "Supports immune function and collagen production for skin health."
    },
    "vitamin d": {
        "category": "vitamin",
        "body_systems_affected": ["bones", "immune_system"],
        "effect": "positive",
        "explanation": "Essential for calcium absorption and bone strength; also supports immune function."
    },
    "calcium": {
        "category": "mineral",
        "body_systems_affected": ["bones", "heart"],
        "effect": "positive",
        "explanation": "Key building block for bone strength and plays a role in healthy heart rhythm."
    },
}


def lookup(ingredient_name: str):
    """Case-insensitive best-effort lookup against the known ingredient list."""
    name = ingredient_name.lower().strip()
    if name in KNOWN_INGREDIENTS:
        return KNOWN_INGREDIENTS[name]
    for key, data in KNOWN_INGREDIENTS.items():
        if key in name or name in key:
            return data
    return None
