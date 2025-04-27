from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

from config import DEFAULT_TARGET_CALORIES, MAX_RESULTS
from modules.utils import get_user_ingredients, get_recipes, parse_ingredient_parts, fetch_recipe_details, fetch_user_preferred_categories, fetch_user_excluded_categories, get_meal_calorie_ranges

# Content Based Filtering

################
# How it works:
################

# Text Processing: Uses TF-IDF vectorisation to convert ingredient lists into numerical vectors

# Similarity Calculation: Calculates cosine similarity between user ingredients and recipe ingredients

# Multi-criteria Ranking: Recipes are ranked based on a weighted combination of:
# - Ingredient coverage (what proportion of recipe ingredients the user has)
# - Ingredient similarity (TF-IDF vector similarity)
# - Shopping effort (how many additional ingredients are needed)
# - Category preferences (user's preferred food categories)

# Constraint Satisfaction: Ensures recommendations meet:
# - Excluded category filtering (removes recipes from unwanted categories)
# - Calorie requirements (recipes fit within meal specific calorie ranges for breakfast, lunch and dinner)
# - Daily calorie target (meal combinations meet daily nutritional goal)

# Fallback: When primary recommendations aren't available, uses alternative selection strategies prioritising ingredient coverage and calorie requirements

# The algorithm balances utilising ingredients the user already has, while ensuring nutritional requirements and dietary preferences are met


def calculate_ingredient_coverage(user_ingredients, recipe_ingredients):
    if not recipe_ingredients or not user_ingredients:
        return 0
    
    user_ingredients_lower = [ing.lower() for ing in user_ingredients]
    
    matches = 0

    for ingredient in recipe_ingredients:
        ingredient_lower = ingredient.lower()

        if any(user_ing in ingredient_lower for user_ing in user_ingredients_lower):
            matches += 1
    
    return matches / len(recipe_ingredients)


def calculate_shopping_effort(user_ingredients, recipe_ingredients):
    if not recipe_ingredients:
        return 0
    
    user_ingredients_lower = [ing.lower() for ing in user_ingredients]
    
    missing_ingredients = 0

    for ingredient in recipe_ingredients:
        ingredient_lower = ingredient.lower()

        if not any(user_ing in ingredient_lower for user_ing in user_ingredients_lower):
            missing_ingredients += 1
    
    return missing_ingredients


