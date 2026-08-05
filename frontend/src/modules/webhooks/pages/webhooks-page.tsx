/**
 * WebhooksPage — manage outgoing webhook endpoints.
 *
 * Lists the current user's webhooks with their latest delivery outcome,
 * and provides create / update (activate-deactivate) / test-ping / delete.
 */

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  CheckCircle2,
  Copy,
  Pause,
  Play,
  Plus,
  Send,
  Trash2,
  Webhook as WebhookIcon,
  XCircle,
} from "lucide-react";

import * as webhooksService from "@/modules/webhooks/services";
import {
  WEBHOOK_EVENTS,
  type Webhook,
  type WebhookEvent,
} from "@/modules/webhooks/services";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";

function StatusBadge({ status }: { status: string }) {
  const styles =
    status === "delivered"
      ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
      : status === "failed"
        ? "bg-red-500/15 text-red-600 dark:text-red-400"
        : "bg-amber-500/15 text-amber-600 dark:text-amber-400";
  const Icon =
    status === "delivered"
      ? CheckCircle2
      : status === "failed"
        ? XCircle
        : Activity;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        styles,
      )}
    >
      <Icon className="h-3 w-3" />
      {status}
    </span>
  );
}

function CreateWebhookDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [events, setEvents] = useState<WebhookEvent[]>(["analysis.completed"]);

  const createMutation = useMutation({
    mutationFn: () =>
      webhooksService.createWebhook({
        name: name.trim(),
        url: url.trim(),
        events,
      }),
    onSuccess: () => {
      onCreated();
      setOpen(false);
      setName("");
      setUrl("");
      setEvents(["analysis.completed"]);
    },
  });

  const toggleEvent = (event: WebhookEvent) => {
    setEvents((prev) =>
      prev.includes(event)
        ? prev.filter((e) => e !== event)
        : [...prev, event],
    );
  };

  const valid =
    name.trim().length > 0 &&
    url.trim().startsWith("http") &&
    events.length > 0;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Add Webhook
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Webhook</DialogTitle>
          <DialogDescription>
            Deliver analysis events to your endpoint as signed HTTP callbacks.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="wh-name">Name</Label>
            <Input
              id="wh-name"
              placeholder="CI Notifier"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="wh-url">Endpoint URL</Label>
            <Input
              id="wh-url"
              placeholder="https://example.com/hooks/cypherpilot"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Events</Label>
            <div className="flex flex-col gap-2">
              {WEBHOOK_EVENTS.map((event) => (
                <label
                  key={event}
                  className="flex cursor-pointer items-center gap-2 rounded-md border p-2 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={events.includes(event)}
                    onChange={() => toggleEvent(event)}
                    className="h-4 w-4"
                  />
                  <code className="text-xs">{event}</code>
                </label>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button
            onClick={() => createMutation.mutate()}
            disabled={!valid || createMutation.isPending}
          >
            {createMutation.isPending ? "Creating..." : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function TestPingButton({ webhook }: { webhook: Webhook }) {
  const queryClient = useQueryClient();
  const [result, setResult] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => webhooksService.testWebhook(webhook.id),
    onSuccess: (outcome) => {
      setResult(outcome.status);
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
    onError: (error: unknown) => {
      setResult(
        error instanceof Error ? error.message : "Test ping failed",
      );
    },
  });

  return (
    <Button
      variant="outline"
      size="sm"
      disabled={!webhook.is_active || mutation.isPending}
      onClick={() => mutation.mutate()}
      title="Send a test.ping event"
    >
      <Send className="mr-2 h-4 w-4" />
      {mutation.isPending ? "Pinging..." : "Test"}
      {result && (
        <span
          className={cn(
            "ml-2 text-xs",
            result === "delivered"
              ? "text-emerald-600 dark:text-emerald-400"
              : "text-red-600 dark:text-red-400",
          )}
        >
          {result}
        </span>
      )}
    </Button>
  );
}

export function WebhooksPage() {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState<string | null>(null);

  const { data: webhooks = [], isLoading } = useQuery({
    queryKey: ["webhooks"],
    queryFn: webhooksService.listWebhooks,
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      webhooksService.updateWebhook(id, { is_active: isActive }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => webhooksService.deleteWebhook(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });

  const copySecret = (id: string, secret: string) => {
    void navigator.clipboard?.writeText(secret);
    setCopied(id);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Webhooks</h1>
          <p className="text-sm text-muted-foreground">
            Receive signed callbacks when analysis sessions complete or fail.
          </p>
        </div>
        <CreateWebhookDialog
          onCreated={() => queryClient.invalidateQueries({ queryKey: ["webhooks"] })}
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : webhooks.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <WebhookIcon className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium">No webhooks yet</p>
            <p className="text-sm text-muted-foreground">
              Add an endpoint to start receiving analysis events.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {webhooks.map((webhook) => (
            <Card key={webhook.id} className={cn(!webhook.is_active && "opacity-70")}>
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle className="flex items-center gap-2 text-lg">
                      {webhook.name}
                      {webhook.last_delivery ? (
                        <StatusBadge status={webhook.last_delivery.status} />
                      ) : (
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                          never fired
                        </span>
                      )}
                      {!webhook.is_active && (
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
                          paused
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      <code className="text-xs">{webhook.url}</code>
                    </CardDescription>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <TestPingButton webhook={webhook} />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        toggleMutation.mutate({
                          id: webhook.id,
                          isActive: !webhook.is_active,
                        })
                      }
                      title={webhook.is_active ? "Pause webhook" : "Activate webhook"}
                    >
                      {webhook.is_active ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-red-600 hover:bg-red-500/10 dark:text-red-400"
                          title="Delete webhook"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogTitle>Delete webhook?</AlertDialogTitle>
                          <AlertDialogDescription>
                            "{webhook.name}" will stop receiving events. This
                            cannot be undone.
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                          <AlertDialogCancel>Cancel</AlertDialogCancel>
                          <AlertDialogAction
                            className="bg-red-600 text-white hover:bg-red-700"
                            onClick={() => deleteMutation.mutate(webhook.id)}
                          >
                            Delete
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-3 text-sm">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-muted-foreground">Events:</span>
                  {webhook.events.map((event) => (
                    <code
                      key={event}
                      className="rounded bg-muted px-1.5 py-0.5 text-xs"
                    >
                      {event}
                    </code>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-muted-foreground">Secret:</span>
                  <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                    {webhook.secret_masked}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copySecret(webhook.id, webhook.secret_masked)}
                    title="Copy (masked) secret"
                  >
                    <Copy className="mr-1 h-3 w-3" />
                    {copied === webhook.id ? "Copied" : "Copy"}
                  </Button>
                </div>
                {webhook.last_delivery?.last_error && (
                  <p className="text-xs text-muted-foreground">
                    Last error: {webhook.last_delivery.last_error}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
