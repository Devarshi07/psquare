"""Heart-healthy meal suggestions.

Cuisine-aware, BP-aware, lipid-aware recommendations.
"""
import structlog
from dataclasses import dataclass
from typing import Optional

log = structlog.get_logger()


@dataclass
class MealSuggestion:
    """A meal suggestion."""
    name: str
    description: str
    calories: int
    sodium_mg: Optional[int] = None
    ldl_impact: str = "neutral"  # "lowers", "neutral", "raises"
    why: str = ""  # Personalization reason


# Base meal database
# Organized by cuisine and meal type
MEALS_DB = {
    "north_indian": {
        "breakfast": [
            MealSuggestion(
                name="Oats Porridge with Nuts",
                description="Steel-cut oats cooked with milk, topped with almonds and walnuts",
                calories=350,
                sodium_mg=150,
                ldl_impact="lowers",
                why="Oats contain beta-glucan which reduces LDL; nuts add healthy fats",
            ),
            MealSuggestion(
                name="Poha with Roasted Peanuts",
                description="Flattened rice with mustard seeds, curry leaves, peanuts, and vegetables",
                calories=280,
                sodium_mg=200,
                ldl_impact="neutral",
                why="Light and nutritious, good for heart when prepared with minimal oil",
            ),
            MealSuggestion(
                name="Besan Chilla",
                description="Gram flour pancake with vegetables",
                calories=250,
                sodium_mg=180,
                ldl_impact="neutral",
                why="High protein from besan, vegetables add fiber",
            ),
        ],
        "lunch": [
            MealSuggestion(
                name="Dal Tadka + Brown Rice",
                description="Tempered lentils with garlic and spices, served with brown rice",
                calories=450,
                sodium_mg=300,
                ldl_impact="lowers",
                why="Dal is high in soluble fiber; brown rice has more fiber than white",
            ),
            MealSuggestion(
                name="Chicken / Paneer Salad",
                description="Grilled protein with mixed greens, vegetables, olive oil dressing",
                calories=400,
                sodium_mg=250,
                ldl_impact="neutral",
                why="Lean protein with healthy fats from olive oil",
            ),
            MealSuggestion(
                name="Roti with Moong Dal",
                description="Whole wheat roti with protein-rich green gram dal",
                calories=500,
                sodium_mg=350,
                ldl_impact="neutral",
                why="Complex carbs and protein combination",
            ),
        ],
        "dinner": [
            MealSuggestion(
                name="Grilled Fish / Paneer with Veggies",
                description="Grilled protein with steamed or sautéed vegetables",
                calories=350,
                sodium_mg=200,
                ldl_impact="lowers",
                why="Omega-3 from fish (if using fish) helps heart health",
            ),
            MealSuggestion(
                name="Soup + Roti",
                description="Clear vegetable soup with whole wheat roti",
                calories=300,
                sodium_mg=180,
                ldl_impact="neutral",
                why="Light dinner option, easy to digest",
            ),
        ],
    },
    "south_indian": {
        "breakfast": [
            MealSuggestion(
                name="Ragi Mudde + Sambar",
                description="Finger millet balls with lentil curry",
                calories=320,
                sodium_mg=200,
                ldl_impact="lowers",
                why="Ragi is rich in fiber and calcium; whole grain",
            ),
            MealSuggestion(
                name="Idli with Sambar",
                description="Steamed rice-lentil cakes with lentil curry",
                calories=250,
                sodium_mg=180,
                ldl_impact="neutral",
                why="Fermented idli is light and digestible; pair with vegetables",
            ),
            MealSuggestion(
                name="Upma with Vegetables",
                description="Semolina cooked with vegetables and curry leaves",
                calories=300,
                sodium_mg=220,
                ldl_impact="neutral",
                why="Vegetables add fiber; go easy on coconut",
            ),
        ],
        "lunch": [
            MealSuggestion(
                name="Sambar Rice",
                description="Lentil stew with rice and vegetables",
                calories=450,
                sodium_mg=280,
                ldl_impact="lowers",
                why="Sambar has multiple lentils - great fiber and protein",
            ),
            MealSuggestion(
                name="Rasam + Rice",
                description="Spicy tomato-lentil soup with rice",
                calories=350,
                sodium_mg=300,
                ldl_impact="neutral",
                why="Light and digestive; has anti-inflammatory properties",
            ),
            MealSuggestion(
                name="Leafy Greens + Roti",
                description="Mixed greens (palak, methi, gongura) with roti",
                calories=400,
                sodium_mg=250,
                ldl_impact="lowers",
                why="Leafy greens are rich in potassium, magnesium, fiber",
            ),
        ],
        "dinner": [
            MealSuggestion(
                name="Idiyappam with Egg Curry",
                description="Rice noodle strands with egg curry",
                calories=380,
                sodium_mg=280,
                ldl_impact="neutral",
                why="Light option; egg provides protein",
            ),
            MealSuggestion(
                name="Rasam Soup",
                description="Clear rasam as light dinner",
                calories=200,
                sodium_mg=150,
                ldl_impact="neutral",
                why="Very light, good for digestion, warm",
            ),
        ],
    },
    "vegetarian": {
        "breakfast": [
            MealSuggestion(
                name="Greek Yogurt + Fruits",
                description="Plain Greek yogurt with berries and nuts",
                calories=280,
                sodium_mg=80,
                ldl_impact="lowers",
                why="Probiotics from yogurt; berries are antioxidant-rich",
            ),
            MealSuggestion(
                name="Smoothie Bowl",
                description="Blend of banana, spinach, berries with seeds on top",
                calories=320,
                sodium_mg=100,
                ldl_impact="lowers",
                why="High in antioxidants, fiber, and healthy fats",
            ),
        ],
        "lunch": [
            MealSuggestion(
                name="Buddha Bowl",
                description="Quinoa, roasted vegetables, chickpeas, tahini dressing",
                calories=450,
                sodium_mg=200,
                ldl_impact="lowers",
                why="Complete plant protein from chickpeas; healthy fats from tahini",
            ),
        ],
        "dinner": [
            MealSuggestion(
                name="Lentil Soup + Salad",
                description="Hearty lentil soup with side salad",
                calories=350,
                sodium_mg=180,
                ldl_impact="lowers",
                why="Lentils are excellent for heart health",
            ),
        ],
    },
}


