"use client";

import { useEffect, useState } from "react";
import type { Connector, ConnectorTypeInfo } from "@/lib/types";
import { CONNECTOR_META } from "@/lib/constants/connectors";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

interface ConfigureConnectorModalProps {
  connector: Connector | null;
  typeInfo: ConnectorTypeInfo | null;
  onClose: () => void;
  onSave: (id: string, payload: { name?: string; config?: Record<string, unknown> }) => Promise<Connector>;
  onSaveCredentials: (id: string, credentials: Record<string, unknown>) => Promise<Connector>;
}

const MULTILINE_FIELDS = new Set(["service_account_json", "urls"]);
const SECRET_FIELDS = new Set(["access_key_id", "secret_access_key", "connection_string", "connection_url", "service_account_json"]);

function humanizeField(field: string): string {
  return field
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function ConfigureConnectorModal({ connector, typeInfo, onClose, onSave, onSaveCredentials }: ConfigureConnectorModalProps) {
  const [name, setName] = useState("");
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [credentialValues, setCredentialValues] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!connector) return;
    setName(connector.name);
    const config: Record<string, string> = {};
    for (const [key, value] of Object.entries(connector.config)) {
      config[key] = Array.isArray(value) ? value.join("\n") : String(value);
    }
    setConfigValues(config);
    setCredentialValues({});
  }, [connector]);

  if (!connector || !typeInfo) return null;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const config: Record<string, unknown> = {};
      for (const field of typeInfo.required_config_fields) {
        const raw = configValues[field] ?? "";
        config[field] = field === "urls" ? raw.split("\n").map((line) => line.trim()).filter(Boolean) : raw;
      }
      await onSave(connector.id, { name, config: Object.keys(config).length > 0 ? config : undefined });

      const hasCredentialInput = typeInfo.required_credential_fields.some((field) => (credentialValues[field] ?? "").length > 0);
      if (hasCredentialInput) {
        await onSaveCredentials(connector.id, credentialValues);
      }
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal open onClose={onClose} title={`Configure ${CONNECTOR_META[connector.type].label}`}>
      <div className="flex flex-col gap-3">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-ink-muted">Name</label>
          <Input value={name} onChange={(event) => setName(event.target.value)} />
        </div>

        {typeInfo.required_config_fields.map((field) => (
          <div key={field}>
            <label className="mb-1.5 block text-xs font-medium text-ink-muted">{humanizeField(field)}</label>
            {MULTILINE_FIELDS.has(field) ? (
              <Textarea rows={3} value={configValues[field] ?? ""} onChange={(event) => setConfigValues((prev) => ({ ...prev, [field]: event.target.value }))} />
            ) : (
              <Input value={configValues[field] ?? ""} onChange={(event) => setConfigValues((prev) => ({ ...prev, [field]: event.target.value }))} />
            )}
          </div>
        ))}

        {typeInfo.required_credential_fields.length > 0 && (
          <>
            <div className="mt-2 border-t border-line pt-3">
              <p className="text-xs font-medium text-ink-muted">Rotate credentials</p>
              <p className="mt-0.5 text-xs text-ink-faint">Leave blank to keep the current values.</p>
            </div>
            {typeInfo.required_credential_fields.map((field) => (
              <div key={field}>
                <label className="mb-1.5 block text-xs font-medium text-ink-muted">{humanizeField(field)}</label>
                {MULTILINE_FIELDS.has(field) ? (
                  <Textarea rows={4} value={credentialValues[field] ?? ""} onChange={(event) => setCredentialValues((prev) => ({ ...prev, [field]: event.target.value }))} />
                ) : (
                  <Input
                    type={SECRET_FIELDS.has(field) ? "password" : "text"}
                    value={credentialValues[field] ?? ""}
                    onChange={(event) => setCredentialValues((prev) => ({ ...prev, [field]: event.target.value }))}
                  />
                )}
              </div>
            ))}
          </>
        )}

        <Button onClick={handleSave} disabled={isSaving} className="mt-2 w-full">
          {isSaving ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </Modal>
  );
}
