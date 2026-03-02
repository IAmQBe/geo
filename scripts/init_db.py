import asyncio

from db.base import init_models


async def main() -> None:
    await init_models()
    print("Database schema created.")


if __name__ == "__main__":
    asyncio.run(main())
