import type { ContentTable } from "@/lib/types";

export function MessageTable({ table }: { table: ContentTable }) {
  return (
    <div className="w-full overflow-x-auto rounded-md border border-line bg-surface-sunken">
      {table.title && (
        <p className="border-b border-line px-3 py-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">{table.title}</p>
      )}
      <table className="w-full min-w-[280px] border-collapse text-left text-sm">
        <thead>
          <tr className="border-b border-line bg-surface">
            {table.headers.map((header) => (
              <th key={header} className="px-3 py-2 font-medium text-ink">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-line last:border-b-0">
              {row.map((cell, cellIndex) => (
                <td key={cellIndex} className="px-3 py-2 text-ink-muted">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
