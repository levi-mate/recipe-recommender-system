import unittest
import json
import sys
from pathlib import Path
from datetime import datetime

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from webapp import app
import modules.decorators
original_require_auth = modules.decorators.require_auth

def mock_require_auth(f):
    return f


class TestCompleteWorkflows(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        modules.decorators.require_auth = mock_require_auth
        
        self.username = f"workflow_test_{datetime.now().timestamp()}"
        self.password = "TestPassword123!"
        self.email = f"workflow_{datetime.now().timestamp()}@example.com"
        
        register_response = self.app.post('/login/', data={
            "form_type": "register",
            "registerUser": self.username,
            "registerEmail": self.email,
            "registerPwd": self.password,
            "registerRepPwd": self.password
        })
        
        register_data = json.loads(register_response.data)
        self.assertTrue(register_data['success'], "User registration failed")
    
    def tearDown(self):
        self.app_context.pop()

        modules.decorators.require_auth = original_require_auth
    
    def test_user_recommendation_workflow(self):
        login_response = self.app.post('/login/', data = {
            "form_type": "login",
            "loginUser": self.username,
            "loginPwd": self.password
        })
        
        self.assertEqual(login_response.status_code, 200)
        
        nutrition_data = {
            "nutri_state": True,
            "sex": "female",
            "age": 30,
            "height": 165,
            "weight": 60,
            "goal": "maintain",
            "activity_level": "moderate"
        }
        
        nutrition_response = self.app.post('/update_nutrition_info', json = nutrition_data)
        self.assertEqual(nutrition_response.status_code, 200)
        
        ingredients = [
            {"ingredient_name": "Chicken breast", "quantity": 500, "unit": "g", "category": "Meat"},
            {"ingredient_name": "Rice", "quantity": 2, "unit": "cups", "category": "Grains"},
            {"ingredient_name": "Broccoli", "quantity": 1, "unit": "head", "category": "Vegetable"}
        ]
        
        for ingredient in ingredients:
            add_response = self.app.post('/add_ingredient', json = ingredient)
            self.assertEqual(add_response.status_code, 200)
        
        recommendation_response = self.app.get('/generate_recommendations?days=3&targetCalories=2000')
        self.assertEqual(recommendation_response.status_code, 200)
        
        recommendation_data = json.loads(recommendation_response.data)
        self.assertTrue(recommendation_data['success'])
        self.assertIn('days', recommendation_data['data'])
        self.assertTrue(len(recommendation_data['data']['days']) == 3)
        
        first_day = recommendation_data['data']['days'][0]
        
        breakfast_id = first_day['breakfast'][0] if isinstance(first_day['breakfast'][0], int) else first_day['breakfast'][0]['recipe_id']
        lunch_id = first_day['lunch'][0] if isinstance(first_day['lunch'][0], int) else first_day['lunch'][0]['recipe_id']
        dinner_id = first_day['dinner'][0] if isinstance(first_day['dinner'][0], int) else first_day['dinner'][0]['recipe_id']
        
        meal_plan = {
            "mealPlans": [
                {
                    "breakfast_id": breakfast_id,
                    "lunch_id": lunch_id,
                    "dinner_id": dinner_id
                }
            ]
        }
        
        save_response = self.app.post('/save_meal_plans', json = meal_plan)
        self.assertEqual(save_response.status_code, 200)
        
        today = datetime.now().strftime('%Y-%m-%d')
        get_meal_response = self.app.get(f'/get_meal_plan?meal_date={today}')
        self.assertEqual(get_meal_response.status_code, 200)
        
        meal_data = json.loads(get_meal_response.data)
        self.assertEqual(meal_data['breakfast']['recipe_id'], breakfast_id)
        
        mark_response = self.app.post('/mark_meal_finished', json = {
            "meal_date": today,
            "meal_type": "breakfast"
        })

        self.assertEqual(mark_response.status_code, 200)
        
        get_updated_meal = self.app.get(f'/get_meal_plan?meal_date={today}')
        updated_meal_data = json.loads(get_updated_meal.data)
        self.assertTrue(updated_meal_data['breakfast_finished'])
        
        new_recommendations = self.app.get('/generate_recommendations?days=1&targetCalories=2000')
        self.assertEqual(new_recommendations.status_code, 200)