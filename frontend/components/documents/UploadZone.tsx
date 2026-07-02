"use client";

import { useCallback, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { cn } from "@/lib/utils";

const ACCEPTED_EXTENSIONS = ".pdf,.docx,.csv,.xlsx,.txt,.md,.html";

interface UploadZoneProps {
  onUpload: (files: FileList) => void;
  uploadingCount: number;
}

export function UploadZone({ onUpload, uploadingCount }: UploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();
      setIsDragging(false);
      if (event.dataTransfer.files.length > 0) onUpload(event.dataTransfer.files);
    },
    [onUpload],
  );

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-md border border-dashed px-6 py-10 text-center transition-colors",
        isDragging ? "border-route bg-route-soft" : "border-line-strong hover:border-route",
      )}
    >
      <UploadCloud className={cn("h-6 w-6", isDragging ? "text-route" : "text-ink-faint")} strokeWidth={1.5} />
      <p className="text-sm text-ink">Drop files here or click to browse</p>
      <p className="font-mono text-xs text-ink-faint">PDF, DOCX, CSV, XLSX, TXT, MD, HTML</p>
      {uploadingCount > 0 && <p className="mt-1 text-xs text-route">Uploading {uploadingCount} file{uploadingCount === 1 ? "" : "s"}…</p>}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        onChange={(event) => {
          if (event.target.files && event.target.files.length > 0) onUpload(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
