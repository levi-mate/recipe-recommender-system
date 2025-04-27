import unittest
import json
import sys
from datetime import datetime
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(backend_dir))

from components.db_connect import get_db_connection
from webapp import app
import modules.decorators
original_require_auth = modules.decorators.require_auth

def mock_require_auth(f):
    return f


class TestAuthAPI(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        
        self.app = app.test_client()
        self.app.testing = True
        
        self.app_context = app.app_context()
        self.app_context.push()
        
        self.test_username = f"testuser_{datetime.now().timestamp()}"
        self.test_email = f"test_{datetime.now().timestamp()}@example.com"
        self.test_password = "TestPassword123!"
        
        self.original_require_auth = modules.decorators.require_auth
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            password_hash = generate_password_hash(self.test_password)
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (self.test_username, self.test_email, password_hash))
            conn.commit()
            
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (self.test_username,))
            result = cursor.fetchone()
            self.test_user_id = result[0]
    
    def tearDown(self):
        self.app_context.pop()
        
        modules.decorators.require_auth = self.original_require_auth
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = ?", (self.test_user_id,))
            conn.commit()
    
    def test_endpoints_exist(self):
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        url_map = {}

        for rule in app.url_map.iter_rules():
            url_map[rule.endpoint] = str(rule)

            print(f"DEBUG: {rule.endpoint} -> {rule}")
        
        endpoints_to_test = [
            'auth.login',
            'auth.logout',
            'auth.check_login',
            'auth.get_user_profile',
            'auth.update_username',
            'auth.update_email',
            'auth.update_password',
            'auth.save_preferred_categories',
            'auth.get_preferred_categories',
            'auth.add_preferred_category',
            'auth.delete_preferred_category',
            'auth.get_excluded_categories',
            'auth.add_excluded_category',
            'auth.delete_excluded_category'
        ]
        
        modules.decorators.require_auth = mock_require_auth
        
        for endpoint in endpoints_to_test:
            route = url_map.get(endpoint)

            if not route:
                print(f"Warning: No URL found for endpoint {endpoint}")

                continue
                
            print(f"Testing route: {endpoint} -> {route}")
            
            try:
                if 'get' in endpoint.lower() or 'check' in endpoint.lower():
                    response = self.app.get(route)
                else:
                    params = {'data': {}} if 'login' in endpoint.lower() else {'json': {}}
                    response = self.app.post(route, **params)
                
                print(f"  Response: {response.status_code}")
                
                self.assertNotEqual(response.status_code, 404, f"Route {route} not found (404)")

            except Exception as e:
                self.fail(f"Failed testing route {route}: {str(e)}")
    
    def test_register_user(self):
        username = f"newuser_{datetime.now().timestamp()}"
        email = f"new_{datetime.now().timestamp()}@example.com"
        password = "NewPassword123!"
        
        response = self.app.post('/login/', data = {
            "form_type": "register",
            "registerUser": username,
            "registerEmail": email,
            "registerPwd": password,
            "registerRepPwd": password
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Registration successful', data['message'])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            self.assertIsNotNone(result, "User was not created in the database")
            
            cursor.execute("DELETE FROM users WHERE user_id = ?", (result[0],))
            conn.commit()
    
    def test_register_duplicate_user(self):
        response = self.app.post('/login/', data = {
            "form_type": "register",
            "registerUser": self.test_username,
            "registerEmail": f"another_{datetime.now().timestamp()}@example.com",
            "registerPwd": "Password123!",
            "registerRepPwd": "Password123!"
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('already exists', data['error'].lower())
    
    def test_login_success(self):
        response = self.app.post('/login/', data = {
            "form_type": "login",
            "loginUser": self.test_username,
            "loginPwd": self.test_password
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Login successful', data['message'])
        
        with self.app.session_transaction() as session:
            self.assertIn('user_id', session)
            self.assertEqual(session['user_id'], self.test_user_id)
            self.assertIn('username', session)
            self.assertEqual(session['username'], self.test_username)
    
    def test_login_failure(self):
        response = self.app.post('/login/', data = {
            "form_type": "login",
            "loginUser": self.test_username,
            "loginPwd": "WrongPassword123!"
        })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
        self.assertIn('invalid username or password', data['error'].lower())
        
        with self.app.session_transaction() as session:
            self.assertNotIn('user_id', session)
    
    def test_logout(self):
        login_response = self.app.post('/login/', data = {
            "form_type": "login",
            "loginUser": self.test_username,
            "loginPwd": self.test_password
        })
        
        self.assertEqual(login_response.status_code, 200)
        
        logout_response = self.app.post('/logout')
        
        self.assertEqual(logout_response.status_code, 200)
        data = json.loads(logout_response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Logged out successfully', data['message'])
        
        with self.app.session_transaction() as session:
            self.assertNotIn('user_id', session)
            self.assertNotIn('username', session)
    
    def test_check_login(self):
        not_logged_in_response = self.app.get('/check_login')
        self.assertEqual(not_logged_in_response.status_code, 200)
        not_logged_in_data = json.loads(not_logged_in_response.data)
        
        self.assertFalse(not_logged_in_data['data']['loggedIn'])
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        logged_in_response = self.app.get('/check_login')
        self.assertEqual(logged_in_response.status_code, 200)
        logged_in_data = json.loads(logged_in_response.data)
        
        self.assertTrue(logged_in_data['data']['loggedIn'])
        self.assertEqual(logged_in_data['data']['userId'], self.test_user_id)
        self.assertEqual(logged_in_data['data']['username'], self.test_username)
    
    def test_get_user_profile(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        response = self.app.get('/get_user_profile')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        self.assertEqual(data['data']['username'], self.test_username)
        self.assertEqual(data['data']['email'], self.test_email)
    
    def test_update_username(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        new_username = f"updated_user_{datetime.now().timestamp()}"
        response = self.app.post('/update_username', json = {"username": new_username})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Username updated successfully', data['message'])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE user_id = ?", (self.test_user_id,))
            result = cursor.fetchone()
            
            self.assertEqual(result[0], new_username)
        
        self.test_username = new_username
    
    def test_update_email(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        new_email = f"updated_{datetime.now().timestamp()}@example.com"
        response = self.app.post('/update_email', json = {"email": new_email})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Email updated successfully', data['message'])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE user_id = ?", (self.test_user_id,))
            result = cursor.fetchone()
            
            self.assertEqual(result[0], new_email)
        
        self.test_email = new_email
    
    def test_update_password(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        new_password = f"NewPassword{datetime.now().timestamp()}"
        response = self.app.post('/update_password', json = {"current_password": self.test_password, "new_password": new_password})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
        self.assertIn('Password updated successfully', data['message'])
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (self.test_user_id,))
            result = cursor.fetchone()
            
            self.assertTrue(check_password_hash(result[0], new_password))
            self.assertFalse(check_password_hash(result[0], self.test_password))
        
        self.test_password = new_password
    
    def test_preferred_categories_workflow(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        test_categories = [f"category_{datetime.now().timestamp()}_{i}" for i in range(10)]
        
        save_response = self.app.post('/save_preferred_categories', json = {"preferred_categories": test_categories})
        
        self.assertEqual(save_response.status_code, 200)
        save_data = json.loads(save_response.data)
        self.assertTrue(save_data['success'])
    
    def test_excluded_categories_workflow(self):
        modules.decorators.require_auth = mock_require_auth
        
        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        test_categories = [f"excluded_cat_{datetime.now().timestamp()}_{i}" for i in range(3)]
        
        for category in test_categories:
            add_response = self.app.post('/add_excluded_category', json = {"category": category})
            
            self.assertEqual(add_response.status_code, 200)
            add_data = json.loads(add_response.data)
            self.assertTrue(add_data['success'])
        
        get_response = self.app.get('/get_excluded_categories')
        
        self.assertEqual(get_response.status_code, 200)
        get_data = json.loads(get_response.data)
        
        self.assertIn('success', get_data)
        self.assertTrue(get_data['success'])
        self.assertIn('data', get_data)
        
        excluded_categories = set(get_data['data'])
        expected_categories = set(test_categories)
        self.assertEqual(excluded_categories, expected_categories)
    
    def test_invalid_form_data(self):
        login_response = self.app.post('/login/', data = {"form_type": "login",})
        
        self.assertEqual(login_response.status_code, 400)
        login_data = json.loads(login_response.data)
        self.assertIn('error', login_data)
        
        reg_response = self.app.post('/login/', data = {
            "form_type": "register",
            "registerUser": f"mismatch_user_{datetime.now().timestamp()}",
            "registerEmail": f"mismatch_{datetime.now().timestamp()}@example.com",
            "registerPwd": "Password123!",
            "registerRepPwd": "DifferentPassword123!"
        })
        
        self.assertEqual(reg_response.status_code, 400)
        reg_data = json.loads(reg_response.data)
        self.assertIn('error', reg_data)
        self.assertIn('passwords do not match', reg_data['error'].lower())
        
        modules.decorators.require_auth = mock_require_auth

        with self.app.session_transaction() as session:
            session['user_id'] = self.test_user_id
            session['username'] = self.test_username
            session['authenticated'] = True
        
        username_response = self.app.post('/update_username', json = {"username": ""})
        
        self.assertEqual(username_response.status_code, 400)
        username_data = json.loads(username_response.data)
        self.assertIn('error', username_data)
        
        email_response = self.app.post('/update_email', json = {"email": ""})
        
        self.assertEqual(email_response.status_code, 400)
        email_data = json.loads(email_response.data)
        self.assertIn('error', email_data)
        
        password_response = self.app.post('/update_password', json = {"current_password": "WrongPassword123", "new_password": "NewPassword123!"})
        
        self.assertEqual(password_response.status_code, 400)
        password_data = json.loads(password_response.data)
        self.assertIn('error', password_data)
        self.assertIn('incorrect', password_data['error'].lower())


if __name__ == "__main__":
    unittest.main()