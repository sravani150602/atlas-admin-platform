import { Button, Badge, EmptyState, Panel } from "@atlas/ux";
import type { Identity, Proposal } from "./api";
export function Review({
  proposals,
  users,
  onReview,
  onCancel,
  busy,
}: {
  proposals: Proposal[];
  users: Identity[];
  onReview: (p: Proposal) => void;
  onCancel: (p: Proposal) => void;
  busy: boolean;
}) {
  return (
    <Panel
      title="Your change proposals"
      aside={
        <Badge>
          {
            proposals.filter(
              (p) => p.status === "pending" && p.expires * 1000 > Date.now(),
            ).length
          }{" "}
          awaiting review
        </Badge>
      }
    >
      {proposals.length === 0 ? (
        <EmptyState title="A clear review queue">
          Draft a manual or AI-assisted change from the identity directory.
          Every change comes here for your review.
        </EmptyState>
      ) : (
        <div className="proposal-list">
          {proposals.map((p) => {
            const expired =
              p.expires * 1000 <= Date.now() && p.status === "pending";
            const target = users.find((u) => u.id === p.target_id);
            return (
              <article className="proposal" key={p.id}>
                <div>
                  <div className="inline">
                    <strong>{target?.name ?? p.target_id}</strong>
                    <Badge
                      tone={p.status === "applied" ? "success" : "neutral"}
                    >
                      {expired ? "expired" : p.status}
                    </Badge>
                  </div>
                  <p>
                    {p.action.replaceAll("_", " ")}
                    {p.action === "change_role" ? ` → ${p.role}` : ""}
                  </p>
                  <small>
                    {p.reason}
                    <br />
                    Source: {p.provider} ·{" "}
                    {new Date(p.created * 1000).toLocaleString()}
                  </small>
                </div>
                {p.status === "pending" && !expired && (
                  <div className="row-actions">
                    <Button
                      disabled={busy}
                      variant="secondary"
                      onClick={() => onCancel(p)}
                    >
                      Cancel
                    </Button>
                    <Button disabled={busy} onClick={() => onReview(p)}>
                      Review change
                    </Button>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      )}
    </Panel>
  );
}