def generate_content_recommendations(user_id, num_recommendations = MAX_RESULTS, days = 1, target_calories = DEFAULT_TARGET_CALORIES, ingredient_weight = 3.0, category_weight = 1.0):
    preferred_categories = fetch_user_preferred_categories(user_id)
    excluded_categories = fetch_user_excluded_categories(user_id)
    user_ingredients = get_user_ingredients(user_id)
    
    print(f"User has {len(user_ingredients)} ingredients and {len(preferred_categories)} preferred categories")
    
    all_recipes = get_recipes()
    recipes = []

    if excluded_categories:
        excluded_lower = [cat.strip().lower() for cat in excluded_categories]

        for recipe in all_recipes:
            rid, name, category, ingredient_parts, calories = recipe

            if category.strip().lower() not in excluded_lower:
                recipes.append(recipe)
    else:
        recipes = all_recipes

    recipe_data = []
    recipe_ids = []
    recipe_names = []
    recipe_categories = []
    recipe_calories = []
    recipe_ingredients_list = []

    for recipe in recipes:
        rid, name, category, ingredient_parts, calories = recipe
        ingredients = parse_ingredient_parts(ingredient_parts)

        if not ingredients or calories is None or calories <= 0:
            continue

        recipe_data.append(" ".join(ingredients))
        recipe_ids.append(rid)
        recipe_names.append(name)
        recipe_categories.append(category.strip().lower())
        recipe_calories.append(float(calories))
        recipe_ingredients_list.append(ingredients)

    if not recipe_data:
        print("No valid recipes found! Falling back to random recommendations")
        fallback_recipes = recipes[:days * 15]
        meal_plans = []

        for _ in range(days):
            meal_plans.append({
                "breakfast": [r for r in fallback_recipes if r[2].lower() == "breakfast"][:5],
                "lunch": [r for r in fallback_recipes if r[2].lower() == "lunch"][:5],
                "dinner": [r for r in fallback_recipes if r[2].lower() == "dinner"][:5],
            })

        return {"days": meal_plans}

    calorie_ranges = get_meal_calorie_ranges(target_calories)
    total_min_calories = target_calories - 50
    total_max_calories = target_calories + 50

    vectorizer = TfidfVectorizer()
    all_ingredients = [" ".join(user_ingredients)] + recipe_data
    ingredient_vectors = vectorizer.fit_transform(all_ingredients)
    user_vector = ingredient_vectors[0]
    recipe_vectors = ingredient_vectors[1:]
    similarities = cosine_similarity(user_vector, recipe_vectors).flatten()

    ranked_recipes = []

    for i in range(len(recipe_ids)):
        recipe_ingredients = recipe_ingredients_list[i]
        coverage = calculate_ingredient_coverage(user_ingredients, recipe_ingredients)
        shopping_effort = calculate_shopping_effort(user_ingredients, recipe_ingredients)
        
        category_score = 0.3 if recipe_categories[i] in [cat.lower() for cat in preferred_categories] else 0
        
        combined_score = ((coverage * 0.6 * ingredient_weight) + (similarities[i] * 0.2 * ingredient_weight) - (min(1.0, shopping_effort / 10) * 0.2 * ingredient_weight) + (category_score * category_weight))
        
        ranked_recipes.append({
            "recipe_id": recipe_ids[i],
            "recipe_name": recipe_names[i],
            "category": recipe_categories[i],
            "calories": recipe_calories[i],
            "similarity": similarities[i],
            "ingredient_coverage": coverage,
            "shopping_effort": shopping_effort,
            "combined_score": combined_score
        })
    
    ranked_recipes.sort(key = lambda x: -x["combined_score"])
    
    print(f"Top 5 recipes by ingredient usage:")

    for i, recipe in enumerate(ranked_recipes[:5]):
        print(f"  {i + 1}. {recipe['recipe_name']} - Coverage: {recipe['ingredient_coverage']:.2f}, " + f"Shopping: {recipe['shopping_effort']}, Score: {recipe['combined_score']:.2f}")
    
    meal_plans = []
    selected_recipe_ids = []
    
    for day in range(days):
        day_plan = {}
        day_calories = 0
        
        for meal_type, (min_cal, max_cal) in calorie_ranges.items():
            print(f"Selecting {meal_type} with calorie range {min_cal:.1f}-{max_cal:.1f}")
            
            suitable_recipes = [r for r in ranked_recipes if min_cal <= r["calories"] <= max_cal and r["recipe_id"] not in selected_recipe_ids]
            
            if suitable_recipes:
                print(f"Found {len(suitable_recipes)} suitable recipes for {meal_type} calorie range")

                selected_recipes = suitable_recipes[:num_recommendations]
                day_plan[meal_type] = selected_recipes
                selected_recipe_ids.extend([r["recipe_id"] for r in selected_recipes])
                
                if selected_recipes:
                    day_calories += selected_recipes[0]["calories"]

                    print(f"  Selected: {selected_recipes[0]['recipe_name']}, " + f"Coverage: {selected_recipes[0]['ingredient_coverage']:.2f}, " + f"Shopping: {selected_recipes[0]['shopping_effort']}")
            else:
                print(f"No suitable ingredient-matched recipes found for {meal_type}, using alternative recipes within same calorie range")
                
                fallback_candidates = []

                for recipe in recipes:
                    rid, name, category, ingredient_parts, calories = recipe

                    if (calories is not None and min_cal <= float(calories) <= max_cal and rid not in selected_recipe_ids):
                        
                        ingredients = parse_ingredient_parts(ingredient_parts)
                        coverage = calculate_ingredient_coverage(user_ingredients, ingredients)
                        shopping_effort = calculate_shopping_effort(user_ingredients, ingredients)
                        
                        fallback_candidates.append({
                            "recipe_id": rid,
                            "recipe_name": name,
                            "category": category.strip().lower(),
                            "calories": float(calories),
                            "similarity": 0,
                            "ingredient_coverage": coverage,
                            "shopping_effort": shopping_effort,
                            "combined_score": (coverage * 0.7) - (min(1.0, shopping_effort / 10) * 0.3)
                        })
                
                if fallback_candidates:
                    print(f"Found {len(fallback_candidates)} alternative recipes within calorie range {min_cal:.1f}-{max_cal:.1f}")
                    
                    fallback_candidates.sort(key = lambda x: -x["combined_score"])
                    selected_recipes = fallback_candidates[:num_recommendations]
                    day_plan[meal_type] = selected_recipes
                    selected_recipe_ids.extend([r["recipe_id"] for r in selected_recipes])
                    
                    if selected_recipes:
                        if min_cal <= selected_recipes[0]["calories"] <= max_cal:
                            day_calories += selected_recipes[0]["calories"]

                            print(f"  Selected alternative: {selected_recipes[0]['recipe_name']} " + f"({selected_recipes[0]['calories']:.1f} cal), " + f"Coverage: {selected_recipes[0]['ingredient_coverage']:.2f}, " + f"Shopping: {selected_recipes[0]['shopping_effort']}")
                        else:
                            print(f"  WARNING: Selected recipe outside calorie range: {selected_recipes[0]['calories']:.1f} not in {min_cal:.1f}-{max_cal:.1f}")
                else:
                    print(f"No recipes found for {meal_type} calorie range {min_cal:.1f}-{max_cal:.1f}")
                    day_plan[meal_type] = []
        
        if total_min_calories <= day_calories <= total_max_calories:
            print(f"Day plan total calories: {day_calories:.1f} (target: {target_calories})")
        else:
            print(f"Day plan calories ({day_calories:.1f}) outside acceptable range ({total_min_calories:.1f}-{total_max_calories:.1f})")
        
        recipe_ids_to_fetch = [r["recipe_id"] for meal_type in day_plan for r in day_plan[meal_type]]

        if recipe_ids_to_fetch:
            full_recipe_details = fetch_recipe_details(recipe_ids_to_fetch)
            day_plan_with_details = {}

            for meal_type in day_plan:
                day_plan_with_details[meal_type] = []

                for recipe in day_plan[meal_type]:
                    matching_details = [r for r in full_recipe_details if r["recipe_id"] == recipe["recipe_id"]]

                    if matching_details:
                        recipe_detail = matching_details[0]
                        recipe_detail["ingredient_coverage"] = recipe["ingredient_coverage"]
                        recipe_detail["shopping_effort"] = recipe["shopping_effort"]
                        
                        if "calories" in recipe_detail:
                            cal_range = calorie_ranges[meal_type]

                            if not (cal_range[0] <= float(recipe_detail["calories"]) <= cal_range[1]):
                                print(f"  WARNING: Recipe {recipe_detail['recipe_name']} has {recipe_detail['calories']} calories," + f" which is outside the {meal_type} range {cal_range[0]}-{cal_range[1]}")
                            
                        day_plan_with_details[meal_type].append(recipe_detail)
            
            meal_plans.append(day_plan_with_details)
        else:
            print("No recipes selected for this day")

    return {"days": meal_plans}