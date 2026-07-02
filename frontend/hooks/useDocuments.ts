"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DocumentRecord } from "@/lib/types";
import { deleteDocument as apiDeleteDocument, listDocuments, uploadDocument as apiUploadDocument } from "@/lib/api";

const POLL_INTERVAL_MS = 4000;

export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadingCount, setUploadingCount] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await listDocuments();
      setDocuments(list);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "failed to load documents");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const hasPendingWork = documents.some((doc) => doc.status === "pending" || doc.status === "processing");
    if (hasPendingWork && !pollRef.current) {
      pollRef.current = setInterval(refresh, POLL_INTERVAL_MS);
    }
    if (!hasPendingWork && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [documents, refresh]);

  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArray = Array.from(files);
      setUploadingCount((count) => count + fileArray.length);
      try {
        for (const file of fileArray) {
          const created = await apiUploadDocument(file);
          setDocuments((prev) => [created, ...prev]);
        }
      } finally {
        setUploadingCount((count) => Math.max(0, count - fileArray.length));
      }
    },
    [],
  );

  const removeDocument = useCallback(async (documentId: string) => {
    await apiDeleteDocument(documentId);
    setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
  }, []);

  return { documents, isLoading, error, uploadingCount, refresh, uploadFiles, removeDocument };
}
