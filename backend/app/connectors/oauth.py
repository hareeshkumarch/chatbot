import secrets

from app.config import get_settings
from app.connectors.saas.confluence_connector import ConfluenceConnector
from app.connectors.saas.dropbox_connector import DropboxConnector
from app.connectors.saas.github_connector import GitHubConnector
from app.connectors.saas.google_drive_connector import GoogleDriveConnector
from app.connectors.saas.jira_connector import JiraConnector
from app.connectors.saas.notion_connector import NotionConnector
from app.connectors.saas.slack_connector import SlackConnector
from app.connectors.saas.zendesk_connector import ZendeskConnector

OAUTH_HANDLERS = {
    "slack": SlackConnector,
    "github": GitHubConnector,
    "jira": JiraConnector,
    "confluence": ConfluenceConnector,
    "notion": NotionConnector,
    "google_drive": GoogleDriveConnector,
    "dropbox": DropboxConnector,
    "zendesk": ZendeskConnector,
}

OAUTH_SETTINGS_KEYS: dict[str, tuple[str, str, str]] = {
    "slack": ("slack_client_id", "slack_client_secret", "slack_redirect_uri"),
    "github": ("github_client_id", "github_client_secret", "github_redirect_uri"),
    "jira": ("jira_client_id", "jira_client_secret", "jira_redirect_uri"),
    "confluence": ("jira_client_id", "jira_client_secret", "confluence_redirect_uri"),
    "notion": ("notion_client_id", "notion_client_secret", "notion_redirect_uri"),
    "google_drive": ("google_drive_client_id", "google_drive_client_secret", "google_drive_redirect_uri"),
    "dropbox": ("dropbox_client_id", "dropbox_client_secret", "dropbox_redirect_uri"),
    "zendesk": ("zendesk_client_id", "zendesk_client_secret", "zendesk_redirect_uri"),
}

SUBDOMAIN_CONNECTOR_TYPES = {"zendesk"}


def generate_state() -> str:
    return secrets.token_urlsafe(24)


def build_authorize_url(connector_type: str, state: str, config: dict | None = None) -> str:
    settings = get_settings()
    handler = OAUTH_HANDLERS[connector_type]
    client_id_key, _, redirect_uri_key = OAUTH_SETTINGS_KEYS[connector_type]
    client_id = getattr(settings, client_id_key)
    redirect_uri = getattr(settings, redirect_uri_key)
    if connector_type in SUBDOMAIN_CONNECTOR_TYPES:
        subdomain = (config or {}).get("subdomain", "")
        return handler.authorize_url(client_id, redirect_uri, state, subdomain=subdomain)
    return handler.authorize_url(client_id, redirect_uri, state)


async def exchange_code(connector_type: str, code: str, config: dict | None = None) -> dict:
    settings = get_settings()
    handler = OAUTH_HANDLERS[connector_type]
    client_id_key, client_secret_key, redirect_uri_key = OAUTH_SETTINGS_KEYS[connector_type]
    client_id = getattr(settings, client_id_key)
    client_secret = getattr(settings, client_secret_key)
    redirect_uri = getattr(settings, redirect_uri_key)
    if connector_type in SUBDOMAIN_CONNECTOR_TYPES:
        subdomain = (config or {}).get("subdomain", "")
        return await handler.exchange_code(client_id, client_secret, code, redirect_uri, subdomain=subdomain)
    return await handler.exchange_code(client_id, client_secret, code, redirect_uri)
