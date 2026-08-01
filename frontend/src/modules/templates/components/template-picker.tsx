/** Template picker — loads a saved template into the analysis form.

Placed above the failure input on the Failure Analysis page. Shows a
dropdown of the user's templates; selecting one fills the content,
source type, and title fields. Hidden when the user has no templates.
*/

import { LayoutTemplate } from "lucide-react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTemplates } from "@/modules/templates/hooks/use-templates";
import type { AnalysisTemplate } from "@/modules/templates/types";

interface TemplatePickerProps {
  /** Called when the user selects a template to load. */
  onSelectTemplate: (template: AnalysisTemplate) => void;
}

export function TemplatePicker({ onSelectTemplate }: TemplatePickerProps) {
  const { data, isLoading } = useTemplates(1);
  const templates = data?.items ?? [];

  // Hide the whole section when there is nothing to load.
  if (!isLoading && templates.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl border bg-card p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <LayoutTemplate className="h-4 w-4" />
          Templates
          <span className="text-xs font-normal text-muted-foreground/60">
            load a saved failure pattern
          </span>
        </div>
        <Button asChild variant="ghost" size="sm" className="h-8 px-2 text-xs">
          <Link to="/templates">Manage templates</Link>
        </Button>
      </div>
      <Select
        value=""
        onValueChange={(id) => {
          const template = templates.find((t) => t.id === id);
          if (template) onSelectTemplate(template);
        }}
      >
        <SelectTrigger
          className="w-full sm:max-w-sm"
          aria-label="Load a template"
        >
          <SelectValue placeholder={isLoading ? "Loading templates..." : "Choose a template..."} />
        </SelectTrigger>
        <SelectContent>
          {templates.map((template) => (
            <SelectItem key={template.id} value={template.id}>
              {template.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
