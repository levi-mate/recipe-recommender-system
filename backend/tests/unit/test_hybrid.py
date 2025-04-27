import unittest
from unittest.mock import patch
import sys
import random
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from modules.hybrid import hybrid_recommendations, combine_recommendations
from config import MAX_RESULTS, DEFAULT_TARGET_CALORIES


class TestHybridRecommendations(unittest.TestCase):
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_basic_hybrid_recommendations(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [{"recipe_id": 101}, {"recipe_id": 102}],
                    "lunch": [{"recipe_id": 201}, {"recipe_id": 202}],
                    "dinner": [{"recipe_id": 301}, {"recipe_id": 302}]
                }
            ]
        }
        
        mock_collab.return_value = [
            {
                "breakfast": [103, 104],
                "lunch": [203, 204],
                "dinner": [303, 304]
            }
        ]
        
        result = hybrid_recommendations(user_id = 1, days = 1)
        
        mock_content.assert_called_once_with(1, days = 1, num_recommendations = MAX_RESULTS, target_calories = DEFAULT_TARGET_CALORIES)
        mock_collab.assert_called_once_with(1, days = 1, num_recommendations = MAX_RESULTS, target_calories = DEFAULT_TARGET_CALORIES)
        
        self.assertIn("days", result)
        self.assertEqual(len(result["days"]), 1)
        
        day = result["days"][0]

        self.assertIn("breakfast", day)
        self.assertIn("lunch", day)
        self.assertIn("dinner", day)
        
        self.assertIsInstance(day["breakfast"], list)
        self.assertIsInstance(day["lunch"], list)
        self.assertIsInstance(day["dinner"], list)
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_multiple_days_hybrid_recommendations(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [{"recipe_id": 101}, {"recipe_id": 102}],
                    "lunch": [{"recipe_id": 201}, {"recipe_id": 202}],
                    "dinner": [{"recipe_id": 301}, {"recipe_id": 302}]
                },
                {
                    "breakfast": [{"recipe_id": 111}, {"recipe_id": 112}],
                    "lunch": [{"recipe_id": 211}, {"recipe_id": 212}],
                    "dinner": [{"recipe_id": 311}, {"recipe_id": 312}]
                },
                {
                    "breakfast": [{"recipe_id": 121}, {"recipe_id": 122}],
                    "lunch": [{"recipe_id": 221}, {"recipe_id": 222}],
                    "dinner": [{"recipe_id": 321}, {"recipe_id": 322}]
                }
            ]
        }
        
        mock_collab.return_value = [
            {
                "breakfast": [103, 104],
                "lunch": [203, 204],
                "dinner": [303, 304]
            },
            {
                "breakfast": [113, 114],
                "lunch": [213, 214],
                "dinner": [313, 314]
            },
            {
                "breakfast": [123, 124],
                "lunch": [223, 224],
                "dinner": [323, 324]
            }
        ]
        
        result = hybrid_recommendations(user_id = 1, days = 3)
        
        self.assertIn("days", result)
        self.assertEqual(len(result["days"]), 3)
        
        for day in result["days"]:
            self.assertIn("breakfast", day)
            self.assertIn("lunch", day)
            self.assertIn("dinner", day)
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_hybrid_recommendations_content_only(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [{"recipe_id": 101}, {"recipe_id": 102}],
                    "lunch": [{"recipe_id": 201}, {"recipe_id": 202}],
                    "dinner": [{"recipe_id": 301}, {"recipe_id": 302}]
                }
            ]
        }
        
        mock_collab.return_value = [
            {
                "breakfast": [],
                "lunch": [],
                "dinner": []
            }
        ]
        
        result = hybrid_recommendations(user_id = 1, days = 1)
        
        self.assertEqual(len(result["days"]), 1)
        day = result["days"][0]
        
        self.assertGreater(len(day["breakfast"]), 0)
        self.assertGreater(len(day["lunch"]), 0)
        self.assertGreater(len(day["dinner"]), 0)
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_hybrid_recommendations_collab_only(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [],
                    "lunch": [],
                    "dinner": []
                }
            ]
        }
        
        mock_collab.return_value = [
            {
                "breakfast": [103, 104],
                "lunch": [203, 204],
                "dinner": [303, 304]
            }
        ]
        
        result = hybrid_recommendations(user_id = 1, days = 1)
        
        self.assertEqual(len(result["days"]), 1)
        day = result["days"][0]
        
        self.assertGreater(len(day["breakfast"]), 0)
        self.assertGreater(len(day["lunch"]), 0)
        self.assertGreater(len(day["dinner"]), 0)
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_hybrid_recommendations_content_failure(self, mock_collab, mock_content):
        mock_content.side_effect = Exception("Content system failure")
        
        mock_collab.return_value = [
            {
                "breakfast": [103, 104],
                "lunch": [203, 204],
                "dinner": [303, 304]
            }
        ]
        
        with self.assertRaises(Exception):
            result = hybrid_recommendations(user_id = 1, days = 1)
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_hybrid_recommendations_collab_failure(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [{"recipe_id": 101}, {"recipe_id": 102}],
                    "lunch": [{"recipe_id": 201}, {"recipe_id": 202}],
                    "dinner": [{"recipe_id": 301}, {"recipe_id": 302}]
                }
            ]
        }
        
        mock_collab.side_effect = Exception("Collaborative system failure")
        
        with self.assertRaises(Exception):
            result = hybrid_recommendations(user_id = 1, days = 1)
    
    def test_combine_recommendations_with_overlap(self):
        content_recipes = [{"recipe_id": 101}, {"recipe_id": 102}, {"recipe_id": 103}]
        collaborative_recipes = [102, 103, 104]
        
        result = combine_recommendations(content_recipes, collaborative_recipes)
        
        self.assertIn(102, result)
        self.assertIn(103, result)
        
        self.assertLessEqual(len(result), MAX_RESULTS)
        
        self.assertTrue(101 in result or 104 in result)
    
    def test_combine_recommendations_over_max(self):
        content_recipes = [{"recipe_id": i} for i in range(100, 150)]
        collaborative_recipes = list(range(150, 200))
        
        result = combine_recommendations(content_recipes, collaborative_recipes)
        
        self.assertLessEqual(len(result), MAX_RESULTS)
    
    def test_combine_recommendations_with_ratio(self):
        content_recipes = [{"recipe_id": i} for i in range(100, 110)]
        collaborative_recipes = list(range(200, 210))
        
        result = combine_recommendations(content_recipes, collaborative_recipes, content_ratio = 0.7)
        
        content_count = sum(1 for r in result if 100 <= r < 200)
        collab_count = sum(1 for r in result if 200 <= r < 300)
        
        self.assertTrue(content_count > collab_count)
        self.assertAlmostEqual(content_count / len(result), 0.7, delta = 0.3)
        
        self.assertLessEqual(len(result), MAX_RESULTS)
    
    def test_combine_recommendations_dict_vs_int(self):
        content_recipes = [
            {"recipe_id": 101, "name": "Recipe 1"}, 
            {"recipe_id": 102, "name": "Recipe 2"}
        ]

        collaborative_recipes = [103, 104]
        
        result = combine_recommendations(content_recipes, collaborative_recipes)
        
        for r in result:
            self.assertIsInstance(r, int)
        
        self.assertTrue(101 in result or 102 in result)
        self.assertTrue(103 in result or 104 in result)
    

