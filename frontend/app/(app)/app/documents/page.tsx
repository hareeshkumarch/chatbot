"use client";

import { Topbar } from "@/components/layout/Topbar";
import { UploadZone } from "@/components/documents/UploadZone";
import { DocumentList } from "@/components/documents/DocumentList";
import { Skeleton } from "@/components/ui/Skeleton";
import { ErrorState } from "@/components/ui/ErrorState";
import { useDocuments } from "@/hooks/useDocuments";
import { useToastStore } from "@/store/toastStore";

export default function DocumentsPage() {
  const { documents, isLoading, error, refresh, uploadingCount, uploadFiles, removeDocument } = useDocuments();
  const push = useToastStore((state) => state.push);

  const handleUpload = async (files: FileList) => {
    try {
      await uploadFiles(files);
    } catch (error) {
      push(error instanceof Error ? error.message : "upload failed", "attn");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await removeDocument(id);
    } catch (error) {
      push(error instanceof Error ? error.message : "failed to delete document", "attn");
    }
  };

  return (
    <div className="flex h-full flex-1 flex-col overflow-y-auto">
      <Topbar title="Documents" description="Files indexed into your knowledge base for retrieval" />
      <div className="flex flex-col gap-6 p-4 md:p-8">
        <UploadZone onUpload={handleUpload} uploadingCount={uploadingCount} />
        {isLoading ? (
          <div className="flex flex-col divide-y divide-line rounded-md border border-line bg-surface">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between gap-4 px-4 py-3.5">
                <div className="flex flex-1 items-center gap-3">
                  <Skeleton className="h-4 w-4 shrink-0 rounded-sm" />
                  <div className="flex flex-1 flex-col gap-1.5">
                    <Skeleton className="h-3 w-1/3" />
                    <Skeleton className="h-2.5 w-1/2" />
                  </div>
                </div>
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={refresh} />
        ) : (
          <DocumentList documents={documents} onDelete={handleDelete} />
        )}
      </div>
    </div>
  );
}
