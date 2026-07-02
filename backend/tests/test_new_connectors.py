import pytest

from app.connectors import oauth
from app.core.exceptions import ValidationAppError
from app.services.connector_service import REQUIRED_CONFIG_FIELDS, REQUIRED_CREDENTIAL_FIELDS, ConnectorService, auth_mode_for


def test_confluence_reuses_jira_client_credentials():
    assert oauth.OAUTH_SETTINGS_KEYS["confluence"][:2] == oauth.OAUTH_SETTINGS_KEYS["jira"][:2]


def test_confluence_has_its_own_redirect_uri():
    assert oauth.OAUTH_SETTINGS_KEYS["confluence"][2] != oauth.OAUTH_SETTINGS_KEYS["jira"][2]


def test_build_authorize_url_dispatches_to_correct_handler(monkeypatch):
    url = oauth.build_authorize_url("notion", "state123")
    assert url.startswith("https://api.notion.com/v1/oauth/authorize")


def test_build_authorize_url_embeds_subdomain_for_zendesk():
    url = oauth.build_authorize_url("zendesk", "state123", {"subdomain": "acmecorp"})
    assert url.startswith("https://acmecorp.zendesk.com/oauth/authorizations/new")


def test_build_authorize_url_zendesk_without_subdomain_defaults_empty():
    url = oauth.build_authorize_url("zendesk", "state123", {})
    assert url.startswith("https://.zendesk.com/oauth/authorizations/new")


async def test_exchange_code_passes_subdomain_to_zendesk_handler(monkeypatch):
    captured = {}

    async def fake_exchange(client_id, client_secret, code, redirect_uri, subdomain=""):
        captured["subdomain"] = subdomain
        return {"access_token": "tok"}

    monkeypatch.setattr(oauth.OAUTH_HANDLERS["zendesk"], "exchange_code", staticmethod(fake_exchange))
    result = await oauth.exchange_code("zendesk", "auth-code", {"subdomain": "acmecorp"})
    assert captured["subdomain"] == "acmecorp"
    assert result["access_token"] == "tok"


def test_new_connector_types_have_correct_auth_mode():
    assert auth_mode_for("notion") == "oauth"
    assert auth_mode_for("google_drive") == "oauth"
    assert auth_mode_for("dropbox") == "oauth"
    assert auth_mode_for("confluence") == "oauth"
    assert auth_mode_for("zendesk") == "oauth"
    assert auth_mode_for("linear") == "credentials"


def test_linear_requires_api_key_credential():
    assert REQUIRED_CREDENTIAL_FIELDS["linear"] == ["api_key"]


def test_zendesk_requires_subdomain_config():
    assert REQUIRED_CONFIG_FIELDS["zendesk"] == ["subdomain"]


class _FakeSession:
    def add(self, obj):
        pass

    async def commit(self):
        pass

    async def flush(self):
        pass


async def test_create_zendesk_connector_without_subdomain_raises():
    service = ConnectorService(_FakeSession())
    with pytest.raises(ValidationAppError):
        await service.create_connector("tenant-1", "zendesk", "Support", {}, {})


async def test_create_zendesk_connector_with_subdomain_succeeds():
    service = ConnectorService(_FakeSession())
    connector = await service.create_connector("tenant-1", "zendesk", "Support", {"subdomain": "acmecorp"}, {})
    assert connector.status == "pending_auth"
    assert connector.config["subdomain"] == "acmecorp"


async def test_create_linear_connector_without_api_key_raises():
    service = ConnectorService(_FakeSession())
    with pytest.raises(ValidationAppError):
        await service.create_connector("tenant-1", "linear", "Linear", {}, {})


async def test_create_linear_connector_with_api_key_succeeds():
    service = ConnectorService(_FakeSession())
    connector = await service.create_connector("tenant-1", "linear", "Linear", {}, {"api_key": "lin_api_xxx"})
    assert connector.status == "connected"
