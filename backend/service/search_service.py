from database import edamam_api
from database import spoonacular_api
from database import yummly_api
from database import puppy_api
from dto import dish_summary_dto
from foodPrepIt.models import CacheRecipeDetail
from django.db import IntegrityError
from django.db import connection
from service import sql_service

# file for keyword searches
def get_spoonacular_data(keywords,dietRestriction,excludedIngredients,prepTime,calorieLimit):
    search_result = spoonacular_api.search(keywords,dietRestriction,excludedIngredients)
    dish_list = search_result['results']
    dish_summary_dto_list = []

    if dietRestriction == '' and excludedIngredients == '' and prepTime == '' and calorieLimit == '':
        baseUri = search_result['baseUri']
        dish_summary_dto_list = [ dish_summary_dto.DishSummary(
            id = dish['id'], 
            title = dish['title'], 
            image = baseUri + dish['imageUrls'][0],
            recipeLink = '',
            sourceAPI = 'Spoonacular') for dish in dish_list]
    
    else:
        filtered_list = dish_list
        store_image = ''

        # store into cache
        for dish in dish_list:
            print('id: ', str(dish['id']))
            print('title: ',dish['title'])

            recipePrepTime = -1
            recipeCalories = -1

            check = sql_service.check_key_exist(dish['title'],'Spoonacular')
            if check!=0:
                print('existing key')

                response = sql_service.get_db_data("readyInMinutes,calories,image",dish['title'],'Spoonacular')
                recipePrepTime = response[0]
                recipeCalories = response[1]
                store_image = response[2]
            
            else:
                print('no key')
        
                recipe = spoonacular_api.getRecipe(str(dish['id']))
                priceBreakdown = spoonacular_api.getPriceBreakdown(str(dish['id']))
                nutrition = spoonacular_api.getNutrition(str(dish['id']))

                store_diet = ''
                if recipe['vegetarian']:
                    store_diet += 'vegetarian,'
                if recipe['vegan']:
                    store_diet += 'vegan,'
                
                ingredients_raw = recipe['extendedIngredients']
                ingredients_list = []
                for item in ingredients_raw:
                    ingredients_list.append(item['originalString'])

                recipePrepTime = recipe['readyInMinutes']
                recipeCalories = int(nutrition['calories'])

                try:
                    store_image = recipe['image']
                except:
                    store_image = ''

                try:
                    cachEntry = CacheRecipeDetail(
                        title = dish['title'], 
                        image = store_image, 
                        sourceAPI = 'Spoonacular', 
                        recipeLink = recipe['sourceUrl'],
                        readyInMinutes = recipe['readyInMinutes'],
                        instruction = recipe['instructions'] if recipe['instructions'] != None else '',
                        ingredients = ingredients_list,
                        diet = store_diet,
                        budget = priceBreakdown['totalCostPerServing'],
                        # budget = -1,
                        calories = str(nutrition['calories'])
                        )
                    cachEntry.save()
                except IntegrityError:
                    pass

            # filter
            if prepTime != '' and int(prepTime) < recipePrepTime:
                dish_list.remove(dish)
            elif calorieLimit != '' and int(calorieLimit) < recipeCalories:
                dish_list.remove(dish)

            if dish in filtered_list:
                dish_summary_dto_list.append(dish_summary_dto.DishSummary(
                    id = dish['id'], 
                    title = dish['title'], 
                    image = store_image,
                    recipeLink = '',
                    sourceAPI = 'Spoonacular'))

    return dish_summary_dto_list

