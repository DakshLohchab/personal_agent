from unittest.mock import Mock

from botocore.exceptions import ClientError

from services.storage.fake import FakeObjectStore
from services.storage.r2 import R2ObjectStore, R2Settings


def test_fake_object_store_supports_upload_completion_and_delete() -> None:
    store = FakeObjectStore()
    store.put_object("users/u/files/f.txt", size_bytes=12, content_type="text/plain")

    metadata = store.head_object("users/u/files/f.txt")
    assert metadata is not None
    assert metadata.size_bytes == 12
    assert store.create_presigned_download("users/u/files/f.txt", expires_in=30).startswith(
        "https://fake-r2.invalid/"
    )

    store.delete_object("users/u/files/f.txt")
    assert store.head_object("users/u/files/f.txt") is None


def test_r2_adapter_uses_s3_operations_without_real_credentials() -> None:
    client = Mock()
    client.generate_presigned_url.side_effect = ["put-url", "get-url"]
    client.head_object.return_value = {"ContentLength": 4, "ContentType": "text/plain"}
    store = R2ObjectStore(
        R2Settings("account", "bucket", "key", "secret", "https://r2.invalid"),
        client,
    )

    assert (
        store.create_presigned_upload("key", content_type="text/plain", expires_in=10)
        == "put-url"
    )
    assert store.create_presigned_download("key", expires_in=10) == "get-url"
    assert store.head_object("key").size_bytes == 4
    store.delete_object("key")
    client.delete_object.assert_called_once_with(Bucket="bucket", Key="key")


def test_r2_head_returns_none_for_missing_object() -> None:
    client = Mock()
    client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404"}}, "HeadObject"
    )
    store = R2ObjectStore(
        R2Settings("account", "bucket", "key", "secret", "https://r2.invalid"),
        client,
    )

    assert store.head_object("missing") is None