class TestHybridRecommendationIntegration(unittest.TestCase):
    
    @patch('modules.hybrid.generate_content_recommendations')
    @patch('modules.hybrid.generate_collaborative_recommendations')
    def test_end_to_end_hybrid_workflow(self, mock_collab, mock_content):
        mock_content.return_value = {
            "days": [
                {
                    "breakfast": [
                        {"recipe_id": 101, "recipe_name": "Eggs Benedict", "calories": 450},
                        {"recipe_id": 102, "recipe_name": "Avocado Toast", "calories": 350}
                    ],

                    "lunch": [
                        {"recipe_id": 201, "recipe_name": "Cobb Salad", "calories": 550},
                        {"recipe_id": 202, "recipe_name": "Quinoa Bowl", "calories": 450}
                    ],

                    "dinner": [
                        {"recipe_id": 301, "recipe_name": "Salmon with Vegetables", "calories": 650},
                        {"recipe_id": 302, "recipe_name": "Steak with Potatoes", "calories": 850}
                    ]
                }
            ]
        }
        
        mock_collab.return_value = [
            {
                "breakfast": [103, 104],
                "lunch": [203, 204],
                "dinner": [303, 304]
            }
        ]
        
        random.seed(42)
        
        result = hybrid_recommendations(user_id = 1, days = 1)
        
        self.assertIn("days", result)
        self.assertEqual(len(result["days"]), 1)
        
        day = result["days"][0]
        
        self.assertGreater(len(day["breakfast"]), 0)
        self.assertGreater(len(day["lunch"]), 0)
        self.assertGreater(len(day["dinner"]), 0)
        
        all_content_ids = [101, 102, 201, 202, 301, 302]
        all_collab_ids = [103, 104, 203, 204, 303, 304]
        
        all_results = day["breakfast"] + day["lunch"] + day["dinner"]
        content_matches = [r for r in all_results if r in all_content_ids]
        collab_matches = [r for r in all_results if r in all_collab_ids]
        
        self.assertGreater(len(content_matches), 0, "No content recommendations were included")
        self.assertGreater(len(collab_matches), 0, "No collaborative recommendations were included")
    
    @patch('random.sample')
    def test_deterministic_behavior_with_fixed_seed(self, mock_random_sample):
        mock_random_sample.side_effect = lambda population, k: population[:k]
        
        content_recipes = [{"recipe_id": i} for i in range(101, 111)]
        collab_recipes = list(range(201, 211))
        
        result1 = combine_recommendations(content_recipes, collab_recipes)
        result2 = combine_recommendations(content_recipes, collab_recipes)
        
        self.assertEqual(result1, result2)


if __name__ == "__main__":
    unittest.main()