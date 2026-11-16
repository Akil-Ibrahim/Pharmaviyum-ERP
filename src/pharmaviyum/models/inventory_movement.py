"""Append-only journal of pharmacy lot stock and reservation movements."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.pharmaviyum.db.base import Base


class InventoryMovement(Base):
    """Immutable audit record paired atomically with an Inventory balance change."""

    __tablename__ = "inventory_movements"
    __table_args__ = (
        UniqueConstraint(
            "pharmacy_id",
            "idempotency_key",
            name="uq_inventory_movements_pharmacy_idempotency",
        ),
        ForeignKeyConstraint(
            ["inventory_id", "pharmacy_id", "product_id"],
            ["inventory.id", "inventory.pharmacy_id", "inventory.product_id"],
            ondelete="RESTRICT",
            name="fk_inventory_movements_lot_identity",
        ),
        CheckConstraint(
            "movement_type IN ("
            "'goods_receipt', 'cash_sale', 'payment_reservation', "
            "'payment_settlement', 'payment_failure', 'sale_cancellation', "
            "'stock_adjustment', 'write_off', 'expiry_disposal', "
            "'accepted_return', 'transfer_in', 'transfer_out', 'opening_balance'"
            ")",
            name="ck_inventory_movements_type",
        ),
        CheckConstraint(
            "actor_type IN ('user', 'system')",
            name="ck_inventory_movements_actor_type",
        ),
        CheckConstraint(
            "(actor_type = 'user' AND actor_user_id IS NOT NULL) OR "
            "(actor_type = 'system' AND actor_user_id IS NULL)",
            name="ck_inventory_movements_actor_identity",
        ),
        CheckConstraint(
            "quantity_before >= 0 AND quantity_after >= 0 "
            "AND reserved_before >= 0 AND reserved_after >= 0 "
            "AND reserved_before <= quantity_before "
            "AND reserved_after <= quantity_after",
            name="ck_inventory_movements_balances_nonnegative",
        ),
        CheckConstraint(
            "quantity_after = quantity_before + quantity_delta "
            "AND reserved_after = reserved_before + reserved_delta",
            name="ck_inventory_movements_balance_deltas",
        ),
        CheckConstraint(
            "quantity_delta <> 0 OR reserved_delta <> 0",
            name="ck_inventory_movements_nonzero_delta",
        ),
        Index("ix_inventory_movements_inventory_created", "inventory_id", "created_at"),
        Index("ix_inventory_movements_pharmacy_created", "pharmacy_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pharmacy_id: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_before: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_before: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_type: Mapped[str] = mapped_column(String(16), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
