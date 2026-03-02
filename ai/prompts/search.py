
def search_prompt(query: str, city: str) -> str:
    return (
        "Преобразуй запрос пользователя к городским местам в JSON с фильтрами.\n"
        f"Город: {city}\n"
        f"Запрос: {query}\n"
        "Формат: {\"keywords\": [str], \"category\": str | null, \"intent\": str}."
    )
