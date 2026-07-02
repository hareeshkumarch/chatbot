"use client";

import { useMemo, useState } from "react";
import type { Connector, ConnectorTypeInfo } from "@/lib/types";
import { CONNECTOR_META, CONNECTOR_TYPE_ORDER } from "@/lib/constants/connectors";
import { Modal } from "@/components/ui/Modal";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

interface AddConnectorModalProps {
  open: boolean;
  onClose: () => void;
  types: ConnectorTypeInfo[];
  onCreate: (payload: { type: string; name: string; config?: Record<string, unknown>; credentials?: Record<string, unknown> }) => Promise<Connector>;
  onAuthorizeAfterCreate: (id: string) => Promise<void>;
}

const MULTILINE_FIELDS = new Set(["service_account_json", "urls"]);
const SECRET_FIELDS = new Set(["access_key_id", "secret_access_key", "connection_string", "connection_url", "service_account_json"]);

function humanizeField(field: string): string {
  return field
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function AddConnectorModal({ open, onClose, types, onCreate, onAuthorizeAfterCreate }: AddConnectorModalProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const typeInfo = useMemo(() => types.find((t) => t.type === selectedType) ?? null, [types, selectedType]);

  const reset = () => {
    setSelectedType(null);
    setName("");
    setFieldValues({});
    setError(null);
  };

  const close = () => {
    reset();
    onClose();
  };

  const handleCreate = async () => {
    if (!typeInfo || !name.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const config: Record<string, unknown> = {};
      const credentials: Record<string, unknown> = {};

      for (const field of typeInfo.required_config_fields) {
        const raw = fieldValues[field] ?? "";
        config[field] = field === "urls" ? raw.split("\n").map((line) => line.trim()).filter(Boolean) : raw;
      }
      for (const field of typeInfo.required_credential_fields) {
        credentials[field] = fieldValues[field] ?? "";
      }

      const created = await onCreate({
        type: typeInfo.type,
        name: name.trim(),
        config: Object.keys(config).length > 0 ? config : undefined,
        credentials: Object.keys(credentials).length > 0 ? credentials : undefined,
      });

      if (typeInfo.auth_mode === "oauth") {
        await onAuthorizeAfterCreate(created.id);
      }
      close();
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to create connector");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal open={open} onClose={close} title="Connect a source">
      {!typeInfo ? (
        <div className="grid grid-cols-3 gap-2">
          {CONNECTOR_TYPE_ORDER.map((type) => {
            const meta = CONNECTOR_META[type];
            const Icon = meta.icon;
            return (
              <button
                key={type}
                type="button"
                onClick={() => setSelectedType(type)}
                className="flex flex-col items-center gap-2 rounded-sm border border-line p-3 text-center hover:border-route hover:bg-route-soft"
              >
                <Icon className="h-5 w-5 text-ink" strokeWidth={1.6} />
                <span className="text-xs text-ink">{meta.label}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <button type="button" onClick={() => setSelectedType(null)} className="self-start text-xs text-ink-faint hover:text-ink">
            ← Choose a different source
          </button>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-ink-muted">Name</label>
            <Input value={name} onChange={(event) => setName(event.target.value)} placeholder={CONNECTOR_META[typeInfo.type].label} />
          </div>

          {typeInfo.required_config_fields.map((field) => (
            <div key={field}>
              <label className="mb-1.5 block text-xs font-medium text-ink-muted">
                {humanizeField(field)}
                {field === "urls" && " (one per line)"}
              </label>
              {MULTILINE_FIELDS.has(field) ? (
                <Textarea rows={3} value={fieldValues[field] ?? ""} onChange={(event) => setFieldValues((prev) => ({ ...prev, [field]: event.target.value }))} />
              ) : (
                <Input value={fieldValues[field] ?? ""} onChange={(event) => setFieldValues((prev) => ({ ...prev, [field]: event.target.value }))} />
              )}
            </div>
          ))}

          {typeInfo.required_credential_fields.map((field) => (
            <div key={field}>
              <label className="mb-1.5 block text-xs font-medium text-ink-muted">{humanizeField(field)}</label>
              {MULTILINE_FIELDS.has(field) ? (
                <Textarea rows={4} value={fieldValues[field] ?? ""} onChange={(event) => setFieldValues((prev) => ({ ...prev, [field]: event.target.value }))} />
              ) : (
                <Input
                  type={SECRET_FIELDS.has(field) ? "password" : "text"}
                  value={fieldValues[field] ?? ""}
                  onChange={(event) => setFieldValues((prev) => ({ ...prev, [field]: event.target.value }))}
                />
              )}
            </div>
          ))}

          {typeInfo.auth_mode === "oauth" && (
            <p className="rounded-sm bg-surface-sunken px-3 py-2 text-xs text-ink-muted">
              You will be redirected to {CONNECTOR_META[typeInfo.type].label} to authorize access after creating this connector.
            </p>
          )}

          {error && <p className="text-sm text-attn">{error}</p>}

          <Button onClick={handleCreate} disabled={isSubmitting || !name.trim()} className={cn("mt-2 w-full")}>
            {isSubmitting ? "Creating…" : typeInfo.auth_mode === "oauth" ? "Continue to authorize" : "Connect"}
          </Button>
        </div>
      )}
    </Modal>
  );
}
