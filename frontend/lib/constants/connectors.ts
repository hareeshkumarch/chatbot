import { Database, Globe } from "lucide-react";
import {
  AWSIcon,
  AzureIcon,
  GoogleCloudIcon,
  SlackIcon,
  GitHubIcon,
  JiraIcon,
  MongoDBIcon,
  ConfluenceIcon,
  NotionIcon,
  GoogleDriveIcon,
  DropboxIcon,
  ZendeskIcon,
  LinearAppIcon,
} from "@/components/icons/BrandIcons";
import type { ConnectorType } from "@/lib/types";

interface ConnectorMeta {
  label: string;
  description: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

export const CONNECTOR_META: Record<ConnectorType, ConnectorMeta> = {
  s3: { label: "Amazon S3", description: "Buckets and objects", icon: AWSIcon },
  azure_blob: { label: "Azure Blob Storage", description: "Containers and blobs", icon: AzureIcon },
  gcs: { label: "Google Cloud Storage", description: "Buckets and objects", icon: GoogleCloudIcon },
  slack: { label: "Slack", description: "Channels and messages", icon: SlackIcon },
  github: { label: "GitHub", description: "Repositories, issues, and code", icon: GitHubIcon },
  jira: { label: "Jira", description: "Projects and issues", icon: JiraIcon },
  confluence: { label: "Confluence", description: "Spaces and pages", icon: ConfluenceIcon },
  notion: { label: "Notion", description: "Pages and databases", icon: NotionIcon },
  google_drive: { label: "Google Drive", description: "Docs, sheets, and files", icon: GoogleDriveIcon },
  dropbox: { label: "Dropbox", description: "Files and folders", icon: DropboxIcon },
  zendesk: { label: "Zendesk", description: "Support tickets", icon: ZendeskIcon },
  linear: { label: "Linear", description: "Issues and projects", icon: LinearAppIcon },
  sql: { label: "SQL Database", description: "Postgres, MySQL, SQL Server", icon: Database },
  mongodb: { label: "MongoDB", description: "Collections and documents", icon: MongoDBIcon },
  web: { label: "Web Pages", description: "Crawled and indexed URLs", icon: Globe },
};

export const CONNECTOR_TYPE_ORDER: ConnectorType[] = [
  "s3",
  "azure_blob",
  "gcs",
  "slack",
  "github",
  "jira",
  "confluence",
  "notion",
  "google_drive",
  "dropbox",
  "zendesk",
  "linear",
  "sql",
  "mongodb",
  "web",
];
