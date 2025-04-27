import unittest
import json
import sys
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


class TestNutritionAPI(unittest.TestCase):
    
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
            
            if self.test_user_id:
                cursor.execute("SELECT username FROM users WHERE user_id = ?", (self.test_user_id,))
                user_result = cursor.fetchone()
                self.username = user_result[0] if user_result else "testuser"
            else:
                self.username = "testuser"
                
            cursor.execute("DELETE FROM user_nutrition WHERE user_id = ?", (self.test_user_id,))
            conn.commit()
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.username
            session['authenticated'] = True
    
    def tearDown(self):
        self.app_context.pop()
        
        modules.decorators.require_auth = original_require_auth
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_nutrition WHERE user_id = ?", (self.test_user_id,))
            conn.commit()
    
    def test_endpoints_exist(self):
        url_map = {}

        for rule in app.url_map.iter_rules():
            url_map[rule.endpoint] = str(rule)

            print(f"DEBUG: {rule.endpoint} -> {rule}")
        
        endpoints_to_test = [
            'nutrition.get_nutrition_info',
            'nutrition.update_nutrition_info',
            'nutrition.calculate_target_calories'
        ]
        
        for endpoint in endpoints_to_test:
            route = url_map.get(endpoint)

            if not route:
                print(f"Warning: No URL found for endpoint {endpoint}")

                continue
                
            print(f"Testing route: {endpoint} -> {route}")
            
            try:
                if 'get' in endpoint.lower():
                    response = self.app.get(route)
                else:
                    response = self.app.post(route, json={})
                
                print(f"  Response: {response.status_code}")
                
                self.assertNotEqual(response.status_code, 404, f"Route {route} not found (404)")

            except Exception as e:
                self.fail(f"Failed testing route {route}: {str(e)}")
    
    def test_get_nutrition_info_new_user(self):
        response = self.app.get('/get_nutrition_info')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        self.assertFalse(data['data']['nutri_state'])
        self.assertEqual(data['data']['target_calories'], 2000)
        self.assertEqual(data['data']['goal'], 'maintain')
        self.assertEqual(data['data']['activity_level'], 'low')
    
    def test_update_nutrition_info(self):
        nutrition_data = {
            "nutri_state": True,
            "sex": "male",
            "age": 30,
            "height": 180,
            "weight": 75,
            "bmi": 23.1,
            "goal": "lose",
            "activity_level": "moderate",
            "target_calories": 1800
        }
        
        update_response = self.app.post('/update_nutrition_info', json = nutrition_data)
        
        self.assertEqual(update_response.status_code, 200)
        update_data = json.loads(update_response.data)
        self.assertTrue(update_data['success'])
        
        get_response = self.app.get('/get_nutrition_info')
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)
        
        self.assertTrue(get_data['data']['nutri_state'])
        self.assertEqual(get_data['data']['sex'], 'male')
        self.assertEqual(get_data['data']['age'], 30)
        self.assertEqual(get_data['data']['height'], 180)
        self.assertEqual(get_data['data']['weight'], 75)
        self.assertEqual(get_data['data']['bmi'], 23.1)
        self.assertEqual(get_data['data']['goal'], 'lose')
        self.assertEqual(get_data['data']['activity_level'], 'moderate')
        self.assertEqual(get_data['data']['target_calories'], 1800)
        
        partial_update = {
            "nutri_state": True,
            "sex": "male",
            "age": 30,
            "height": 180,
            "weight": 75,
            "bmi": 23.1,
            "goal": "gain",
            "activity_level": "moderate",
            "target_calories": 2500
        }
        
        partial_update_response = self.app.post('/update_nutrition_info', json = partial_update)
        self.assertEqual(partial_update_response.status_code, 200)
        
        get_response_2 = self.app.get('/get_nutrition_info')
        get_data_2 = json.loads(get_response_2.data)
        
        self.assertEqual(get_data_2['data']['goal'], 'gain')
        self.assertEqual(get_data_2['data']['target_calories'], 2500)
        self.assertEqual(get_data_2['data']['sex'], 'male')
    
    def test_calculate_target_calories_male(self):
        data = {
            "sex": "male",
            "age": 30,
            "height": 180,
            "weight": 75,
            "goal": "maintain",
            "activity_level": "moderate"
        }
        
        response = self.app.post('/calculate_target_calories', json = data)
        
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        
        self.assertIn('success', result_data)
        self.assertTrue(result_data['success'])
        self.assertIn('data', result_data)
        self.assertIn('target_calories', result_data['data'])
        self.assertIn('bmi', result_data['data'])
        
        self.assertAlmostEqual(result_data['data']['bmi'], 23.1, delta = 0.1)
        
        target_calories = result_data['data']['target_calories']
        self.assertTrue(2600 <= target_calories <= 2750, f"Target calories {target_calories} outside expected range")
    
    def test_calculate_target_calories_female(self):
        data = {
            "sex": "female",
            "age": 25,
            "height": 165,
            "weight": 60,
            "goal": "lose",
            "activity_level": "low"
        }
        
        response = self.app.post('/calculate_target_calories', json = data)
        
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        
        self.assertAlmostEqual(result_data['data']['bmi'], 22.0, delta = 0.1)
        
        target_calories = result_data['data']['target_calories']
        self.assertTrue(1500 <= target_calories <= 1600, f"Target calories {target_calories} outside expected range")
    
    def test_calculate_target_calories_weight_gain(self):
        data = {
            "sex": "male",
            "age": 22,
            "height": 175,
            "weight": 65,
            "goal": "gain",
            "activity_level": "heavy"
        }
        
        response = self.app.post('/calculate_target_calories', json = data)
        
        self.assertEqual(response.status_code, 200)
        result_data = json.loads(response.data)
        
        target_calories = result_data['data']['target_calories']
        self.assertTrue(target_calories > 2800, f"Target calories {target_calories} not high enough for weight gain")
    
    def test_calculate_target_calories_invalid_input(self):
        response1 = self.app.post('/calculate_target_calories', json = {"sex": "male", "age": 30})
        
        self.assertEqual(response1.status_code, 400)
        data1 = json.loads(response1.data)
        self.assertIn('error', data1)
        
        response2 = self.app.post('/calculate_target_calories', json = {"sex": "male", "age": "invalid", "height": 180, "weight": 75})
        
        self.assertEqual(response2.status_code, 400)
        data2 = json.loads(response2.data)
        self.assertIn('error', data2)
    
    def test_integration_calculate_and_update(self):
        calc_data = {
            "sex": "female",
            "age": 28,
            "height": 170,
            "weight": 65,
            "goal": "maintain",
            "activity_level": "moderate"
        }
        
        calc_response = self.app.post('/calculate_target_calories', json = calc_data)
        calc_result = json.loads(calc_response.data)
        target_calories = calc_result['data']['target_calories']
        bmi = calc_result['data']['bmi']
        
        update_data = {
            "nutri_state": True,
            "sex": "female",
            "age": 28,
            "height": 170,
            "weight": 65,
            "bmi": bmi,
            "goal": "maintain",
            "activity_level": "moderate",
            "target_calories": target_calories
        }
        
        update_response = self.app.post('/update_nutrition_info', json = update_data)
        self.assertEqual(update_response.status_code, 200)
        
        get_response = self.app.get('/get_nutrition_info')
        get_data = json.loads(get_response.data)
        
        self.assertEqual(get_data['data']['target_calories'], target_calories)
        self.assertEqual(get_data['data']['bmi'], bmi)
        self.assertEqual(get_data['data']['sex'], 'female')
        self.assertEqual(get_data['data']['goal'], 'maintain')
        self.assertEqual(get_data['data']['activity_level'], 'moderate')


if __name__ == "__main__":
    unittest.main()