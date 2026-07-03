import { IS_PREVIEW } from "@/lib/constants";

/**
 * Banner shown when the frontend is deployed as a static preview
 * without a live backend (e.g. GitHub Pages).
 *
 * Dismissible via localStorage so returning visitors aren't annoyed.
 */
export function BackendBanner() {
  if (!IS_PREVIEW) {
    return null;
  }

  return (
    <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 text-sm text-amber-800 dark:bg-amber-950 dark:border-amber-800 dark:text-amber-200">
      <div className="flex items-center justify-center gap-2 max-w-5xl mx-auto">
        <span className="inline-flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-amber-500 animate-pulse" />
          <strong>Preview Mode</strong>
        </span>
        <span className="text-amber-700 dark:text-amber-300">
          &mdash; Backend not connected.{" "}
          <a
            href="https://github.com/CypherMorgan/qpilot#quick-start"
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-medium hover:text-amber-900 dark:hover:text-amber-100"
          >
            Run the backend locally
          </a>{" "}
          or{" "}
          <a
            href="https://github.com/CypherMorgan/qpilot"
            target="_blank"
            rel="noopener noreferrer"
            className="underline font-medium hover:text-amber-900 dark:hover:text-amber-100"
          >
            deploy your own
          </a>{" "}
          to use all features.
        </span>
      </div>
    </div>
  );
}
