import pytest
from pydantic import ValidationError

from app.api.v1.chat import ChatStreamRequestBody, ConversationCreateRequest
from app.api.v1.connectors import ConnectorCreateRequest, ConnectorUpdateRequest
from app.api.v1.reports import ReportGenerateRequest
from app.core.limits import (
    CONNECTOR_NAME_MAX_LENGTH,
    MAX_CONFIG_FIELDS,
    MAX_CONNECTOR_IDS,
    MESSAGE_MAX_LENGTH,
    REPORT_QUERY_MAX_LENGTH,
)


def test_chat_message_rejects_empty():
    with pytest.raises(ValidationError):
        ChatStreamRequestBody(message="")


def test_chat_message_rejects_whitespace_only():
    with pytest.raises(ValidationError):
        ChatStreamRequestBody(message="   \n\t  ")


def test_chat_message_trims_surrounding_whitespace():
    body = ChatStreamRequestBody(message="  hello world  ")
    assert body.message == "hello world"


def test_chat_message_rejects_over_limit():
    with pytest.raises(ValidationError):
        ChatStreamRequestBody(message="x" * (MESSAGE_MAX_LENGTH + 1))


def test_chat_message_accepts_at_limit():
    body = ChatStreamRequestBody(message="x" * MESSAGE_MAX_LENGTH)
    assert len(body.message) == MESSAGE_MAX_LENGTH


def test_chat_connector_ids_deduplicated():
    body = ChatStreamRequestBody(message="hi", connector_ids=["a", "b", "a", "c", "b"])
    assert body.connector_ids == ["a", "b", "c"]


def test_chat_connector_ids_drops_empty_strings():
    body = ChatStreamRequestBody(message="hi", connector_ids=["a", "", "b"])
    assert body.connector_ids == ["a", "b"]


def test_chat_connector_ids_rejects_too_many():
    with pytest.raises(ValidationError):
        ChatStreamRequestBody(message="hi", connector_ids=[str(i) for i in range(MAX_CONNECTOR_IDS + 1)])


def test_conversation_title_rejects_over_limit():
    with pytest.raises(ValidationError):
        ConversationCreateRequest(title="x" * 5000)


def test_conversation_title_allows_none():
    body = ConversationCreateRequest()
    assert body.title is None


def test_connector_create_rejects_blank_name():
    with pytest.raises(ValidationError):
        ConnectorCreateRequest(type="s3", name="   ")


def test_connector_create_rejects_blank_type():
    with pytest.raises(ValidationError):
        ConnectorCreateRequest(type="", name="My Bucket")


def test_connector_create_trims_name_and_type():
    body = ConnectorCreateRequest(type="  s3  ", name="  My Bucket  ")
    assert body.type == "s3"
    assert body.name == "My Bucket"


def test_connector_create_rejects_name_over_limit():
    with pytest.raises(ValidationError):
        ConnectorCreateRequest(type="s3", name="x" * (CONNECTOR_NAME_MAX_LENGTH + 1))


def test_connector_create_rejects_too_many_config_fields():
    with pytest.raises(ValidationError):
        ConnectorCreateRequest(type="s3", name="B", config={str(i): i for i in range(MAX_CONFIG_FIELDS + 1)})


def test_connector_create_defaults_are_independent():
    a = ConnectorCreateRequest(type="s3", name="A")
    b = ConnectorCreateRequest(type="s3", name="B")
    a.config["x"] = 1
    assert b.config == {}


def test_connector_update_rejects_blank_name():
    with pytest.raises(ValidationError):
        ConnectorUpdateRequest(name="  ")


def test_connector_update_allows_all_none():
    body = ConnectorUpdateRequest()
    assert body.name is None
    assert body.config is None


def test_report_query_rejects_empty():
    with pytest.raises(ValidationError):
        ReportGenerateRequest(query="")


def test_report_query_rejects_whitespace():
    with pytest.raises(ValidationError):
        ReportGenerateRequest(query="   ")


def test_report_query_trims():
    body = ReportGenerateRequest(query="  revenue summary  ")
    assert body.query == "revenue summary"


def test_report_rejects_invalid_format():
    with pytest.raises(ValidationError):
        ReportGenerateRequest(query="q", format="xlsx")


def test_report_accepts_valid_formats():
    for fmt in ("pdf", "docx", "html"):
        body = ReportGenerateRequest(query="q", format=fmt)
        assert body.format == fmt


def test_report_query_rejects_over_limit():
    with pytest.raises(ValidationError):
        ReportGenerateRequest(query="x" * (REPORT_QUERY_MAX_LENGTH + 1))
