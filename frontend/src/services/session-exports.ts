/** Server-side session export — download a session as Markdown, JSON, or CSV.
 *
 * Unlike the client-side ExportActions (which rebuild the document in the
 * browser), this downloads the authoritative file from the backend, which
 * also means the CSV spreadsheets and server-side formatting stay in sync.
 * The request goes through the authenticated apiClient so the bearer token
 * is attached automatically.
 */

import { apiClient } from "@/services/api-client";

export type SessionExportFormat = "markdown" | "json" | "csv";

const FALLBACK_EXTENSIONS: Record<SessionExportFormat, string> = {
  markdown: "md",
  json: "json",
  csv: "csv",
};

/**
 * Extract the filename from a Content-Disposition header when present.
 */
function filenameFromContentDisposition(
  header: string | undefined,
  fallback: string,
): string {
  if (!header) return fallback;
  const match = /filename="?([^";]+)"?/.exec(header);
  return match && match[1] ? match[1] : fallback;
}

/**
 * Download a session export file.
 *
 * @param exportPath API path of the export endpoint,
 *   e.g. `/failures/sessions/<id>/export`.
 * @param format One of `markdown`, `json`, `csv`.
 */
export async function downloadSessionExport(
  exportPath: string,
  format: SessionExportFormat,
): Promise<void> {
  const response = await apiClient.get<Blob>(exportPath, {
    params: { format },
    responseType: "blob",
  });

  const fallback = `session-export.${FALLBACK_EXTENSIONS[format]}`;
  const filename = filenameFromContentDisposition(
    response.headers["content-disposition"],
    fallback,
  );

  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