def get_edamam_data(keywords,dietRestriction,excludedIngredients,prepTime,calorieLimit):
    dish_list = edamam_api.search(keywords,excludedIngredients,prepTime,calorieLimit)
    filtered_list = []
    dish_summary_dto_list = []
    
    if dietRestriction == '' and excludedIngredients == '' and prepTime == '' and calorieLimit == '':
        filtered_list = dish_list
    else:
        # store into cache
        for dish in dish_list:
            
            store_diet = ''  
            healthLabels = dish['recipe']['healthLabels']
            print(healthLabels)
            for item in healthLabels:
                if item == 'Vegetarian':
                    store_diet += 'vegetarian,'
                    if dietRestriction == 'vegetarian':
                        filtered_list.append(dish)
                if item == 'Vegan':
                    store_diet += 'vegan,'
                    if dietRestriction == 'vegan':
                        filtered_list.append(dish)
            try:
                cachEntry = CacheRecipeDetail(
                    title = dish['recipe']['label'], 
                    image = dish['recipe']['image'], 
                    sourceAPI = 'Edamam', 
                    recipeLink = dish['recipe']['url'],
                    readyInMinutes = -1,
                    instruction = '',
                    ingredients = dish['recipe']['ingredientLines'],
                    diet = store_diet,
                    budget = -1,
                    calories = dish['recipe']['calories']
                    )
                cachEntry.save()
            except IntegrityError:
                pass

        if dietRestriction == '':
            filtered_list = dish_list

    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = -1, 
        title = dish['recipe']['label'], 
        image = dish['recipe']['image'],
        recipeLink = dish['recipe']['url'],
        sourceAPI = 'Edamam') for i, dish in enumerate(filtered_list)]
    return dish_summary_dto_list

def get_yummly_data(keywords,ingredients,dietRestriction,excludedIngredients,prepTime,calorieLimit):
    dish_list = yummly_api.search(keywords,ingredients,dietRestriction,excludedIngredients,prepTime)
    filtered_list = []
    if dietRestriction == '' and excludedIngredients == '' and prepTime == '' and calorieLimit == '':
        filtered_list = dish_list
    else:
        # store into cache
        store_diet = ''
        store_calories = -1

        if dietRestriction != '':
            store_diet = dietRestriction
        
        for dish in dish_list:
            recipe = yummly_api.getRecipe(dish['id'])
            for nutrient in recipe['nutritionEstimates']:
                if nutrient['attribute'] == 'ENERC_KCAL':
                    store_calories = nutrient['value']
                    # print(store_calories)

            if calorieLimit != '' and int(calorieLimit) > store_calories:
                filtered_list.append(dish)

            try:
                cachEntry = CacheRecipeDetail(
                    title = dish['recipeName'], 
                    image = dish['imageUrlsBySize']['90'], 
                    sourceAPI = 'Yummly', 
                    recipeLink = recipe['source']['sourceRecipeUrl'],
                    readyInMinutes = int(recipe['totalTimeInSeconds']/60),
                    instruction = '',
                    ingredients = recipe['ingredientLines'],
                    diet = store_diet,
                    budget = -1,
                    calories = int(store_calories)
                    )
                cachEntry.save()
            except IntegrityError:
                pass

        if calorieLimit == '':
            filtered_list = dish_list

    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = dish['id'], 
        title = dish['recipeName'], 
        image = dish['imageUrlsBySize']['90'],
        recipeLink = '',
        sourceAPI = 'Yummly') for i, dish in enumerate(filtered_list)]
    return dish_summary_dto_list

def get_puppy_data(keywords):
    dish_list = puppy_api.search(keywords)
    ingredientsList = []
    
    # store to cache
    # for dish in dish_list:
    #     ingredientsList.append(dish['ingredients'])
    #     try:
    #         cachEntry = CacheRecipeDetail(
    #             title = dish['title'], 
    #             image = dish['thumbnail'],
    #             sourceAPI = 'Puppy', 
    #             recipeLink = dish['href'],
    #             readyInMinutes = -1,
    #             instruction = '',
    #             ingredients = ingredientsList,
    #             diet = '',
    #             budget = -1,
    #             calories = -1
    #             )
    #         cachEntry.save()
    #     except IntegrityError:
    #         pass

    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = -1, 
        title = dish['title'],
        image = dish['thumbnail'],
        recipeLink = dish['href'],
        sourceAPI = 'Puppy') for i, dish in enumerate(dish_list)]
    return dish_summary_dto_list