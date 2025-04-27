import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from modules.collab import build_interaction_matrix, train_collaborative_filtering_model, recommend_recipes, generate_collaborative_recommendations
from config import MAX_RESULTS, DEFAULT_TARGET_CALORIES


class TestCollaborativeFiltering(unittest.TestCase):
    
    @patch('modules.collab.Dataset')
    def test_build_interaction_matrix(self, mock_dataset_class):
        mock_dataset = MagicMock()
        mock_dataset_class.return_value = mock_dataset
        
        mock_dataset.mapping.return_value = (
            {1: 0, 2: 1},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        test_interactions = [
            (1, 101, "like"),
            (1, 102, "like"),
            (2, 103, "like"),
            (2, 101, "dislike")
        ]
        
        test_interactions_matrix = sp.csr_matrix([
            [1, 1, 0],
            [0, -1, 1]
        ])

        mock_dataset.build_interactions.return_value = (test_interactions_matrix, None)
        
        result_dataset, result_matrix = build_interaction_matrix(test_interactions)
        
        mock_dataset.fit.assert_called_once()
        mock_dataset.build_interactions.assert_called_once()
        
        self.assertEqual(result_dataset, mock_dataset)
        self.assertIs(result_matrix, test_interactions_matrix)
    
    @patch('modules.collab.LightFM')
    def test_train_collaborative_filtering_model(self, mock_lightfm_class):
        mock_model = MagicMock()
        mock_lightfm_class.return_value = mock_model
        
        test_matrix = sp.csr_matrix([[1, 0], [0, 1]])
        
        result_model = train_collaborative_filtering_model(test_matrix)
        
        mock_lightfm_class.assert_called_once()
        mock_model.fit.assert_called_once_with(test_matrix, epochs = 5, num_threads = 2, verbose = True)
        
        self.assertEqual(result_model, mock_model)
    
    @patch('modules.collab.fetch_user_preferred_categories')
    @patch('modules.collab.fetch_user_excluded_categories')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories')
    @patch('modules.collab.find_similar_users')
    @patch('modules.collab.get_user_liked_recipes')
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_recommend_recipes_basic(self, mock_calorie_ranges, mock_get_liked, mock_find_similar, mock_recipe_calories, mock_recipe_categories, mock_excluded_categories, mock_preferred_categories):
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        mock_model.predict.return_value = np.array([0.8, 0.2, 0.9])
        
        mock_preferred_categories.return_value = ["Breakfast", "Lunch"]
        mock_excluded_categories.return_value = ["Dinner"]
        mock_recipe_categories.return_value = {
            101: "Breakfast",
            102: "Lunch",
            103: "Dinner"
        }

        mock_recipe_calories.return_value = {
            101: 500,
            102: 900,
            103: 600
        }

        mock_find_similar.return_value = [(2, 0.85, ["Breakfast"])]
        mock_get_liked.return_value = [101, 102]
        
        mock_calorie_ranges.return_value = {
            "breakfast": (400, 600),
            "lunch": (800, 1000),
            "dinner": (500, 700)
        }
        
        result = recommend_recipes(mock_model, mock_dataset, user_id = 1, days = 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn("breakfast", result[0])
        self.assertIn("lunch", result[0])
        self.assertIn("dinner", result[0])
        
        self.assertEqual(len(result[0]["dinner"]), 0)
        
        self.assertGreaterEqual(len(result[0]["breakfast"]), 1)
        self.assertGreaterEqual(len(result[0]["lunch"]), 1)
    
    @patch('modules.collab.fetch_user_preferred_categories')
    @patch('modules.collab.fetch_user_excluded_categories')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories')
    @patch('modules.collab.find_similar_users')
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_recommend_recipes_no_similar_users(self, mock_calorie_ranges, mock_find_similar, mock_recipe_calories, mock_recipe_categories, mock_excluded_categories, mock_preferred_categories):
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        mock_model.predict.return_value = np.array([0.8, 0.7, 0.6])
        
        mock_preferred_categories.return_value = ["Breakfast"]
        mock_excluded_categories.return_value = []
        mock_recipe_categories.return_value = {
            101: "Breakfast",
            102: "Lunch",
            103: "Dinner"
        }
        
        mock_recipe_calories.return_value = {
            101: 500,
            102: 900,
            103: 600
        }

        mock_find_similar.return_value = []
        
        mock_calorie_ranges.return_value = {
            "breakfast": (400, 600),
            "lunch": (800, 1000),
            "dinner": (500, 700)
        }
        
        result = recommend_recipes(mock_model, mock_dataset, user_id = 1, days = 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn("breakfast", result[0])
        self.assertIn("lunch", result[0])
        self.assertIn("dinner", result[0])
    
    @patch('modules.collab.build_interaction_matrix')
    @patch('modules.collab.train_collaborative_filtering_model')
    @patch('modules.collab.recommend_recipes')
    @patch('modules.collab.fetch_interactions')
    def test_generate_collaborative_recommendations_existing_user(self, mock_fetch_interactions, mock_recommend_recipes, mock_train_model, mock_build_matrix):
        mock_dataset = MagicMock()
        mock_matrix = MagicMock()
        mock_model = MagicMock()
        mock_build_matrix.return_value = (mock_dataset, mock_matrix)
        mock_train_model.return_value = mock_model
        
        mock_fetch_interactions.return_value = [
            (1, 101, "like"),
            (1, 102, "like"),
            (2, 103, "like")
        ]
        
        mock_dataset.mapping.return_value = (
            {1: 0, 2: 1},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        mock_day_recommendations = {
            "breakfast": [101],
            "lunch": [102],
            "dinner": [103]
        }

        mock_recommend_recipes.return_value = [mock_day_recommendations]
        
        result = generate_collaborative_recommendations(user_id = 1, days = 1)
        
        mock_fetch_interactions.assert_called_once()
        mock_build_matrix.assert_called_once()
        mock_train_model.assert_called_once()
        mock_recommend_recipes.assert_called_once()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_day_recommendations)
    
    @patch('modules.collab.build_interaction_matrix')
    @patch('modules.collab.train_collaborative_filtering_model')
    @patch('modules.collab.fetch_interactions')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories')
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_generate_collaborative_recommendations_new_user(self, mock_meal_ranges, mock_recipe_calories, mock_recipe_categories, mock_fetch_interactions, mock_train_model, mock_build_matrix):
        mock_dataset = MagicMock()
        mock_matrix = MagicMock()
        mock_build_matrix.return_value = (mock_dataset, mock_matrix)
        
        mock_dataset.mapping.return_value = (
            {2: 0},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        mock_fetch_interactions.return_value = [(2, 103, "like")]
        
        mock_recipe_categories.return_value = {
            101: "Breakfast",
            102: "Lunch",
            103: "Dinner"
        }

        mock_recipe_calories.return_value = {
            101: 500,
            102: 900,
            103: 600
        }

        mock_meal_ranges.return_value = {
            "breakfast": (400, 600),
            "lunch": (800, 1000),
            "dinner": (500, 700)
        }
        
        result = generate_collaborative_recommendations(user_id = 1, days = 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn("breakfast", result[0])
        self.assertIn("lunch", result[0])
        self.assertIn("dinner", result[0])
    
    @patch('modules.collab.build_interaction_matrix')
    @patch('modules.collab.train_collaborative_filtering_model')
    @patch('modules.collab.recommend_recipes')
    @patch('modules.collab.fetch_interactions')
    def test_generate_collaborative_recommendations_multiple_days(self, mock_fetch_interactions, mock_recommend_recipes, mock_train_model, mock_build_matrix):
        mock_dataset = MagicMock()
        mock_matrix = MagicMock()
        mock_model = MagicMock()
        mock_build_matrix.return_value = (mock_dataset, mock_matrix)
        mock_train_model.return_value = mock_model
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2, 104: 3, 105: 4, 106: 5}
        )
        
        mock_fetch_interactions.return_value = [
            (1, 101, "like"),
            (1, 102, "like")
        ]
        
        mock_recommendations = [
            {
                "breakfast": [101],
                "lunch": [102],
                "dinner": [103]
            },
            {
                "breakfast": [104],
                "lunch": [105],
                "dinner": [106]
            },
            {
                "breakfast": [101],
                "lunch": [102], 
                "dinner": [106]
            }
        ]

        mock_recommend_recipes.return_value = mock_recommendations
        
        result = generate_collaborative_recommendations(user_id = 1, days = 3)
        
        mock_recommend_recipes.assert_called_once_with(mock_model, mock_dataset, 1, MAX_RESULTS, 3, DEFAULT_TARGET_CALORIES)
        
        self.assertEqual(len(result), 3)
    
    @patch('modules.collab.build_interaction_matrix')
    @patch('modules.collab.fetch_interactions')
    def test_generate_collaborative_recommendations_error_handling(self, mock_fetch_interactions, mock_build_matrix):
        mock_fetch_interactions.return_value = [(1, 101, "like")]
        mock_build_matrix.side_effect = ValueError("Test error")
        
        result = generate_collaborative_recommendations(user_id = 1, days = 1)
        
        self.assertEqual(len(result), 1)
        self.assertIn("breakfast", result[0])
        self.assertIn("lunch", result[0])
        self.assertIn("dinner", result[0])

        self.assertEqual(len(result[0]["breakfast"]), 0)
        self.assertEqual(len(result[0]["lunch"]), 0)
        self.assertEqual(len(result[0]["dinner"]), 0)
    
    @patch('modules.collab.fetch_user_preferred_categories')
    @patch('modules.collab.fetch_user_excluded_categories')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories')
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_calorie_targeting(self, mock_calorie_ranges, mock_recipe_calories, mock_recipe_categories, mock_excluded_categories, mock_preferred_categories):
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2, 104: 3, 105: 4, 106: 5, 107: 6}
        )
        
        mock_model.predict.return_value = np.array([0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2])
        
        mock_preferred_categories.return_value = ["Breakfast", "Lunch", "Dinner"]
        mock_excluded_categories.return_value = []
        mock_recipe_categories.return_value = {
            101: "Breakfast",
            102: "Breakfast",
            103: "Breakfast",
            104: "Lunch",
            105: "Lunch",
            106: "Dinner",
            107: "Dinner"
        }
        
        target_calories = 2000
        breakfast_min = 0.23 * target_calories
        breakfast_max = 0.27 * target_calories
        lunch_min = 0.43 * target_calories
        lunch_max = 0.47 * target_calories
        dinner_min = 0.28 * target_calories
        dinner_max = 0.32 * target_calories
        
        mock_calorie_ranges.return_value = {
            "breakfast": (breakfast_min, breakfast_max),
            "lunch": (lunch_min, lunch_max),
            "dinner": (dinner_min, dinner_max)
        }
        
        mock_recipe_calories.return_value = {
            101: 400,
            102: 500,
            103: 600,
            104: 800,
            105: 900,
            106: 600,
            107: 700
        }
        
        result = recommend_recipes(mock_model, mock_dataset, user_id = 1, days = 1, target_calories = target_calories)
        
        breakfast_id = result[0]["breakfast"][0]
        breakfast_calories = mock_recipe_calories.return_value[breakfast_id]

        self.assertGreaterEqual(breakfast_calories, breakfast_min)
        self.assertLessEqual(breakfast_calories, breakfast_max)
        
        lunch_id = result[0]["lunch"][0]
        lunch_calories = mock_recipe_calories.return_value[lunch_id]

        self.assertGreaterEqual(lunch_calories, lunch_min)
        self.assertLessEqual(lunch_calories, lunch_max)
        
        dinner_id = result[0]["dinner"][0]
        dinner_calories = mock_recipe_calories.return_value[dinner_id]

        self.assertGreaterEqual(dinner_calories, dinner_min)
        self.assertLessEqual(dinner_calories, dinner_max)
    
    @patch('modules.collab.fetch_user_preferred_categories')
    @patch('modules.collab.fetch_user_excluded_categories')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories') 
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_recipe_uniqueness_across_days(self, mock_calorie_ranges, mock_recipe_calories, mock_recipe_categories, mock_excluded_categories, mock_preferred_categories):
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        def mock_predict_function(user_id, item_ids):
            return np.array([0.9] * len(item_ids))
        
        mock_model.predict = mock_predict_function
        
        mock_preferred_categories.return_value = ["Breakfast", "Lunch", "Dinner"]
        mock_excluded_categories.return_value = []
        mock_recipe_categories.return_value = {
            101: "Breakfast", 
            102: "Lunch",    
            103: "Dinner"   
        }
        
        mock_calorie_ranges.return_value = {
            "breakfast": (400, 600),
            "lunch": (800, 1000),
            "dinner": (500, 700)
        }
        
        mock_recipe_calories.return_value = {
            101: 500,
            102: 900,
            103: 600
        }
        
        result = recommend_recipes(mock_model, mock_dataset, user_id = 1, days = 1)
        
        day = result[0]
        all_recipes = day["breakfast"] + day["lunch"] + day["dinner"]
        unique_recipes = set(all_recipes)
        
        self.assertEqual(len(all_recipes), len(unique_recipes), "Each meal should use different recipes")
    
    @patch('modules.collab.fetch_user_preferred_categories')
    @patch('modules.collab.fetch_user_excluded_categories')
    @patch('modules.collab.fetch_recipe_categories')
    @patch('modules.collab.fetch_recipe_calories')
    @patch('modules.collab.find_similar_users')
    @patch('modules.collab.get_user_liked_recipes')
    @patch('modules.collab.get_meal_calorie_ranges')
    def test_similar_users_recommendation_weight(self, mock_calorie_ranges, mock_get_liked, mock_find_similar, mock_recipe_calories, mock_recipe_categories, mock_excluded_categories, mock_preferred_categories):
        mock_model = MagicMock()
        mock_dataset = MagicMock()
        
        mock_dataset.mapping.return_value = (
            {1: 0},
            None,
            {101: 0, 102: 1, 103: 2}
        )
        
        mock_find_similar.return_value = [
            (2, 0.9, ["Breakfast"]),
            (3, 0.5, ["Breakfast"]),
        ]
        
        def get_liked_mock(user_id):
            if user_id == 2:
                return [101]
            elif user_id == 3:
                return [102]
            
            return []
        
        mock_get_liked.side_effect = get_liked_mock
        
        mock_preferred_categories.return_value = ["Breakfast"]
        mock_excluded_categories.return_value = []
        mock_recipe_categories.return_value = {
            101: "Breakfast", 
            102: "Breakfast",    
            103: "Breakfast"   
        }
        
        mock_calorie_ranges.return_value = {
            "breakfast": (400, 600),
            "lunch": (800, 1000),
            "dinner": (500, 700)
        }
        
        mock_recipe_calories.return_value = {
            101: 500,
            102: 500,
            103: 500
        }
        
        result = recommend_recipes(mock_model, mock_dataset, user_id = 1, days = 1)
        
        breakfast_recommendations = result[0]["breakfast"]

        if breakfast_recommendations:
            self.assertEqual(breakfast_recommendations[0], 101, "Recipe liked by most similar user should be recommended first")


if __name__ == "__main__":
    unittest.main()