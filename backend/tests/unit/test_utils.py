from modules.utils import (
    get_meal_calorie_ranges, 
    parse_ingredient_parts,
    get_user_ingredients,
    get_recipes,
    fetch_recipe_details,
    fetch_recipe_categories,
    fetch_user_preferred_categories,
    fetch_user_excluded_categories,
    find_similar_users,
    fetch_interactions,
    get_user_liked_recipes,
    fetch_recipe_calories
)


class TestMealCalorieRanges:
    def test_get_meal_calorie_ranges_default(self):
        ranges = get_meal_calorie_ranges(2000)
        
        assert 450 <= ranges['breakfast'][0] <= 550
        assert 450 <= ranges['breakfast'][1] <= 550
        
        assert 850 <= ranges['lunch'][0] <= 950
        assert 850 <= ranges['lunch'][1] <= 950
        
        assert 550 <= ranges['dinner'][0] <= 650
        assert 550 <= ranges['dinner'][1] <= 650
    
    def test_get_meal_calorie_ranges_low_calories(self):
        ranges = get_meal_calorie_ranges(1200)
        
        assert sum([r[0] for r in ranges.values()]) < 1200
        assert sum([r[1] for r in ranges.values()]) > 1200
        
    def test_get_meal_calorie_ranges_high_calories(self):
        ranges = get_meal_calorie_ranges(3000)
        
        assert 'breakfast' in ranges
        assert 'lunch' in ranges
        assert 'dinner' in ranges
        
        for meal_type in ranges:
            assert len(ranges[meal_type]) == 2
            assert ranges[meal_type][0] < ranges[meal_type][1]


class TestIngredientParsing:
    def test_parse_ingredient_parts_simple(self):
        result = parse_ingredient_parts("eggs,bacon,toast")

        assert result == ['eggs', 'bacon', 'toast']
    
    def test_parse_ingredient_parts_with_spaces(self):
        result = parse_ingredient_parts("eggs, bacon, toast")

        assert result == ['eggs', 'bacon', 'toast']
    
    def test_parse_ingredient_parts_complex(self):
        test_str = "2 cups flour, 1 tsp salt, 3 tbsp sugar"
        result = parse_ingredient_parts(test_str)

        assert "2 cups flour" in result 
        assert "1 tsp salt" in result
        assert "3 tbsp sugar" in result
        
    def test_parse_ingredient_parts_empty(self):
        result = parse_ingredient_parts("")

        assert result == []
        
    def test_parse_ingredient_parts_with_numbers_and_units(self):
        result = parse_ingredient_parts("1 cup milk, 2 large eggs, 1/2 tsp vanilla")

        assert "1 cup milk" in result 
        assert "2 large eggs" in result
        assert "1/2 tsp vanilla" in result
        
    def test_parse_ingredient_parts_with_special_chars(self):
        result = parse_ingredient_parts("olive oil, bell pepper (red), sea-salt")

        assert "olive oil" in result 
        assert "bell pepper (red)" in result
        assert "sea-salt" in result


class TestDatabaseQueries:
    def test_get_user_ingredients(self, db_connection):
        ingredients = get_user_ingredients(1)
        
        assert isinstance(ingredients, list)
        assert 'eggs' in ingredients
        assert 'bacon' in ingredients
        
    def test_get_recipes(self, db_connection):
        recipes = get_recipes()
        
        assert len(recipes) > 0
        
        first_recipe = recipes[0]

        assert isinstance(first_recipe[0], int)
        assert isinstance(first_recipe[1], str)
        assert isinstance(first_recipe[4], (int, float))
        
    def test_fetch_recipe_details(self, db_connection):
        recipe_ids = [1, 2]
        recipes = fetch_recipe_details(recipe_ids)
        
        assert len(recipes) == 2
        
        recipe_ids_found = [r['recipe_id'] for r in recipes]

        assert 1 in recipe_ids_found
        assert 2 in recipe_ids_found
        
        first_recipe = recipes[0]

        assert 'recipe_id' in first_recipe
        assert 'recipe_name' in first_recipe
        assert 'calories' in first_recipe
        assert 'ingredient_parts' in first_recipe
        
    def test_fetch_recipe_categories(self, db_connection):
        categories = fetch_recipe_categories()
        
        assert isinstance(categories, dict)
        
        assert 1 in categories
        assert 2 in categories
        assert 3 in categories
        
        assert categories[1] == 'Breakfast'
        assert categories[2] == 'Breakfast'
        assert categories[3] == 'Breakfast'
        
    def test_fetch_user_preferred_categories(self, db_connection):
        categories = fetch_user_preferred_categories(2)
        
        assert isinstance(categories, list)
        assert len(categories) > 0
        assert 'Breakfast' in categories
        assert 'Dinner' in categories
        
        categories = fetch_user_preferred_categories(1)

        assert isinstance(categories, list)
        
    def test_fetch_user_excluded_categories(self, db_connection):
        excluded = fetch_user_excluded_categories(1)

        assert isinstance(excluded, list)
        
    def test_find_similar_users(self, db_connection):
        similar_users = find_similar_users(1)
        
        assert isinstance(similar_users, list)
        
    def test_fetch_interactions(self, db_connection):
        interactions = fetch_interactions()
        
        assert isinstance(interactions, list)
        assert len(interactions) > 0
        
        first_interaction = interactions[0]

        assert isinstance(first_interaction[0], int)
        assert isinstance(first_interaction[1], int)
        
    def test_get_user_liked_recipes(self, db_connection):
        liked_recipes = get_user_liked_recipes(1)
        
        assert isinstance(liked_recipes, list)
        
    def test_fetch_recipe_calories(self, db_connection):
        calories = fetch_recipe_calories()
        
        assert isinstance(calories, dict)
        assert len(calories) > 0
        
        assert 1 in calories
        assert 2 in calories
        assert 3 in calories
        
        assert calories[1] == 500
        assert calories[2] == 350
        assert calories[3] == 550