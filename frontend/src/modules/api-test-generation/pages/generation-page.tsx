/** Main API Test Generation page.

Provides the complete workflow: paste OpenAPI spec, generate tests, view results.
*/

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, History, RefreshCw, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ROUTES } from "@/lib/constants";
import { SpecEditor } from "@/modules/api-test-generation/components/spec-editor";
import { GenerationResults } from "@/modules/api-test-generation/components/generation-results";
import { useGenerateApiTests } from "@/modules/api-test-generation/hooks/use-api-test-generation";

export function ApiTestGenerationPage() {
  const navigate = useNavigate();
  const {
    mutateAsync: generate,
    isPending,
    data: response,
    reset,
  } = useGenerateApiTests();

  const [error, setError] = useState<string | null>(null);
  const [lastSpec, setLastSpec] = useState("");
  const [lastFormat, setLastFormat] = useState<"yaml" | "json">("yaml");

  const handleSubmit = async (spec: string, specFormat: "yaml" | "json") => {
    setError(null);
    setLastSpec(spec);
    setLastFormat(specFormat);
    try {
      await generate({
        spec,
        spec_format: specFormat,
        title: "API Test Suite",
      });
    } catch (err) {
      const message =
        err && typeof err === "object" && "message" in err
          ? (err as { message: string }).message
          : "An unexpected error occurred during generation.";
      setError(message);
    }
  };

  const handleRetry = async () => {
    if (lastSpec) {
      await handleSubmit(lastSpec, lastFormat);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate(ROUTES.HOME)}
              className="shrink-0"
            >
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold tracking-tight">
              API Test Generation
            </h1>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(ROUTES.API_TEST_SESSIONS)}
              className="ml-auto gap-1.5 text-xs text-muted-foreground"
            >
              <History className="h-3.5 w-3.5" />
              History
            </Button>
          </div>
          <p className="mt-1 ml-10 text-sm text-muted-foreground">
            Paste an OpenAPI 3.x spec (YAML or JSON) to generate
            production-ready PyTest test suites with AI.
          </p>
        </div>
      </div>

      {/* Main content */}
      {!response ? (
        <div className="space-y-6">
          <SpecEditor
            onSubmit={handleSubmit}
            isSubmitting={isPending}
            error={null}
          />

          {/* Error message with retry */}
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/5 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">
                    Generation Failed
                  </p>
                  <p className="mt-0.5 text-sm text-destructive/80">
                    {error}
                  </p>
                </div>
              </div>
              <div className="mt-3 flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRetry}
                  disabled={isPending || !lastSpec}
                >
                  <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                  Retry
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setError(null)}
                >
                  Dismiss
                </Button>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-6">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={reset}>
              New Generation
            </Button>
          </div>
          <GenerationResults result={response} />
        </div>
      )}
    </div>
  );
}
