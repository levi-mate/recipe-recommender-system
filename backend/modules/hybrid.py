import traceback
import random

from config import DEFAULT_TARGET_CALORIES, MAX_RESULTS, CONTENT_WEIGHT
from modules.content import generate_content_recommendations
from modules.collab import generate_collaborative_recommendations

# Hybrid Recommendation System

# Combines content based and collaborative filtering to give personalised recommendations with some exploration for recipe diversity
# Uses the strengths of both systems while mitigating their individual weaknesses

# Key features:
# - Combines recommendations from content-based and collaborative filtering systems
# - Prioritises recipes that appear in both recommendation systems
# - Maintains balance between ingredient based and popularity based recommendations
# - Preserves meal type categorisation and calorie targets
# - Provides consistent multi day meal planning with diverse recipe selection

# The hybrid approach allows for:
# - Better handling of the cold start problem than pure collaborative filtering
# - Higher relevance for users with established preferences
# - Balance between familiar ingredients and recipe discovery
# - Improved personalisation by considering both user ingredients and similar users preferences

# Algorithm details:
# - First prioritises recipes recommended by both systems
# - Then fills remaining slots using a ratio (60% content-based, 40% collaborative)
# - Randomly selects from each system's unique recommendations for variety
# - Preserves the daily structure with breakfast, lunch and dinner recommendations


def hybrid_recommendations(user_id, days = 1, num_recommendations = MAX_RESULTS, target_calories = DEFAULT_TARGET_CALORIES):
    try:
        print("Generating content-based recommendations...")
        content_recommendations = generate_content_recommendations(user_id, days = days, num_recommendations = num_recommendations, target_calories = target_calories)
        print("Content-based recommendations generated.")

        print("Generating collaborative filtering recommendations...")
        collaborative_recommendations = generate_collaborative_recommendations(user_id, days = days, num_recommendations = num_recommendations, target_calories = target_calories)
        print("Collaborative filtering recommendations generated.")

        print("Combining content-based and collaborative filtering recommendations...")
        combined_recommendations = []

        for day in range(days):
            breakfast_ids = combine_recommendations(
                content_recommendations["days"][day]["breakfast"],
                collaborative_recommendations[day]["breakfast"]
            )
            
            lunch_ids = combine_recommendations(
                content_recommendations["days"][day]["lunch"],
                collaborative_recommendations[day]["lunch"]
            )
            
            dinner_ids = combine_recommendations(
                content_recommendations["days"][day]["dinner"],
                collaborative_recommendations[day]["dinner"]
            )
            
            print(f"Hybrid breakfast recipes: {breakfast_ids}")
            content_breakfast_ids = [r["recipe_id"] if isinstance(r, dict) else r for r in content_recommendations["days"][day]["breakfast"]]
            collab_breakfast_ids = collaborative_recommendations[day]["breakfast"]
            print(f"Content breakfast recipes: {content_breakfast_ids}")
            print(f"Collab breakfast recipes: {collab_breakfast_ids}")
            
            day_recommendations = {
                "breakfast": breakfast_ids,
                "lunch": lunch_ids,
                "dinner": dinner_ids,
            }

            combined_recommendations.append(day_recommendations)

        return {"days": combined_recommendations}
    
    except Exception as e:
        print(f"[ERROR] Hybrid recommendation system failed: {e}")
        traceback.print_exc()

        raise


def combine_recommendations(content_recipes, collaborative_recipes, content_ratio = CONTENT_WEIGHT):
    if not collaborative_recipes:
        return [r["recipe_id"] if isinstance(r, dict) else r for r in content_recipes[:MAX_RESULTS]]
    
    content_ids = [r["recipe_id"] if isinstance(r, dict) else r for r in content_recipes]
    collab_ids = list(collaborative_recipes) if collaborative_recipes else []
    
    overlap_ids = list(set(content_ids).intersection(set(collab_ids)))
    print(f"Found {len(overlap_ids)} recipes in both recommendation systems: {overlap_ids}")
    
    result = overlap_ids.copy()
    
    remaining_slots = MAX_RESULTS - len(result)
    
    if remaining_slots > 0:
        remaining_content_count = int(remaining_slots * content_ratio)
        remaining_collab_count = remaining_slots - remaining_content_count
        
        unique_content_ids = [r for r in content_ids if r not in overlap_ids]
        unique_collab_ids = [r for r in collab_ids if r not in overlap_ids]
        
        if unique_content_ids and remaining_content_count > 0:
            selected_content = random.sample(unique_content_ids, min(remaining_content_count, len(unique_content_ids)))
            result.extend(selected_content)

            print(f"Added {len(selected_content)} randomly selected content recipes")
        
        if unique_collab_ids and remaining_collab_count > 0:
            selected_collab = random.sample(unique_collab_ids, min(remaining_collab_count, len(unique_collab_ids)))
            result.extend(selected_collab)

            print(f"Added {len(selected_collab)} randomly selected collaborative recipes")
    
    if len(result) > MAX_RESULTS:
        result = random.sample(result, MAX_RESULTS)
    
    content_count = len([r for r in result if r in content_ids and r not in collab_ids])
    collab_count = len([r for r in result if r in collab_ids and r not in content_ids])
    both_count = len([r for r in result if r in content_ids and r in collab_ids])
    
    print(f"Final selection: {len(result)} recipes")
    print(f"Source breakdown: {both_count} from both systems, {content_count} from content only, {collab_count} from collaborative only")
    
    return result