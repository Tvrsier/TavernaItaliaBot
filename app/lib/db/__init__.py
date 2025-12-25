import asyncio
import atexit
import signal
from typing import Optional, List, Sequence, Dict

from tortoise import Tortoise, BaseDBAsyncClient, connections
from app.logger import logger


class DatabaseManager:
    _initialized = False

    def __init__(self, db_url: str, modules: dict, generate_schemas: bool = False):
        self.db_url = db_url
        self.modules = modules
        self.generate_schemas = generate_schemas

        atexit.register(self._sync_close)
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda signum, frame: self._sync_close())

    def _sync_close(self) -> None:
        if not DatabaseManager._initialized:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.close())
            else:
                loop.run_until_complete(self.close())
        except RuntimeError:
            asyncio.run(self.close())

    async def connect(self) -> None:
        if not self._initialized:
            await Tortoise.init(
                db_url=self.db_url,
                modules=self.modules if self.modules else None
            )
            logger.info("Database connection initialized with URL: %s", self.db_url)
            if self.generate_schemas:
                await Tortoise.generate_schemas()
            DatabaseManager._initialized = True

    @staticmethod
    async def close() -> None:
        await Tortoise.close_connections()
        DatabaseManager._initialized = False

    @property
    def connection(self) -> BaseDBAsyncClient:
        return connections.get("default")

    async def execute_raw(self, query: str, values: Optional[List]) -> tuple[int, Sequence[Dict]]:
        return await self.connection.execute_query(query, values)

    async def execute_raw_fetch(self, query: str, values: Optional[List]) -> List[Dict]:
        return await self.connection.execute_query_dict(query, values)

    async def __aenter__(self) -> "DatabaseManager":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


if __name__ == "__main__":
    db_path = "sqlite://data/taverna_bot.db"
    modules = {"models": ["schemas"]}
    db_manager = DatabaseManager(db_path, modules, generate_schemas=True)
    asyncio.run(db_manager.connect())
    logger.info("Database initialized and schemas generated.")
    asyncio.run(db_manager.close())
