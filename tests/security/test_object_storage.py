import pytest

from src.pharmaviyum.storage.object_storage import ObjectStorage


@pytest.mark.unit
def test_tenant_key_is_namespaced_by_pharmacy_and_job():
    assert (
        ObjectStorage.tenant_key(42, "job-123", ".pdf")
        == "ingestion/42/job-123.pdf"
    )


@pytest.mark.unit
def test_tenant_key_rejects_path_traversal():
    with pytest.raises(ValueError):
        ObjectStorage.tenant_key(42, "../job", ".pdf")


@pytest.mark.unit
def test_tenant_key_rejects_unsupported_suffix():
    with pytest.raises(ValueError):
        ObjectStorage.tenant_key(42, "job-123", ".exe")
