import type { ContentBlock } from "@/lib/types";
import { MessageChart } from "@/components/chat/MessageChart";
import { MessageTable } from "@/components/chat/MessageTable";

export function MessageBlocks({ blocks }: { blocks: ContentBlock[] }) {
  if (blocks.length === 0) return null;

  return (
    <div className="flex w-full flex-col gap-2">
      {blocks.map((block, index) => {
        if (block.type === "table") {
          return <MessageTable key={`table-${index}`} table={block} />;
        }
        if (block.type === "chart") {
          return <MessageChart key={`chart-${index}`} chart={block} />;
        }
        return null;
      })}
    </div>
  );
}
