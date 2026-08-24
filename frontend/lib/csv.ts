export type CsvValue = string | number | boolean | null | undefined;

function escapeCell(value: CsvValue): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

/**
 * Build and download a CSV file client-side.
 * Rows are objects; `headers` maps column key → label (defaults to keys).
 */
export function downloadCsv(
  filename: string,
  rows: Record<string, CsvValue>[],
  headers?: Record<string, string>,
): void {
  const keys = rows.length > 0 ? Object.keys(rows[0]) : Object.keys(headers ?? {});
  const labels = keys.map((k) => headers?.[k] ?? k);
  const lines = [labels.map(escapeCell).join(",")];
  for (const row of rows) {
    lines.push(keys.map((k) => escapeCell(row[k])).join(","));
  }
  const blob = new Blob([`\uFEFF${lines.join("\n")}`], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".csv") ? filename : `${filename}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
