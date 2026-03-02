
def weekly_analysis_prompt(payload: dict) -> str:
    return (
        "Сформируй краткий weekly trend report по данным:\n"
        f"{payload}\n"
        "Верни 3 секции: trending, new_and_noteworthy, admin_insights."
    )
