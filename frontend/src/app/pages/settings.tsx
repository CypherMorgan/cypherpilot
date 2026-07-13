import { Moon, Sun } from "lucide-react";

import { useTheme } from "@/hooks/use-theme";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { APP_NAME, APP_VERSION } from "@/lib/constants";

export function SettingsPage() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="mx-auto max-w-2xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure your QPilot preferences.
        </p>
      </div>

      <Separator />

      {/* Appearance */}
      <section>
        <h2 className="text-base font-semibold">Appearance</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Customize the look and feel of QPilot.
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

      {/* About */}
      <section>
        <h2 className="text-base font-semibold">About</h2>
        <div className="mt-2 space-y-1 text-sm text-muted-foreground">
          <p>{APP_NAME} v{APP_VERSION}</p>
          <p>AI-Powered Quality Engineering Platform</p>
        </div>
      </section>
    </div>
  );
}
