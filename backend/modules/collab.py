import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
import random

from config import DEFAULT_TARGET_CALORIES, MAX_RESULTS
from modules.utils import fetch_user_preferred_categories, fetch_recipe_categories, find_similar_users, get_user_liked_recipes, fetch_recipe_calories, fetch_user_excluded_categories, fetch_interactions, get_meal_calorie_ranges

# Collaborative Filtering

################
# How it works:
################

# Similar Users:
# - Finds users with similar preferences to the target user
# - Recommends recipes that similar users liked, weighted by similarity score
# - Filters recommendations by meal specific calorie ranges

# Model Prediction:
# - Uses the trained LightFM model to predict user-recipe interactions
# - Combines model scores with category preference matching
# - Ensures recipes fit within the calorie range for each meal

# Random Selection:
# - Fallback, when the first two stages don't give enough recommendations
# - Randomly selects recipes within the calorie range
# - Maintains diversity by avoiding previously selected recipes

# Handles new users (cold start problem) by recommending diverse recipes that match calorie targets for each meal type


def build_interaction_matrix(interactions):
    try:
        dataset = Dataset()
        print("Fitting dataset with user and recipe IDs...")

        dataset.fit((interaction[0] for interaction in interactions), (interaction[1] for interaction in interactions))

        print("Dataset fitted")

        print("Building interaction matrix...")
        interactions_matrix, weights_matrix = dataset.build_interactions(((interaction[0], interaction[1], 1 if interaction[2] == "like" else -1) for interaction in interactions))

        print("Interaction matrix built")

        if interactions_matrix.nnz == 0:
            print("[ERROR] Interaction matrix is empty!")

            raise ValueError("Interaction matrix is empty.")
        
        if np.isnan(interactions_matrix.data).any():
            print("[ERROR] Interaction matrix contains NaN values!")

            raise ValueError("Interaction matrix contains NaN values.")

        return dataset, interactions_matrix
    
    except Exception as e:
        print(f"[ERROR] Failed to build interaction matrix: {e}")

        raise

def train_collaborative_filtering_model(interactions_matrix, learning_rate = 0.05, epochs = 5, no_components = 10, item_alpha = 0.0001, user_alpha = 0.0001):
    try:
        model = LightFM(loss = 'logistic', learning_rate = learning_rate, item_alpha = item_alpha, user_alpha = user_alpha, no_components = no_components)
                       
        model.fit(interactions_matrix, epochs = epochs, num_threads = 2, verbose = True)

        print("Collaborative filtering model trained successfully.")

        return model
    
    except Exception as e:
        print(f"[ERROR] Failed to train collaborative filtering model: {e}")

        raise

