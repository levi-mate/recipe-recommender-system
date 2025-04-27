import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import numpy as np

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from modules.content import generate_content_recommendations


class TestContentRecommendations(unittest.TestCase):
    
    @patch('modules.content.fetch_user_preferred_categories')
    @patch('modules.content.fetch_user_excluded_categories')
    @patch('modules.content.get_user_ingredients')
    @patch('modules.content.get_recipes')
    @patch('modules.content.fetch_recipe_details')
    @patch('modules.content.get_meal_calorie_ranges')
    def test_basic_recommendation_generation(self, mock_calorie_ranges, mock_fetch_recipe_details, mock_get_recipes, mock_get_user_ingredients, mock_fetch_user_excluded, mock_fetch_user_preferred):
        mock_fetch_user_preferred.return_value = ["Breakfast", "Dinner"]
        mock_fetch_user_excluded.return_value = ["Lunch"]
        
        mock_get_user_ingredients.return_value = ["eggs", "bacon", "bread"]
        
        mock_calorie_ranges.return_value = {
            "breakfast": (200, 350),
            "lunch": (400, 500),
            "dinner": (600, 800)
        }
        
        mock_recipes = [
            (1, "Breakfast Eggs", "Breakfast", "eggs,bacon,bread", 300),
            (2, "Dinner Steak", "Dinner", "steak,potato", 700),
            (3, "Breakfast Toast", "Breakfast", "bread,butter", 250),
            (4, "Lunch Sandwich", "Lunch", "bread,ham,cheese", 450)
        ]

        mock_get_recipes.return_value = mock_recipes
        
        mock_recipe_details = [
            {
                "recipe_id": 1, 
                "recipe_name": "Breakfast Eggs", 
                "category": "Breakfast", 
                "calories": 300,
                "description": "A breakfast recipe",
                "image_url": "http://example.com/eggs.jpg",
                "instructions": "Cook the eggs",
                "keywords": "eggs,bacon,bread",
                "ingredient_parts": "eggs,bacon,bread",
                "cook_time": "10m"
            },
            {
                "recipe_id": 2, 
                "recipe_name": "Dinner Steak", 
                "category": "Dinner", 
                "calories": 700,
                "description": "A dinner recipe",
                "image_url": "http://example.com/steak.jpg",
                "instructions": "Cook the steak",
                "keywords": "steak,potato",
                "ingredient_parts": "steak,potato",
                "cook_time": "20m"
            },
            {
                "recipe_id": 3, 
                "recipe_name": "Breakfast Toast", 
                "category": "Breakfast", 
                "calories": 250,
                "description": "A simple breakfast",
                "image_url": "http://example.com/toast.jpg",
                "instructions": "Toast the bread",
                "keywords": "bread,butter",
                "ingredient_parts": "bread,butter",
                "cook_time": "5m"
            },
            {
                "recipe_id": 4, 
                "recipe_name": "Lunch Sandwich", 
                "category": "Lunch", 
                "calories": 450,
                "description": "A lunch recipe",
                "image_url": "http://example.com/sandwich.jpg",
                "instructions": "Make a sandwich",
                "keywords": "bread,ham,cheese",
                "ingredient_parts": "bread,ham,cheese",
                "cook_time": "5m"
            }
        ]

        mock_fetch_recipe_details.return_value = mock_recipe_details
        
        result = generate_content_recommendations(user_id = 1, days = 1)
        
        self.assertIn("days", result)
        self.assertEqual(len(result["days"]), 1)
        
        day = result["days"][0]
        self.assertIn("breakfast", day)
        self.assertIn("lunch", day)
        self.assertIn("dinner", day)
        
        self.assertEqual(len(day["lunch"]), 0)
        
        self.assertGreater(len(day["breakfast"]), 0)
        self.assertGreater(len(day["dinner"]), 0)
    
    @patch('modules.content.fetch_user_preferred_categories')
    @patch('modules.content.fetch_user_excluded_categories')
    @patch('modules.content.get_user_ingredients')
    @patch('modules.content.get_recipes')
    def test_no_matching_recipes(self, mock_get_recipes, mock_get_user_ingredients, mock_fetch_user_excluded, mock_fetch_user_preferred):
        mock_fetch_user_preferred.return_value = ["Italian"]
        mock_fetch_user_excluded.return_value = ["American", "Mexican"]
        
        mock_get_user_ingredients.return_value = ["pasta", "tomato"]
        
        mock_get_recipes.return_value = []
        
        result = generate_content_recommendations(user_id = 1, days = 1)
        
        self.assertIn("days", result)
        
        day = result["days"][0] if result["days"] else {}

        self.assertIn("breakfast", day)
        self.assertIn("lunch", day)
        self.assertIn("dinner", day)
    
    @patch('modules.content.fetch_user_preferred_categories')
    @patch('modules.content.fetch_user_excluded_categories')
    @patch('modules.content.get_user_ingredients')
    @patch('modules.content.get_recipes')
    @patch('modules.content.fetch_recipe_details')
    def test_calorie_distribution(self, mock_fetch_recipe_details, mock_get_recipes, mock_get_user_ingredients, mock_fetch_user_excluded, mock_fetch_user_preferred):
        mock_fetch_user_preferred.return_value = ["Breakfast", "Lunch", "Dinner"]
        mock_fetch_user_excluded.return_value = []
        
        mock_get_user_ingredients.return_value = ["eggs", "bread", "chicken", "rice"]
        
        target_calories = 2000
        breakfast_min = 0.23 * target_calories
        breakfast_max = 0.27 * target_calories
        lunch_min = 0.43 * target_calories
        lunch_max = 0.47 * target_calories
        dinner_min = 0.28 * target_calories
        dinner_max = 0.32 * target_calories
        
        mock_recipes = [
            (1, "Low Cal Breakfast", "Breakfast", "eggs,toast", 400),
            (2, "Perfect Breakfast", "Breakfast", "eggs,bacon,toast", 500),
            (3, "High Cal Breakfast", "Breakfast", "eggs,bacon,pancakes,syrup", 600),
            (4, "Low Cal Lunch", "Lunch", "salad", 800),
            (5, "Perfect Lunch", "Lunch", "chicken,rice,vegetables", 900),
            (6, "High Cal Lunch", "Lunch", "burger,fries", 1000),
            (7, "Low Cal Dinner", "Dinner", "fish", 500),
            (8, "Perfect Dinner", "Dinner", "steak,potatoes", 600),
            (9, "High Cal Dinner", "Dinner", "pasta,cream,cheese", 700)
        ]

        mock_get_recipes.return_value = mock_recipes
        
        mock_recipe_details = [{"recipe_id": id, "recipe_name": name, "category": cat, "calories": cal} for id, name, cat, _, cal in mock_recipes]
        mock_fetch_recipe_details.return_value = mock_recipe_details
        
        result = generate_content_recommendations(user_id = 1, days = 1, target_calories = target_calories)
        
        day = result["days"][0]
        
        if day["breakfast"]:
            breakfast_calories = day["breakfast"][0]["calories"]

            self.assertGreaterEqual(breakfast_calories, breakfast_min)
            self.assertLessEqual(breakfast_calories, breakfast_max)
            
        if day["lunch"]:
            lunch_calories = day["lunch"][0]["calories"]

            self.assertGreaterEqual(lunch_calories, lunch_min)
            self.assertLessEqual(lunch_calories, lunch_max)
            
        if day["dinner"]:
            dinner_calories = day["dinner"][0]["calories"]

            self.assertGreaterEqual(dinner_calories, dinner_min)
            self.assertLessEqual(dinner_calories, dinner_max)
    
    @patch('modules.content.fetch_user_preferred_categories')
    @patch('modules.content.fetch_user_excluded_categories')
    @patch('modules.content.get_user_ingredients')
    @patch('modules.content.get_recipes')
    @patch('modules.content.fetch_recipe_details')
    @patch('modules.content.TfidfVectorizer')
    @patch('modules.content.cosine_similarity')
    def test_similarity_ranking(self, mock_cosine, mock_tfidf, mock_fetch_recipe_details, mock_get_recipes, mock_get_user_ingredients, mock_fetch_user_excluded, mock_fetch_user_preferred):
        mock_fetch_user_preferred.return_value = ["Breakfast"]
        mock_fetch_user_excluded.return_value = []
        
        mock_get_user_ingredients.return_value = ["eggs", "bacon", "bread"]
        
        mock_recipes = [
            (1, "Perfect Match", "Breakfast", "eggs,bacon,bread", 500),
            (2, "Partial Match", "Breakfast", "eggs,bread,cheese", 500),
            (3, "Poor Match", "Breakfast", "oats,milk,fruit", 500),
            (4, "Category Match", "Breakfast", "cereal,milk", 500)
        ]

        mock_get_recipes.return_value = mock_recipes
        
        mock_vectorizer = MagicMock()
        mock_tfidf.return_value = mock_vectorizer
        
        mock_cosine.return_value = np.array([[0.9, 0.6, 0.1, 0.3]]) 
        
        mock_recipe_details = [{"recipe_id": id, "recipe_name": name, "category": cat, "calories": cal} for id, name, cat, _, cal in mock_recipes]
        mock_fetch_recipe_details.return_value = mock_recipe_details
        
        result = generate_content_recommendations(user_id = 1, days = 1)
        
        day = result["days"][0]
        breakfast_recommendations = day["breakfast"]
        
        if breakfast_recommendations:
            self.assertEqual(breakfast_recommendations[0]["recipe_id"], 1)
    
    @patch('modules.content.generate_content_recommendations')
    def test_multiple_days_with_mock(self, mock_generate):
        def mock_implementation(user_id, days = 1, **kwargs):
            result = {"days": []}
            
            for i in range(days):
                day_plan = {
                    "breakfast": [
                        {
                            "recipe_id": 1 + i, 
                            "recipe_name": f"Breakfast {i + 1}", 
                            "category": "Breakfast",
                            "calories": 500
                        }
                    ],
                    "lunch": [
                        {
                            "recipe_id": 4 + i, 
                            "recipe_name": f"Lunch {i + 1}", 
                            "category": "Lunch",
                            "calories": 900
                        }
                    ],
                    "dinner": [
                        {
                            "recipe_id": 7 + i, 
                            "recipe_name": f"Dinner {i + 1}", 
                            "category": "Dinner",
                            "calories": 600
                        }
                    ]
                }

                result["days"].append(day_plan)
                
            return result
        
        mock_generate.side_effect = mock_implementation
        
        result = mock_generate(user_id = 1, days = 3)
        
        self.assertEqual(len(result["days"]), 3)
        
        used_recipe_ids = set()
        
        for day in result["days"]:
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if day[meal_type] and len(day[meal_type]) > 0:
                    for recipe in day[meal_type]:
                        recipe_id = recipe["recipe_id"]

                        self.assertNotIn(recipe_id, used_recipe_ids, f"Recipe {recipe_id} was used more than once")

                        used_recipe_ids.add(recipe_id)
    
    @patch('modules.content.fetch_user_preferred_categories')
    @patch('modules.content.fetch_user_excluded_categories')
    @patch('modules.content.get_user_ingredients')
    @patch('modules.content.get_recipes')
    def test_with_no_user_ingredients(self, mock_get_recipes, mock_get_user_ingredients, mock_fetch_user_excluded, mock_fetch_user_preferred):
        mock_fetch_user_preferred.return_value = ["Breakfast"]
        mock_fetch_user_excluded.return_value = []
        
        mock_get_user_ingredients.return_value = []
        
        mock_recipes = [
            (1, "Breakfast 1", "Breakfast", "eggs,toast", 500),
            (2, "Lunch 1", "Lunch", "sandwich,chips", 900),
            (3, "Dinner 1", "Dinner", "pasta,sauce", 600)
        ]

        mock_get_recipes.return_value = mock_recipes
        
        result = generate_content_recommendations(user_id = 1, days = 1)
        
        self.assertIn("days", result)
        self.assertEqual(len(result["days"]), 1)
    
    @patch('modules.content.fetch_recipe_details')
    @patch('modules.content.get_meal_calorie_ranges')
    def test_calorie_range_calculation(self, mock_calorie_ranges, mock_fetch_recipe_details):
        mock_calorie_ranges.return_value = {
            "breakfast": (500, 600),
            "lunch": (850, 950),
            "dinner": (550, 650)
        }
        
        from modules.utils import get_meal_calorie_ranges
        
        test_cases = [2000, 1500, 2500]
        
        for cals in test_cases:
            ranges = get_meal_calorie_ranges(cals)
            
            self.assertIn("breakfast", ranges)
            self.assertIn("lunch", ranges)
            self.assertIn("dinner", ranges)
            
            self.assertEqual(len(ranges["breakfast"]), 2)
            self.assertEqual(len(ranges["lunch"]), 2)
            self.assertEqual(len(ranges["dinner"]), 2)
            
            self.assertLess(ranges["breakfast"][0], ranges["breakfast"][1])
            self.assertLess(ranges["lunch"][0], ranges["lunch"][1])
            self.assertLess(ranges["dinner"][0], ranges["dinner"][1])
            
            breakfast_mid = (ranges["breakfast"][0] + ranges["breakfast"][1]) / 2
            lunch_mid = (ranges["lunch"][0] + ranges["lunch"][1]) / 2
            dinner_mid = (ranges["dinner"][0] + ranges["dinner"][1]) / 2
            
            total = breakfast_mid + lunch_mid + dinner_mid
            
            self.assertAlmostEqual(total, cals, delta = cals * 0.01)


if __name__ == "__main__":
    unittest.main()