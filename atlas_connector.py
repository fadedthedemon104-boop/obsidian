"""Database sync engine for pushing ledger state to MongoDB Atlas."""
import os
from typing import Any, Dict, Optional

from pymongo import MongoClient


class AtlasLedgerConnector:
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_ATLAS_URI")
        if not self.uri:
            raise ValueError("MONGODB_ATLAS_URI environment variable not configured.")
        self.client = MongoClient(self.uri)
        self.db = self.client["production_banking"]

    def upsert_account(self, record: Dict[str, Any]) -> None:
        self.db["accounts"].update_one(
            {"account_id": record["account_id"]},
            {"$set": record},
            upsert=True,
        )

    def log_transaction(self, tx_dict: Dict[str, Any]) -> None:
        self.db["transactions"].insert_one(tx_dict)

    def close(self) -> None:
        self.client.close()
