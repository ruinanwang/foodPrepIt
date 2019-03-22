from database import edamam_api
from database import spoonacular_api
from database import yummly_api
from database import puppy_api
from dto import dish_summary_dto
# file for keyword searches
def get_spoonacular_data(keywords):
    search_result = spoonacular_api.search(keywords)
    print(search_result)
    dish_list = search_result['results']
    baseUri = search_result['baseUri']
    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = dish['id'], 
        title = dish['title'], 
        image = baseUri + dish['imageUrls'][0],
        recipeLink = '',
        sourceAPI = 'Spoonacular') for i, dish in enumerate(dish_list)]
    return dish_summary_dto_list

def get_edamam_data(keywords):
    dish_list = edamam_api.search(keywords)
    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = -1, 
        title = dish['recipe']['label'], 
        image = dish['recipe']['image'],
        recipeLink = dish['recipe']['url'],
        sourceAPI = 'Edamam') for i, dish in enumerate(dish_list)]
    return dish_summary_dto_list

def get_yummly_data(keywords):
    dish_list = yummly_api.search(keywords)
    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = dish['id'], 
        title = dish['recipeName'], 
        image = dish['imageUrlsBySize']['90'],
        recipeLink = '',
        sourceAPI = 'Yummly') for i, dish in enumerate(dish_list)]
    return dish_summary_dto_list

def get_puppy_data(keywords):
    dish_list = puppy_api.search(keywords)
    dish_summary_dto_list = [ dish_summary_dto.DishSummary(
        id = -1, 
        title = dish['title'],
        image = dish['thumbnail'],
        recipeLink = dish['href'],
        sourceAPI = 'Puppy') for i, dish in enumerate(dish_list)]
    return dish_summary_dto_list