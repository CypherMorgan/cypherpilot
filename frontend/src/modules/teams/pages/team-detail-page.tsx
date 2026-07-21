/**
 * TeamDetailPage — view team members, invite users, manage roles.
 */

import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Trash2, UserPlus } from "lucide-react";
import * as teamsService from "@/modules/teams/services";
import { useAuth } from "@/hooks/use-auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Avatar,
  AvatarFallback,
} from "@/components/ui/avatar";

function getInitials(name: string | null | undefined, username: string): string {
  if (name) {
    return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
  }
  return username.slice(0, 2).toUpperCase();
}

const ROLES = [
  { value: "admin", label: "Admin" },
  { value: "member", label: "Member" },
  { value: "viewer", label: "Viewer" },
];

export function TeamDetailPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();

  const [inviteOpen, setInviteOpen] = useState(false);
  const [inviteUsername, setInviteUsername] = useState("");
  const [inviteRole, setInviteRole] = useState("member");

  const { data: team, isLoading } = useQuery({
    queryKey: ["team", teamId],
    queryFn: () => teamsService.getTeamDetail(teamId!),
    enabled: !!teamId,
  });

  const inviteMutation = useMutation({
    mutationFn: () =>
      teamsService.inviteMember(teamId!, inviteUsername, inviteRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", teamId] });
      setInviteOpen(false);
      setInviteUsername("");
      setInviteRole("member");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (userId: string) => teamsService.removeMember(teamId!, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", teamId] });
    },
  });

  const roleMutation = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      teamsService.updateMemberRole(teamId!, userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team", teamId] });
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!team) {
    return (
      <div className="mx-auto max-w-4xl p-6">
        <p className="text-muted-foreground">Team not found.</p>
      </div>
    );
  }

  const currentUserMember = team.members.find(
    (m) => m.user_id === currentUser?.id,
  );
  const isAdmin =
    currentUserMember?.role === "owner" ||
    currentUserMember?.role === "admin";

  return (
    <div className="mx-auto max-w-4xl p-6">
      <Button
        variant="ghost"
        onClick={() => navigate("/teams")}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Teams
      </Button>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{team.name}</h1>
          {team.description && (
            <p className="text-sm text-muted-foreground">{team.description}</p>
          )}
        </div>
        {isAdmin && (
          <Dialog open={inviteOpen} onOpenChange={setInviteOpen}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="mr-2 h-4 w-4" />
                Invite Member
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite Member</DialogTitle>
                <DialogDescription>
                  Add a user to this team by their username.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="invite-username">Username</Label>
                  <Input
                    id="invite-username"
                    placeholder="Enter username"
                    value={inviteUsername}
                    onChange={(e) => setInviteUsername(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role</Label>
                  <Select value={inviteRole} onValueChange={setInviteRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLES.map((r) => (
                        <SelectItem key={r.value} value={r.value}>
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button
                  onClick={() => inviteMutation.mutate()}
                  disabled={!inviteUsername.trim() || inviteMutation.isPending}
                >
                  {inviteMutation.isPending ? "Inviting..." : "Invite"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Members ({team.members.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="divide-y">
            {team.members.map((member) => (
              <div
                key={member.user_id}
                className="flex items-center justify-between py-3"
              >
                <div className="flex items-center gap-3">
                  <Avatar className="h-9 w-9">
                    <AvatarFallback className="text-xs">
                      {getInitials(member.display_name, member.username)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="text-sm font-medium">
                      {member.display_name || member.username}
                      {member.user_id === currentUser?.id && (
                        <span className="ml-2 text-xs text-muted-foreground">
                          (you)
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      @{member.username}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isAdmin && member.role !== "owner" ? (
                    <Select
                      value={member.role}
                      onValueChange={(role) =>
                        roleMutation.mutate({
                          userId: member.user_id,
                          role,
                        })
                      }
                    >
                      <SelectTrigger className="w-28">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ROLES.map((r) => (
                          <SelectItem key={r.value} value={r.value}>
                            {r.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium capitalize">
                      {member.role}
                    </span>
                  )}
                  {isAdmin && member.role !== "owner" && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive"
                      onClick={() =>
                        removeMutation.mutate(member.user_id)
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
