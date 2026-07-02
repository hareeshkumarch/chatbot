from app.connectors.base import BaseConnector
from app.connectors.cloud.aws_s3 import S3Connector
from app.connectors.cloud.azure_blob import AzureBlobConnector
from app.connectors.cloud.gcs import GCSConnector
from app.connectors.database.mongo_connector import MongoConnector
from app.connectors.database.sql_connector import SQLConnector
from app.connectors.saas.confluence_connector import ConfluenceConnector
from app.connectors.saas.dropbox_connector import DropboxConnector
from app.connectors.saas.github_connector import GitHubConnector
from app.connectors.saas.google_drive_connector import GoogleDriveConnector
from app.connectors.saas.jira_connector import JiraConnector
from app.connectors.saas.linear_connector import LinearConnector
from app.connectors.saas.notion_connector import NotionConnector
from app.connectors.saas.slack_connector import SlackConnector
from app.connectors.saas.zendesk_connector import ZendeskConnector
from app.connectors.web.scraper import WebScraperConnector

CONNECTOR_CLASSES: dict[str, type[BaseConnector]] = {
    "s3": S3Connector,
    "azure_blob": AzureBlobConnector,
    "gcs": GCSConnector,
    "slack": SlackConnector,
    "github": GitHubConnector,
    "jira": JiraConnector,
    "confluence": ConfluenceConnector,
    "notion": NotionConnector,
    "google_drive": GoogleDriveConnector,
    "dropbox": DropboxConnector,
    "zendesk": ZendeskConnector,
    "linear": LinearConnector,
    "sql": SQLConnector,
    "mongodb": MongoConnector,
    "web": WebScraperConnector,
}

OAUTH_CONNECTOR_TYPES = {"slack", "github", "jira", "confluence", "notion", "google_drive", "dropbox", "zendesk"}
CREDENTIAL_CONNECTOR_TYPES = {"s3", "azure_blob", "gcs", "sql", "mongodb", "linear"}
CONFIG_ONLY_CONNECTOR_TYPES = {"web"}


def build_connector(connector_type: str, credentials: dict, config: dict | None = None) -> BaseConnector:
    if connector_type not in CONNECTOR_CLASSES:
        raise KeyError(f"unknown connector type: {connector_type}")
    return CONNECTOR_CLASSES[connector_type](credentials, config)
