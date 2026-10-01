from src.pharmaviyum.schemas.pos_schema import POSItem, POSTransactionCreate


def test_pos_item_converts_pack_blister_and_unit_inputs() -> None:
    item = POSItem(product_id=7, packs=2, blisters=1, units=3)
    assert item.packs == 2
    assert item.blisters == 1
    assert item.units == 3


def test_pos_transaction_requires_payment_method_and_items() -> None:
    data = POSTransactionCreate(
        pharmacy_id=1,
        patient_id=2,
        payment_method="cash",
        items=[POSItem(product_id=7, units=2)],
    )
    assert data.payment_method == "cash"
    assert len(data.items) == 1


def test_pos_transaction_rejects_unknown_payment_method() -> None:
    try:
        POSTransactionCreate(
            pharmacy_id=1,
            patient_id=2,
            payment_method="crypto",
            items=[POSItem(product_id=7, units=1)],
        )
    except ValueError:
        return
    raise AssertionError("invalid payment method should be rejected")
