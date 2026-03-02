from db.models import Category, City, Place


def test_models_instantiation() -> None:
    city = City(name="Москва")
    category = Category(slug="eat", name_ru="Поесть")
    place = Place(name="Cafe", city=city, category=category)

    assert place.name == "Cafe"
    assert place.city.name == "Москва"
    assert place.category.slug == "eat"
