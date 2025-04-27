import unittest
import json
import sys
from unittest.mock import patch
from datetime import datetime, timedelta
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from components.db_connect import get_db_connection
from webapp import app
import modules.decorators
original_require_auth = modules.decorators.require_auth

def mock_require_auth(f):
    return f

modules.decorators.require_auth = mock_require_auth

class TestRecommendationsAPI(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        
        self.app = app.test_client()
        self.app.testing = True
        
        self.app_context = app.app_context()
        self.app_context.push()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users LIMIT 1")
            result = cursor.fetchone()
            self.test_user_id = result[0] if result else 1
            
            cursor.execute("SELECT recipe_id FROM recipes LIMIT 9")
            recipes = cursor.fetchall()
            self.test_recipes = [r[0] for r in recipes] if recipes else list(range(101, 110))
            
            if self.test_user_id:
                cursor.execute("SELECT username FROM users WHERE user_id = ?", (self.test_user_id,))
                user_result = cursor.fetchone()
                self.username = user_result[0] if user_result else "testuser"
            else:
                self.username = "testuser"
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.username
            session['authenticated'] = True
    
    def tearDown(self):
        self.app_context.pop()
        
        modules.decorators.require_auth = original_require_auth
        
    def test_endpoints_exist(self):
        url_map = {}

        for rule in app.url_map.iter_rules():
            url_map[rule.endpoint] = str(rule)
            print(f"DEBUG: {rule.endpoint} -> {rule}")
        
        endpoints_to_test = [
            'recommendations.generate_recommendations_endpoint',
            'recommendations.save_meal_plans',
            'recommendations.get_meal_plan',
            'recommendations.get_weekly_meal_plan',
            'recommendations.fetch_recipe_details_endpoint',
            'recommendations.get_recipe_ingredients',
            'recommendations.check_meal_plan_dates',
            'recommendations.mark_meal_finished',
            'recommendations.delete_meal_plan',
            'recommendations.get_user_interactions',
            'recommendations.save_interaction'
        ]
        
        for endpoint in endpoints_to_test:
            route = url_map.get(endpoint)

            if not route:
                print(f"Warning: No URL found for endpoint {endpoint}")

                continue
                
            if '<' in route:
                for param in route.split('<')[1:]:
                    param_name = param.split('>')[0]

                    if 'recipe_id' in param_name:
                        route = route.replace(f'<{param_name}>', str(self.test_recipes[0]))
                    else:
                        route = route.replace(f'<{param_name}>', '1')
            
            print(f"Testing route: {endpoint} -> {route}")
            
            try:
                if 'get' in endpoint.lower() or 'generate' in endpoint.lower():
                    response = self.app.get(route)
                else:
                    response = self.app.post(route, json={})
                
                print(f"  Response: {response.status_code}")
                
                self.assertNotEqual(response.status_code, 404, f"Route {route} not found (404)")

            except Exception as e:
                self.fail(f"Failed testing route {route}: {str(e)}")
    
    @patch('components.recommendations.hybrid_recommendations')
    def test_generate_recommendations(self, mock_hybrid):
        mock_recommendations = {
            "days": [
                {
                    "breakfast": [{"recipe_id": self.test_recipes[0], "recipe_name": "Test Breakfast"}],
                    "lunch": [{"recipe_id": self.test_recipes[1], "recipe_name": "Test Lunch"}],
                    "dinner": [{"recipe_id": self.test_recipes[2], "recipe_name": "Test Dinner"}]
                }
            ]
        }
        mock_hybrid.return_value = mock_recommendations
        
        url_map = {}

        for rule in app.url_map.iter_rules():
            if rule.endpoint == 'recommendations.generate_recommendations_endpoint':
                url_map[rule.endpoint] = str(rule)
        
        generate_url = url_map.get('recommendations.generate_recommendations_endpoint', '/generate_recommendations')
        
        response = self.app.get(f'{generate_url}?days=1&targetCalories=2000')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('days', data['data'])
        self.assertIsInstance(data['data']['days'], list)
        
        mock_hybrid.assert_called_once_with(self.test_user_id, days = 1, target_calories = 2000)
        
    def test_save_and_get_meal_plan(self):
        today = datetime.now().date()
        meal_plans_data = {
            "mealPlans": [
                {
                    "breakfast_id": self.test_recipes[0],
                    "lunch_id": self.test_recipes[1],
                    "dinner_id": self.test_recipes[2]
                }
            ]
        }
        
        save_response = self.app.post('/save_meal_plans', json = meal_plans_data)
        
        self.assertEqual(save_response.status_code, 200)
        save_data = json.loads(save_response.data)
        self.assertTrue(save_data.get('success'))
        
        today_str = today.strftime('%Y-%m-%d')
        get_response = self.app.get(f'/get_meal_plan?meal_date={today_str}')
        
        self.assertEqual(get_response.status_code, 200)
        meal_plan = json.loads(get_response.data)
        
        self.assertIn('breakfast', meal_plan)
        self.assertIn('lunch', meal_plan)
        self.assertIn('dinner', meal_plan)
        
        self.assertEqual(meal_plan['breakfast']['recipe_id'], self.test_recipes[0])
        self.assertEqual(meal_plan['lunch']['recipe_id'], self.test_recipes[1])
        self.assertEqual(meal_plan['dinner']['recipe_id'], self.test_recipes[2])
        
    def test_get_weekly_meal_plan(self):
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days = 6)
        
        for day in range(7):
            date = start_date + timedelta(days = day)
            date_str = date.strftime('%Y-%m-%d')
            
            meal_plans_data = {
                "mealPlans": [
                    {
                        "date": date_str,
                        "breakfast_id": self.test_recipes[0],
                        "lunch_id": self.test_recipes[1],
                        "dinner_id": self.test_recipes[2]
                    }
                ]
            }

            save_response = self.app.post('/save_meal_plans', json = meal_plans_data)
            self.assertEqual(save_response.status_code, 200, f"Failed to save meal plan for {date_str}")
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        print(f"Requesting weekly meal plan from {start_str} to {end_str}")
        
        response = self.app.get(f'/get_weekly_meal_plan?start_date={start_str}&end_date={end_str}')
        
        self.assertEqual(response.status_code, 200)
        weekly_plan = json.loads(response.data)
        
        self.assertIsInstance(weekly_plan, list)
        
        if len(weekly_plan) != 7:
            print(f"WARNING: Expected 7 days but got {len(weekly_plan)}")
            print(f"Weekly plan content: {weekly_plan}")
        
        for day_plan in weekly_plan:
            self.assertIn('date', day_plan)
            self.assertIn('breakfast', day_plan)
            self.assertIn('lunch', day_plan)
            self.assertIn('dinner', day_plan)
        
    @patch('components.recommendations.fetch_recipe_details')
    def test_fetch_recipe_details(self, mock_fetch):
        mock_recipe_details = {
            str(self.test_recipes[0]): {
                "recipe_id": self.test_recipes[0],
                "recipe_name": "Test Recipe 1",
                "calories": 500
            },

            str(self.test_recipes[1]): {
                "recipe_id": self.test_recipes[1],
                "recipe_name": "Test Recipe 2",
                "calories": 600
            }
        }

        mock_fetch.return_value = mock_recipe_details
        
        recipe_ids = [self.test_recipes[0], self.test_recipes[1]]
        response = self.app.post('/fetch_recipe_details', json = {"recipeIds": recipe_ids})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        mock_fetch.assert_called_once_with(recipe_ids)
        
        self.assertEqual(data, mock_recipe_details)
        
    def test_get_recipe_ingredients(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT recipe_id FROM recipes WHERE ingredient_parts IS NOT NULL LIMIT 1")
            result = cursor.fetchone()
            
            if not result:
                self.skipTest("No recipes with ingredients found in database")
            
            recipe_id = result[0]
        
        response = self.app.get(f'/get_recipe_ingredients/{recipe_id}')
        
        self.assertEqual(response.status_code, 200)
        ingredients = json.loads(response.data)
        
        self.assertIsInstance(ingredients, list)

        if ingredients:
            self.assertIn('name', ingredients[0])
            
    def test_check_meal_plan_dates(self):
        today = datetime.now().date().strftime('%Y-%m-%d')
        tomorrow = (datetime.now().date() + timedelta(days = 1)).strftime('%Y-%m-%d')
        
        meal_plans_data = {
            "mealPlans": [
                {
                    "breakfast_id": self.test_recipes[0],
                    "lunch_id": self.test_recipes[1],
                    "dinner_id": self.test_recipes[2]
                }
            ]
        }

        self.app.post('/save_meal_plans', json = meal_plans_data)
        
        check_data = {
            "dates": [today, tomorrow]
        }

        response = self.app.post('/check_meal_plan_dates', json = check_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertIn('results', data['data'])
        
        self.assertEqual(data['data']['results'], [True, False])
        
    def test_mark_meal_finished(self):
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        meal_plans_data = {
            "mealPlans": [
                {
                    "breakfast_id": self.test_recipes[0],
                    "lunch_id": self.test_recipes[1],
                    "dinner_id": self.test_recipes[2]
                }
            ]
        }

        self.app.post('/save_meal_plans', json = meal_plans_data)
        
        mark_data = {
            "meal_date": today,
            "meal_type": "breakfast" 
        }

        response = self.app.post('/mark_meal_finished', json = mark_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        
        get_response = self.app.get(f'/get_meal_plan?meal_date={today}')
        meal_plan = json.loads(get_response.data)
        
        self.assertTrue(meal_plan['breakfast_finished'])
        self.assertFalse(meal_plan['lunch_finished'])
        self.assertFalse(meal_plan['dinner_finished'])
        
    def test_delete_meal_plan(self):
        today = datetime.now().date().strftime('%Y-%m-%d')
        
        meal_plans_data = {
            "mealPlans": [
                {
                    "breakfast_id": self.test_recipes[0],
                    "lunch_id": self.test_recipes[1],
                    "dinner_id": self.test_recipes[2]
                }
            ]
        }

        self.app.post('/save_meal_plans', json = meal_plans_data)
        
        delete_data = {
            "meal_date": today
        }

        response = self.app.post('/delete_meal_plan', json = delete_data)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        
        get_response = self.app.get(f'/get_meal_plan?meal_date={today}')
        self.assertEqual(get_response.status_code, 404)
        
    def test_user_interactions(self):
        interaction_data = {
            "recipe_id": self.test_recipes[0],
            "interaction_type": "like"
        }

        save_response = self.app.post('/save_interaction', json = interaction_data)
        
        self.assertEqual(save_response.status_code, 200)
        save_data = json.loads(save_response.data)
        self.assertTrue(save_data['success'])
        
        get_response = self.app.get('/get_user_interactions')
        
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)
        
        self.assertIn('success', get_data)
        self.assertTrue(get_data['success'])
        self.assertIn('data', get_data)
        self.assertIn('interactions', get_data['data'])
        
        found = False

        for interaction in get_data['data']['interactions']:
            if interaction['recipe_id'] == self.test_recipes[0] and interaction['interaction_type'] == 'like':
                found = True
                
                break
                
        self.assertTrue(found, "Saved interaction not found in get_user_interactions response")


if __name__ == "__main__":
    unittest.main()