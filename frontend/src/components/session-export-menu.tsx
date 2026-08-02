/** Server-side session export menu — download the session as Markdown,
 * JSON, or CSV straight from the backend. Used on the session detail pages.
 */

import { useState } from "react";
import { Download, FileJson, FileSpreadsheet, FileText, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  downloadSessionExport,
  type SessionExportFormat,
} from "@/services/session-exports";

interface SessionExportMenuProps {
  /** API path of the export endpoint, e.g. `/failures/sessions/<id>/export`. */
  exportPath: string;
  /** Disable the menu while the session is still loading. */
  disabled?: boolean;
}

export function SessionExportMenu({ exportPath, disabled = false }: SessionExportMenuProps) {
  const [downloading, setDownloading] = useState<SessionExportFormat | null>(null);

  const handleDownload = async (format: SessionExportFormat) => {
    setDownloading(format);
    try {
      await downloadSessionExport(exportPath, format);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className="gap-1.5 text-xs shrink-0"
          disabled={disabled}
        >
          {downloading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Download className="h-3.5 w-3.5" />
          )}
          <span className="hidden sm:inline">Export</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Export Session</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => handleDownload("markdown")}
          disabled={downloading !== null}
        >
          <FileText className="mr-2 h-4 w-4" />
          Download Markdown
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleDownload("json")}
          disabled={downloading !== null}
        >
          <FileJson className="mr-2 h-4 w-4" />
          Download JSON
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => handleDownload("csv")}
          disabled={downloading !== null}
        >
          <FileSpreadsheet className="mr-2 h-4 w-4" />
          Download CSV
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