def recommend_recipes(model, dataset, user_id, num_recommendations = MAX_RESULTS, days = 1, target_calories = DEFAULT_TARGET_CALORIES):
    calorie_ranges = get_meal_calorie_ranges(target_calories)
    
    preferred_categories = fetch_user_preferred_categories(user_id)
    excluded_categories = fetch_user_excluded_categories(user_id)
    recipe_categories = fetch_recipe_categories()
    recipe_calories = fetch_recipe_calories()
    similar_users = find_similar_users(user_id)

    filtered_recipe_categories = {}
    excluded_lower = [cat.lower() for cat in excluded_categories]
    
    for recipe_id, category in recipe_categories.items():
        if category.lower() not in excluded_lower:
            filtered_recipe_categories[recipe_id] = category
    
    recipe_categories = filtered_recipe_categories
    
    recommendations = []
    selected_recipe_ids = set()
    
    for day in range(days):
        day_recommendations = {
            "breakfast": [],
            "lunch": [],
            "dinner": []
        }
        
        if similar_users:
            for similar_user_id, similarity_score, shared_categories in similar_users:
                if similarity_score == 0:
                    continue
                
                liked_recipes = get_user_liked_recipes(similar_user_id)
                
                available_recipes = [r for r in liked_recipes if r not in selected_recipe_ids]
                
                if not available_recipes:
                    continue
                    
                for meal_type, (min_cal, max_cal) in calorie_ranges.items():
                    if len(day_recommendations[meal_type]) >= num_recommendations:
                        continue
                    
                    fitting_recipes = []

                    for recipe_id in available_recipes:
                        calories = recipe_calories.get(recipe_id, 0)

                        if min_cal <= calories <= max_cal:
                            category = recipe_categories.get(recipe_id, "")
                            category_match = 1 if category in preferred_categories else 0
                            recipe_score = similarity_score + category_match
                            fitting_recipes.append((recipe_id, recipe_score, calories))
                    
                    fitting_recipes.sort(key = lambda x: -x[1])
                    
                    for recipe_id, _, _ in fitting_recipes:
                        if recipe_id not in selected_recipe_ids and len(day_recommendations[meal_type]) < num_recommendations:
                            day_recommendations[meal_type].append(recipe_id)
                            selected_recipe_ids.add(recipe_id)
                            available_recipes.remove(recipe_id)
                
        for meal_type, (min_cal, max_cal) in calorie_ranges.items():
            if len(day_recommendations[meal_type]) >= num_recommendations:
                continue
                
            print(f"Still need {num_recommendations - len(day_recommendations[meal_type])} more recipes for {meal_type}")
            
            category_based_recipes = []

            for recipe_id, category in recipe_categories.items():
                if recipe_id in selected_recipe_ids:
                    continue
                    
                calories = recipe_calories.get(recipe_id, 0)

                if min_cal <= calories <= max_cal:
                    category_match = 2 if category in preferred_categories else 0
                    
                    model_score = 0

                    if recipe_id in dataset.mapping()[2]:
                        user_internal_id = dataset.mapping()[0][user_id]
                        recipe_internal_id = dataset.mapping()[2][recipe_id]
                        model_score = model.predict(user_internal_id, [recipe_internal_id])[0]
                    
                    total_score = category_match + model_score
                    category_based_recipes.append((recipe_id, total_score, calories))
            
            category_based_recipes.sort(key = lambda x: -x[1])
            
            for recipe_id, _, _ in category_based_recipes:
                if len(day_recommendations[meal_type]) < num_recommendations:
                    day_recommendations[meal_type].append(recipe_id)
                    selected_recipe_ids.add(recipe_id)
        
        for meal_type, (min_cal, max_cal) in calorie_ranges.items():
            if len(day_recommendations[meal_type]) >= num_recommendations:
                continue
            
            print(f"Falling back to random selection for {meal_type}, need {num_recommendations - len(day_recommendations[meal_type])} more recipes")
            
            available_recipes = []

            for recipe_id, calories in recipe_calories.items():
                if recipe_id not in selected_recipe_ids and min_cal <= calories <= max_cal:
                    available_recipes.append(recipe_id)
            
            if available_recipes:
                random.shuffle(available_recipes)
                
                for recipe_id in available_recipes:
                    if len(day_recommendations[meal_type]) < num_recommendations:
                        day_recommendations[meal_type].append(recipe_id)
                        selected_recipe_ids.add(recipe_id)
                    else:
                        break
            else:
                print(f"[ERROR] Failed to find enough recipes for {meal_type} in calorie range {min_cal:.1f}-{max_cal:.1f}")
        
        primary_meal_calories = sum(recipe_calories.get(day_recommendations[meal_type][0], 0) for meal_type in day_recommendations if day_recommendations[meal_type])
        
        print(f"Day {day+1} recommendations total calories: {primary_meal_calories:.1f} (target: {target_calories})")
        
        print(f"Collaborative filtering selected recipes for Day {day+1}:")
        for meal_type in day_recommendations:
            if day_recommendations[meal_type]:
                top_recipe = day_recommendations[meal_type][0]
                
                print(f"  - {meal_type.capitalize()}: Recipe ID {top_recipe}, {recipe_calories.get(top_recipe, 0):.1f} calories")
                print(f"    Category: {recipe_categories.get(top_recipe, 'Unknown')}")
                print(f"    Alternative options: {len(day_recommendations[meal_type])-1} recipes")
        
        recommendations.append(day_recommendations)
    
    return recommendations


def generate_collaborative_recommendations(user_id, days=1, num_recommendations=MAX_RESULTS, target_calories=DEFAULT_TARGET_CALORIES):
    try:
        interactions = fetch_interactions()
        
        print("Building interaction matrix...")
        dataset, interactions_matrix = build_interaction_matrix(interactions)
        
        print("Training collaborative filtering model...")
        model = train_collaborative_filtering_model(interactions_matrix)
        
        user_in_dataset = user_id in dataset.mapping()[0]
        
        if user_in_dataset:
            print("Generating recommendations based on trained model...")
            recommendations = recommend_recipes(model, dataset, user_id, num_recommendations, days, target_calories)
        else:
            print(f"New user {user_id} has no interaction history. Using fallback recommendations.")
            recommendations = []
            calorie_ranges = get_meal_calorie_ranges(target_calories)
            
            recipe_categories = fetch_recipe_categories()
            recipe_calories = fetch_recipe_calories()
            
            for _ in range(days):
                day_plan = {
                    "breakfast": [],
                    "lunch": [],
                    "dinner": []
                }
                
                for meal_type, (min_cal, max_cal) in calorie_ranges.items():
                    suitable_recipes = []
                    
                    for recipe_id, calories in recipe_calories.items():
                        if min_cal <= calories <= max_cal:
                            suitable_recipes.append(recipe_id)
                    
                    if suitable_recipes:
                        random.shuffle(suitable_recipes)
                        day_plan[meal_type] = suitable_recipes[:num_recommendations]
                    
                recommendations.append(day_plan)
                
            print("Generated fallback recommendations for new user")
            
        return recommendations
    
    except Exception as e:
        print(f"[ERROR] Collaborative filtering failed: {e}")

        return [{"breakfast": [], "lunch": [], "dinner": []} for _ in range(days)]