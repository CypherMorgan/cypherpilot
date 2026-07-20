/** Shared export actions — copy or download analysis results.
 *
 * Uses shadcn DropdownMenu for a consistent UX across all modules.
 */

import { useState } from "react";
import { Copy, Download, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface ExportActionsProps {
  /** Generate a Markdown string from the current result. */
  formatAsMarkdown: () => string;
  /** Generate a JSON string from the current result. */
  formatAsJson?: () => string;
  /** Filename prefix used for downloads (e.g. "failure-analysis", "requirement-analysis"). */
  filenamePrefix?: string;
}

/**
 * Copy text to clipboard and return whether it succeeded.
 */
async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

export function ExportActions({
  formatAsMarkdown,
  formatAsJson,
  filenamePrefix = "analysis",
}: ExportActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (format: "json" | "markdown") => {
    const text =
      format === "json" && formatAsJson
        ? formatAsJson()
        : formatAsMarkdown();
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = (format: "json" | "markdown") => {
    const text =
      format === "json" && formatAsJson
        ? formatAsJson()
        : formatAsMarkdown();
    const blob = new Blob([text], {
      type: format === "json" ? "application/json" : "text/markdown",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filenamePrefix}.${format === "json" ? "json" : "md"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          {copied ? (
            <>
              <Check className="mr-2 h-4 w-4" />
              Copied
            </>
          ) : (
            <>
              <Download className="mr-2 h-4 w-4" />
              Export
            </>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleCopy("json")}>
          <Copy className="mr-2 h-4 w-4" />
          Copy as JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleCopy("markdown")}>
          <Copy className="mr-2 h-4 w-4" />
          Copy as Markdown
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleDownload("json")}>
          <Download className="mr-2 h-4 w-4" />
          Download JSON
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleDownload("markdown")}>
          <Download className="mr-2 h-4 w-4" />
          Download Markdown
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
