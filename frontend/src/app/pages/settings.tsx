import { Moon, Sun, ExternalLink, Trash2, Loader2, Cpu, Eye, EyeOff, Check, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";

import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { APP_NAME, APP_VERSION } from "@/lib/constants";
import { deleteExpiredSessions } from "@/services/cleanup";
import {
  getAiSettings,
  updateAiSettings,
  type AiSettings,
} from "@/services/settings";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [cleanupResult, setCleanupResult] = useState<{
    deleted: number;
    retention_days: number;
  } | null>(null);
  const [cleanupPending, setCleanupPending] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  // ── AI Provider state ──────────────────────────────────────
  const [aiSettings, setAiSettings] = useState<AiSettings | null>(null);
  const [aiLoading, setAiLoading] = useState(true);
  const [aiSaving, setAiSaving] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiSuccess, setAiSuccess] = useState(false);

  // Editable fields
  const [provider, setProvider] = useState("");
  const [apiKeyVisible, setApiKeyVisible] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [model, setModel] = useState("");
  const [baseUrl, setBaseUrl] = useState("");

  useEffect(() => {
    getAiSettings()
      .then((settings) => {
        setAiSettings(settings);
        setProvider(settings.provider);
        setApiKeyInput(""); // Don't pre-fill masked key
        setModel(
          settings.provider === "openrouter"
            ? settings.openrouter_model
            : settings.provider === "ollama"
              ? settings.ollama_model
              : settings.gemini_model,
        );
        setBaseUrl(settings.ollama_base_url);
      })
      .catch((err) => {
        setAiError(
          (err as { message?: string })?.message ?? "Failed to load AI settings",
        );
      })
      .finally(() => setAiLoading(false));
  }, []);

  const handleSaveAi = async () => {
    setAiSaving(true);
    setAiError(null);
    setAiSuccess(false);
    try {
      const update: Record<string, string | number> = {
        provider,
      };
      if (provider === "openrouter") {
        if (apiKeyInput) update.openrouter_api_key = apiKeyInput;
        if (model) update.openrouter_model = model;
      } else if (provider === "ollama") {
        if (baseUrl) update.ollama_base_url = baseUrl;
        if (model) update.ollama_model = model;
      }
      const result = await updateAiSettings(update);
      setAiSettings(result);
      setApiKeyInput(""); // Clear after save
      setAiSuccess(true);
      setTimeout(() => setAiSuccess(false), 3000);
    } catch (err) {
      setAiError(
        (err as { message?: string })?.message ?? "Failed to save AI settings",
      );
    } finally {
      setAiSaving(false);
    }
  };

  // ── Cleanup handlers ────────────────────────────────────────
  const handleCleanup = async () => {
    setCleanupPending(true);
    setCleanupError(null);
    setCleanupResult(null);
    setConfirmOpen(false);
    try {
      const result = await deleteExpiredSessions();
      setCleanupResult(result);
    } catch (err) {
      setCleanupError(
        (err as { message?: string })?.message ?? "Cleanup failed",
      );
    } finally {
      setCleanupPending(false);
    }
  };

  const hasChanges =
    provider !== aiSettings?.provider ||
    (provider === "openrouter" && model !== aiSettings?.openrouter_model) ||
    (provider === "ollama" &&
      (model !== aiSettings?.ollama_model ||
        baseUrl !== aiSettings?.ollama_base_url)) ||
    apiKeyInput.length > 0;

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure your {APP_NAME} preferences.
        </p>
      </div>

      <Separator />

      {/* ── AI Provider ─────────────────────────────────────── */}
      <section>
        <h2 className="text-base font-semibold">AI Provider</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure the AI provider used for all analysis features.
          Changes take effect immediately — no restart needed.
        </p>

        {aiLoading ? (
          <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading current settings...
          </div>
        ) : (
          <div className="mt-4 space-y-4">
            {/* Provider selector */}
            <div>
              <label className="text-sm font-medium">Provider</label>
              <div className="mt-1 flex gap-2">
                {[
                  { value: "openrouter", label: "OpenRouter" },
                  { value: "ollama", label: "Ollama (Local)" },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => {
                      setProvider(opt.value);
                      setModel(
                        opt.value === "openrouter"
                          ? aiSettings?.openrouter_model || "openai/gpt-4o-mini"
                          : aiSettings?.ollama_model || "qwen3",
                      );
                    }}
                    className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
                      provider === opt.value
                        ? "border-primary bg-primary/5 text-primary"
                        : "border-border hover:border-muted-foreground/30"
                    }`}
                  >
                    <Cpu className="h-4 w-4" />
                    <span className="font-medium">{opt.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Model name */}
            <div>
              <label
                htmlFor="ai-model"
                className="text-sm font-medium"
              >
                Model
              </label>
              <input
                id="ai-model"
                type="text"
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder={
                  provider === "openrouter"
                    ? "openai/gpt-4o-mini"
                    : "qwen3"
                }
                className="mt-1 w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                {provider === "openrouter"
                  ? "Full model path from OpenRouter (e.g. openai/gpt-4o-mini)"
                  : "Local model name from Ollama (e.g. qwen3, llama3)"}
              </p>
            </div>

            {/* API Key (OpenRouter) */}
            {provider === "openrouter" && (
              <div>
                <label
                  htmlFor="ai-api-key"
                  className="text-sm font-medium"
                >
                  API Key
                </label>
                <div className="mt-1 flex items-center gap-2">
                  <div className="relative flex-1">
                    <input
                      id="ai-api-key"
                      type={apiKeyVisible ? "text" : "password"}
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder={
                        aiSettings?.openrouter_api_key
                          ? `${aiSettings.openrouter_api_key}`
                          : "sk-or-..."
                      }
                      className="w-full rounded-lg border bg-background px-3 py-2 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                    <button
                      type="button"
                      onClick={() => setApiKeyVisible(!apiKeyVisible)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {apiKeyVisible ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                {aiSettings?.openrouter_api_key && !apiKeyInput && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Leave blank to keep the current key.
                  </p>
                )}
              </div>
            )}

            {/* Base URL (Ollama) */}
            {provider === "ollama" && (
              <div>
                <label
                  htmlFor="ai-base-url"
                  className="text-sm font-medium"
                >
                  Base URL
                </label>
                <input
                  id="ai-base-url"
                  type="text"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                  className="mt-1 w-full rounded-lg border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <p className="mt-1 text-xs text-muted-foreground">
                  The Ollama server URL (default: http://localhost:11434)
                </p>
              </div>
            )}

            {/* Current key indicator */}
            {aiSettings?.openrouter_api_key && provider === "openrouter" && (
              <p className="text-xs text-muted-foreground">
                Current key: {aiSettings.openrouter_api_key}
              </p>
            )}

            {/* Save button */}
            <div className="flex items-center gap-3">
              <Button
                onClick={handleSaveAi}
                disabled={!hasChanges || aiSaving}
                size="sm"
              >
                {aiSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save"
                )}
              </Button>

              {aiSuccess && (
                <span className="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400">
                  <Check className="h-4 w-4" />
                  Settings saved
                </span>
              )}

              {aiError && (
                <span className="flex items-center gap-1 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4" />
                  {aiError}
                </span>
              )}
            </div>
          </div>
        )}
      </section>

      <Separator />

      {/* Appearance */}
      <section>
        <h2 className="text-base font-semibold">Appearance</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Customize the look and feel of {APP_NAME}.
        </p>

        <div className="mt-4 flex gap-2">
          <Button
            variant={theme === "light" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("light")}
            className="gap-2"
          >
            <Sun className="h-4 w-4" />
            Light
          </Button>
          <Button
            variant={theme === "dark" ? "default" : "outline"}
            size="sm"
            onClick={() => setTheme("dark")}
            className="gap-2"
          >
            <Moon className="h-4 w-4" />
            Dark
          </Button>
        </div>
      </section>

      <Separator />

      {/* Data Retention */}
      <section>
        <h2 className="text-base font-semibold">Data Retention</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Old analysis sessions are automatically eligible for cleanup after the
          configured retention period. Set{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">
            SESSION_RETENTION_DAYS
          </code>{" "}
          in your server environment to change the retention period (default: 90
          days).
        </p>

        <div className="mt-4">
          <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
            <AlertDialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <Trash2 className="h-4 w-4" />
                Clean Up Old Sessions
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Clean up old sessions?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete all analysis sessions older than
                  the configured retention period. This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleCleanup}>
                  Clean Up
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>

          {cleanupPending && (
            <p className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Cleaning up expired sessions...
            </p>
          )}

          {cleanupResult && (
            <p className="mt-2 text-sm text-emerald-600 dark:text-emerald-400">
              {cleanupResult.deleted} expired session
              {cleanupResult.deleted !== 1 ? "s" : ""} deleted (retention:{" "}
              {cleanupResult.retention_days} days)
            </p>
          )}

          {cleanupError && (
            <p className="mt-2 text-sm text-destructive">{cleanupError}</p>
          )}
        </div>
      </section>

      <Separator />

      {/* About */}
      <section>
        <h2 className="text-base font-semibold">About</h2>
        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
          <p>{APP_NAME} v{APP_VERSION}</p>
          <p>AI-Powered Quality Engineering Platform</p>
          <Link
            to="/changelog"
            className="mt-2 inline-flex items-center gap-1 text-primary hover:underline"
          >
            What's New
            <ExternalLink className="h-3 w-3" />
          </Link>
        </div>
      </section>
    </div>
  );
}