def get_meal_suggestion(
    cuisine: str,
    meal_type: str,
    diet_type: str = "veg",
    bp_target: str = "normal",  # normal, low_sodium
    ldl_target: str = "normal",  # normal, low
    allergies: list[str] = None,
) -> list[MealSuggestion]:
    """Get meal suggestions based on user profile."""
    cuisine = cuisine.lower() if cuisine else "mixed"
    meal_type = meal_type.lower() if meal_type else "lunch"
    diet_type = diet_type.lower() if diet_type else "veg"
    allergies = allergies or []

    # Map cuisine
    if cuisine in ["north indian", "north", "punjabi", "delhi"]:
        cuisine_key = "north_indian"
    elif cuisine in ["south indian", "south", "tamil", "kerala"]:
        cuisine_key = "south_indian"
    elif cuisine == "western":
        cuisine_key = "vegetarian"  # Use western-style meals
    else:
        cuisine_key = "north_indian"  # Default

    # Get meals
    meals = MEALS_DB.get(cuisine_key, MEALS_DB["north_indian"])
    suggestions = meals.get(meal_type, [])

    # Filter by diet type (simple logic for now)
    if diet_type == "non_veg":
        # Add non-veg options would go here
        pass

    # Filter by BP target
    if bp_target == "low_sodium":
        suggestions = [m for m in suggestions if m.sodium_mg and m.sodium_mg < 250]

    # Filter by LDL target
    if ldl_target == "low":
        suggestions = [m for m in suggestions if m.ldl_impact != "raises"]

    # Filter allergies
    if allergies:
        for allergen in allergies:
            suggestions = [m for m in suggestions if allergen.lower() not in m.description.lower()]

    return suggestions[:3]


def format_meals_for_whatsapp(suggestions: list[MealSuggestion], meal_type: str) -> str:
    """Format meal suggestions as WhatsApp message."""
    title = f"🍽️ *Heart-Healthy {meal_type.title()} Suggestions*"

    lines = [title, ""]

    for i, meal in enumerate(suggestions, 1):
        lines.append(f"{i}. *{meal.name}*")
        lines.append(f"   {meal.description}")
        lines.append(f"   ~{meal.calories} cal" + (f" | {meal.sodium_mg}mg Na" if meal.sodium_mg else ""))
        if meal.why:
            lines.append(f"   💡 {meal.why}")
        lines.append("")

    lines.append("Pick one and enjoy! ❤️")

    return "\n".join(lines)


async def suggest_meals(
    user_preferences: dict,
) -> str:
    """Generate meal suggestions as WhatsApp message."""
    cuisine = user_preferences.get("cuisine", "mixed")
    diet_type = user_preferences.get("diet_type", "veg")
    time_of_day = user_preferences.get("time_of_day", "lunch")

    # Determine targets based on user health
    bp = user_preferences.get("systolic_bp", 120)
    ldl = user_preferences.get("ldl", 100)

    bp_target = "low_sodium" if bp >= 140 else "normal"
    ldl_target = "low" if ldl >= 130 else "normal"

    suggestions = get_meal_suggestion(
        cuisine=cuisine,
        meal_type=time_of_day,
        diet_type=diet_type,
        bp_target=bp_target,
        ldl_target=ldl_target,
    )

    return format_meals_for_whatsapp(suggestions, time_of_day)