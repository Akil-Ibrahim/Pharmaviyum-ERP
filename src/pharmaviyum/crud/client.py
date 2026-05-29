# crud/client.py - CRUD operations for Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import hashlib
from typing import Optional, List
from src.pharmaviyum.models.client import Client
from src.pharmaviyum.schemas.client_schema import ClientCreate, ClientUpdate, ClientSegment

class ClientCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _generate_discount_card(phone: str) -> str:
        hash_digest = hashlib.md5(phone.encode()).hexdigest()[:8].upper()
        return f"PHARM{hash_digest}"

    async def create(self, data: ClientCreate) -> Client:
        db_client = Client(**data.model_dump())
        db_client.discount_card = self._generate_discount_card(data.phone)
        self.db.add(db_client)
        await self.db.commit()
        await self.db.refresh(db_client)
        return db_client

    async def get(self, client_id: int) -> Optional[Client]:
        result = await self.db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone: str) -> Optional[Client]:
        result = await self.db.execute(
            select(Client).where(Client.phone == phone)
        )
        return result.scalar_one_or_none()

    async def search_by_phone_partial(self, phone_suffix: str, limit: int = 5) -> List[Client]:
        result = await self.db.execute(
            select(Client)
            .where(Client.phone.endswith(phone_suffix))
            .where(Client.is_active == True)
            .limit(limit)
        )
        return result.scalars().all()

    async def update(self, client_id: int, data: ClientUpdate) -> Optional[Client]:
        client = await self.get(client_id)
        if not client:
            return None
        if data.phone and data.phone != client.phone:
            existing = await self.get_by_phone(data.phone)
            if existing:
                raise ValueError("Phone number already used")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(client, key, value)
        client.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(client)
        return client

    async def soft_delete(self, client_id: int) -> bool:
        client = await self.get(client_id)
        if not client:
            return False
        client.is_active = False
        await self.db.commit()
        return True

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Client]:
        result = await self.db.execute(
            select(Client)
            .where(Client.is_active == True)
            .order_by(Client.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def update_purchase_stats(self, client_id: int, amount: float) -> Optional[Client]:
        client = await self.get(client_id)
        if client:
            client.total_purchases += 1
            client.total_spent += amount
            client.last_visit = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(client)
        return client

    def get_segment(self, client: Client) -> ClientSegment:
        if client.is_privileged:
            return ClientSegment.PRIVILEGED
        if client.total_purchases > 50:
            return ClientSegment.VIP
        if client.total_purchases > 10:
            return ClientSegment.REGULAR
        if client.total_purchases == 0:
            return ClientSegment.NEW
        return ClientSegment.DORMANT
