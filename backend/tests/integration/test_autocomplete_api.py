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


class TestAutocompleteAPI(unittest.TestCase):
    
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
            'autocomplete.autocomplete_recipes',
            'autocomplete.autocomplete_ingredients',
            'autocomplete.autocomplete_categories'
        ]
        
        for endpoint in endpoints_to_test:
            route = url_map.get(endpoint)

            if not route:
                print(f"Warning: No URL found for endpoint {endpoint}")

                continue
                
            print(f"Testing route: {endpoint} -> {route}")
            
            try:
                test_route = f"{route}?query=test"
                response = self.app.get(test_route)
                
                print(f"  Response: {response.status_code}")
                
                self.assertNotEqual(response.status_code, 404, f"Route {route} not found (404)")

            except Exception as e:
                self.fail(f"Failed testing route {route}: {str(e)}")
    
    def test_autocomplete_recipes(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT recipe_name FROM recipes LIMIT 5")
            recipes = cursor.fetchall()
            
            if not recipes:
                self.skipTest("No recipes found in database")
            
            test_recipe = recipes[0][0]

            if test_recipe and len(test_recipe) > 3:
                query = test_recipe[:3].lower()
            else:
                query = "a"
        
        response = self.app.get(f"/autocomplete_recipes?query={query}")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        
        if query != "a":
            self.assertTrue(len(data) > 0, "Expected at least one recipe suggestion")
        
        if data:
            first_item = data[0]

            self.assertIn('recipe_id', first_item)
            self.assertIn('recipe_name', first_item)
    
    def test_autocomplete_ingredients(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ingredient_name FROM ingredients LIMIT 5")
            ingredients = cursor.fetchall()
            
            if not ingredients:
                self.skipTest("No ingredients found in database")
            
            test_ingredient = ingredients[0][0]

            if test_ingredient and len(test_ingredient) > 3:
                query = test_ingredient[:3].lower()
            else:
                query = "a"
        
        response = self.app.get(f"/autocomplete_ingredients?query={query}")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        
        if query != "a":
            self.assertTrue(len(data) > 0, "Expected at least one ingredient suggestion")
        
        if data:
            first_item = data[0]

            self.assertIn('id', first_item)
            self.assertIn('name', first_item)
    
    def test_autocomplete_categories(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM recipes LIMIT 5")
            categories = cursor.fetchall()
            
            if not categories:
                self.skipTest("No categories found in database")
            
            test_category = categories[0][0]

            if test_category and len(test_category) > 3:
                query = test_category[:3].lower()
            else:
                query = "a"
        
        response = self.app.get(f"/autocomplete_categories?query={query}")
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIsInstance(data, list)
        
        if query != "a":
            self.assertTrue(len(data) > 0, "Expected at least one category suggestion")
        
        if data:
            first_item = data[0]

            self.assertIsInstance(first_item, str)
    
    def test_empty_query(self):
        response_recipes = self.app.get("/autocomplete_recipes?query=")
        self.assertEqual(response_recipes.status_code, 200)
        data_recipes = json.loads(response_recipes.data)
        self.assertEqual(data_recipes, [], "Expected empty list for empty query")
        
        response_ingredients = self.app.get("/autocomplete_ingredients?query=")
        self.assertEqual(response_ingredients.status_code, 200)
        data_ingredients = json.loads(response_ingredients.data)
        self.assertEqual(data_ingredients, [], "Expected empty list for empty query")
        
        response_categories = self.app.get("/autocomplete_categories?query=")
        self.assertEqual(response_categories.status_code, 200)
        data_categories = json.loads(response_categories.data)
        self.assertEqual(data_categories, [], "Expected empty list for empty query")
    
    def test_missing_query(self):
        response_recipes = self.app.get("/autocomplete_recipes")
        self.assertEqual(response_recipes.status_code, 200)
        data_recipes = json.loads(response_recipes.data)
        self.assertEqual(data_recipes, [], "Expected empty list for missing query")
        
        response_ingredients = self.app.get("/autocomplete_ingredients")
        self.assertEqual(response_ingredients.status_code, 200)
        data_ingredients = json.loads(response_ingredients.data)
        self.assertEqual(data_ingredients, [], "Expected empty list for missing query")
        
        response_categories = self.app.get("/autocomplete_categories")
        self.assertEqual(response_categories.status_code, 200)
        data_categories = json.loads(response_categories.data)
        self.assertEqual(data_categories, [], "Expected empty list for missing query")
    
    def test_limit_results(self):
        common_query = "a"
        
        response_recipes = self.app.get(f"/autocomplete_recipes?query={common_query}")
        data_recipes = json.loads(response_recipes.data)
        self.assertTrue(len(data_recipes) <= 20, "Results should be limited to 20 items")
        
        response_ingredients = self.app.get(f"/autocomplete_ingredients?query={common_query}")
        data_ingredients = json.loads(response_ingredients.data)
        self.assertTrue(len(data_ingredients) <= 20, "Results should be limited to 20 items")
        
        response_categories = self.app.get(f"/autocomplete_categories?query={common_query}")
        data_categories = json.loads(response_categories.data)
        self.assertTrue(len(data_categories) <= 20, "Results should be limited to 20 items")


if __name__ == "__main__":
    unittest.main()