/** TemplatesPage — manage reusable analysis templates.

Full CRUD for the current user's templates: create via dialog, edit
inline in a dialog, delete with confirmation.
*/

import { useState } from "react";
import {
  Calendar,
  LayoutTemplate,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useCreateTemplate,
  useDeleteTemplate,
  useTemplates,
  useUpdateTemplate,
} from "@/modules/templates/hooks/use-templates";
import type { AnalysisTemplate } from "@/modules/templates/types";
import type { InputSourceType } from "@/modules/failure-analysis/types";

type SourceType = InputSourceType;

const SOURCE_LABELS: Record<SourceType, string> = {
  plain_text: "Plain Text",
  markdown: "Markdown",
  ci_log: "CI Log",
  stack_trace: "Stack Trace",
};

interface EditorState {
  id: string | null; // null = creating a new template
  name: string;
  description: string;
  content: string;
  sourceType: SourceType;
}

const EMPTY_EDITOR: EditorState = {
  id: null,
  name: "",
  description: "",
  content: "",
  sourceType: "plain_text",
};

export function TemplatesPage() {
  const { data, isLoading } = useTemplates(1);
  const createMutation = useCreateTemplate();
  const updateMutation = useUpdateTemplate();
  const deleteMutation = useDeleteTemplate();

  const [editor, setEditor] = useState<EditorState>(EMPTY_EDITOR);
  const [editorOpen, setEditorOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<AnalysisTemplate | null>(null);

  const templates = data?.items ?? [];
  const isSaving = createMutation.isPending || updateMutation.isPending;
  const canSave =
    editor.name.trim().length >= 2 && editor.content.trim().length > 0 && !isSaving;

  const openCreate = () => {
    setEditor(EMPTY_EDITOR);
    setEditorOpen(true);
  };

  const openEdit = (template: AnalysisTemplate) => {
    setEditor({
      id: template.id,
      name: template.name,
      description: template.description ?? "",
      content: template.content,
      sourceType: template.source_type,
    });
    setEditorOpen(true);
  };

  const handleSave = () => {
    const payload = {
      name: editor.name.trim(),
      description: editor.description.trim() || null,
      content: editor.content,
      source_type: editor.sourceType,
    };
    if (editor.id) {
      updateMutation.mutate(
        { templateId: editor.id, data: payload },
        { onSuccess: () => setEditorOpen(false) },
      );
    } else {
      createMutation.mutate(payload, { onSuccess: () => setEditorOpen(false) });
    }
  };

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteMutation.mutate(deleteTarget.id);
    setDeleteTarget(null);
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-bold tracking-tight sm:text-2xl">
            Templates
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Reusable failure patterns for quick AI-powered analysis.
          </p>
        </div>
        <Button onClick={openCreate} className="shrink-0">
          <Plus className="mr-2 h-4 w-4" />
          New Template
        </Button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : templates.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <LayoutTemplate className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium">No templates yet</p>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Save common failure patterns (CI log flakes, stack traces,
              config errors) so you can load them into Failure Analysis
              with one click.
            </p>
            <Button className="mt-4" onClick={openCreate}>
              <Plus className="mr-2 h-4 w-4" />
              Create your first template
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {templates.map((template) => (
            <Card key={template.id} className="flex flex-col">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-snug">
                    {template.name}
                  </CardTitle>
                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEdit(template)}
                      aria-label={`Edit ${template.name}`}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => setDeleteTarget(template)}
                      aria-label={`Delete ${template.name}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                {template.description && (
                  <CardDescription>{template.description}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="flex flex-1 flex-col gap-3">
                <pre className="max-h-28 flex-1 overflow-auto whitespace-pre-wrap rounded-md bg-muted/50 p-3 font-mono text-xs text-muted-foreground">
                  {template.content.length > 600
                    ? `${template.content.slice(0, 600)}…`
                    : template.content}
                </pre>
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span className="inline-flex items-center rounded-full border bg-muted/50 px-2 py-0.5 font-medium">
                    {SOURCE_LABELS[template.source_type] ?? template.source_type}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {formatDate(template.updated_at)}
                  </span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create / edit dialog */}
      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editor.id ? "Edit Template" : "New Template"}
            </DialogTitle>
            <DialogDescription>
              {editor.id
                ? "Update the saved failure pattern."
                : "Save a failure pattern for one-click analysis."}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="template-name">Name</Label>
              <Input
                id="template-name"
                placeholder="e.g., CI Pipeline Flake — npm install timeout"
                value={editor.name}
                onChange={(e) => setEditor({ ...editor, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="template-desc">
                Description <span className="text-muted-foreground/60">(optional)</span>
              </Label>
              <Input
                id="template-desc"
                placeholder="What failure does this capture?"
                value={editor.description}
                onChange={(e) =>
                  setEditor({ ...editor, description: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="template-source">Source Type</Label>
              <Select
                value={editor.sourceType}
                onValueChange={(value: SourceType) =>
                  setEditor({ ...editor, sourceType: value })
                }
              >
                <SelectTrigger id="template-source" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(SOURCE_LABELS) as SourceType[]).map((type) => (
                    <SelectItem key={type} value={type}>
                      {SOURCE_LABELS[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="template-content">Content</Label>
              <Textarea
                id="template-content"
                placeholder="Paste the CI/CD log, stack trace, or error output…"
                className="min-h-[180px] font-mono text-xs"
                value={editor.content}
                onChange={(e) =>
                  setEditor({ ...editor, content: e.target.value })
                }
              />
              <p className="text-right text-xs text-muted-foreground">
                {editor.content.length.toLocaleString()} chars
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setEditorOpen(false)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!canSave}>
              {isSaving
                ? "Saving..."
                : editor.id
                  ? "Save Changes"
                  : "Create Template"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete template?</AlertDialogTitle>
            <AlertDialogDescription>
              "{deleteTarget?.name}" will be permanently removed. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
