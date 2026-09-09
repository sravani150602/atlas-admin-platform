import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ShieldCheck,
  Users,
  ListChecks,
  ScrollText,
  SlidersHorizontal,
  ArrowUpRight,
  Search,
  Sparkles,
  LogOut,
  Plus,
  ChevronRight,
  LayoutGrid,
} from "lucide-react";
import {
  Button,
  Badge,
  Field,
  Notice,
  EmptyState,
  Panel,
  ConfirmDialog,
} from "@atlas/ux";
import "@atlas/ux/styles.css";
import "./style.css";
import {
  api,
  setCsrf,
  track,
  type Me,
  type Identity,
  type Proposal,
  type Flags,
  type Audit,
  type Role,
} from "./api";
import { Review } from "./Review";
type Page = "directory" | "review" | "audit" | "flags";
const errorText = (e: unknown) =>
  e instanceof Error ? e.message : "Something went wrong. Please try again.";

function App() {
  const focusReturn = useRef<HTMLElement | null>(null);
  const [me, setMe] = useState<Me | null>(null),
    [initial, setInitial] = useState(true),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [page, setPage] = useState<Page>(
    location.pathname === "/review" ? "review" : "directory",
  );
  const [users, setUsers] = useState<Identity[]>([]),
    [proposals, setProposals] = useState<Proposal[]>([]),
    [flags, setFlags] = useState<Flags | null>(null),
    [audit, setAudit] = useState<Audit[]>([]);
  const [search, setSearch] = useState(""),
    [filter, setFilter] = useState("all"),
    [selected, setSelected] = useState("");
  const [prompt, setPrompt] = useState(""),
    [action, setAction] = useState("suspend"),
    [role, setRole] = useState<Role>("viewer");
  const [confirm, setConfirm] = useState<Proposal | null>(null),
    [creating, setCreating] = useState(false),
    [started, setStarted] = useState(0);
  async function refresh(who: Me) {
    const [u, p, f] = await Promise.all([
      api<Identity[]>("/users"),
      api<Proposal[]>("/proposals"),
      api<Flags>("/flags"),
    ]);
    setUsers(u);
    setProposals(p);
    setFlags(f);
    if (who.role !== "viewer") setAudit(await api<Audit[]>("/audit"));
  }
  useEffect(() => {
    void api<Me>("/me")
      .then(async (who) => {
        setCsrf(who.csrf);
        setMe(who);
        await refresh(who);
      })
      .catch((e) => {
        if (
          !errorText(e).includes("Sign in") &&
          !errorText(e).includes("Session")
        )
          setError(errorText(e));
      })
      .finally(() => setInitial(false));
  }, []);
  async function run(fn: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setBusy(false);
    }
  }
  async function login(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await run(async () => {
      await api("/login", "POST", {
        email: data.get("email"),
        password: data.get("password"),
      });
      const who = await api<Me>("/me");
      setCsrf(who.csrf);
      setMe(who);
      await refresh(who);
    });
  }
  const chosen = users.find((u) => u.id === selected);
  function choose(id: string) {
    setSelected(id);
    const u = users.find((v) => v.id === id);
    setAction(u?.active ? "suspend" : "restore");
    setStarted(performance.now());
    track("task_started", page === "review" ? "review" : "admin");
  }
  async function draft(useAI: boolean) {
    focusReturn.current = document.activeElement as HTMLElement;
    await run(async () => {
      const p = await api<Proposal>(
        useAI ? "/ai/draft" : "/proposals",
        "POST",
        useAI
          ? { target_id: selected, prompt }
          : { target_id: selected, action, role },
      );
      setConfirm(p);
      track("proposal_created", "admin");
      if (me) await refresh(me);
    });
  }
  async function apply() {
    if (!confirm) return;
    await run(async () => {
      await api(`/proposals/${confirm.id}/apply`, "POST", { confirmed: true });
      setConfirm(null);
      setNotice("Access updated. The change is recorded in the audit log.");
      track(
        "task_completed",
        page === "review" ? "review" : "admin",
        started ? performance.now() - started : 0,
      );
      if (me) await refresh(me);
    });
  }
  function navigate(next: Page) {
    setPage(next);
    setError("");
    setNotice("");
  }
  if (initial)
    return (
      <main className="loading" aria-busy="true">
        Opening your workspace…
      </main>
    );
  if (!me)
    return (
      <main className="login">
        <section className="login-story">
          <div className="brand">
            <ShieldCheck size={30} />
            <span>
              atlas<span className="brand-dot">.</span>
            </span>
          </div>
          <span className="eyebrow">IDENTITY, WITH INTENTION</span>
          <h1>
            The right access.
            <br />A clearer workspace.
          </h1>
          <p>
            Review identities, guide access changes, and keep every decision
            accountable.
          </p>
          <div className="login-note">
            <ShieldCheck /> Human review is built into every change.
          </div>
        </section>
        <section className="login-form">
          <Badge>Independent portfolio project</Badge>
          <h2>Welcome to Atlas</h2>
          <p>Sign in to your administration workspace.</p>
          {error && <Notice error>{error}</Notice>}
          <form onSubmit={login}>
            <Field
              label="Email address"
              id="email"
              name="email"
              type="email"
              defaultValue="admin@example.test"
              autoComplete="username"
              required
            />
            <Field
              label="Password"
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
            <Button type="submit" disabled={busy}>
              {busy ? "Signing in…" : "Sign in to workspace"}{" "}
              <ArrowUpRight size={16} />
            </Button>
          </form>
          <small>Use the credentials configured during local setup.</small>
        </section>
      </main>
    );
  const visible = users.filter(
    (u) =>
      (u.name + " " + u.email).toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" || u.role === filter),
  );
  const pages = [
    { id: "directory" as Page, name: "Identity directory", icon: Users },
    { id: "review" as Page, name: "Access review", icon: ListChecks },
    { id: "audit" as Page, name: "Audit activity", icon: ScrollText },
    { id: "flags" as Page, name: "Feature rollout", icon: SlidersHorizontal },
  ];
  const titles = {
    directory: [
      "Identity directory",
      "A clear view of who has access, and what comes next.",
    ],
    review: ["Access review", "Review the impact. Make a deliberate decision."],
    audit: [
      "Audit activity",
      "A traceable record of changes across your workspace.",
    ],
    flags: [
      "Feature rollout",
      "Introduce shared experiences at a controlled pace.",
    ],
  };
  return (
    <>
      <a className="skip" href="#main">
        Skip to main content
      </a>
      <div className="shell">
        <aside className="sidebar">
          <a href="/" className="brand" aria-label="Atlas home">
            <ShieldCheck size={29} />
            <span>
              atlas<span className="brand-dot">.</span>
            </span>
          </a>
          <div className="workspace-label">
            <span className="workspace-icon">SE</span>
            <div>
              Sravani’s workspace<small>Portfolio environment</small>
            </div>
          </div>
          <span className="nav-label">WORKSPACE</span>
          <nav aria-label="Workspace navigation">
            {pages
              .filter((p) => me.role !== "viewer" || p.id === "directory")
              .map(({ id, name, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => navigate(id)}
                  aria-current={page === id ? "page" : undefined}
                >
                  <Icon size={18} />
                  {name}
                  {page === id && <ChevronRight size={15} />}
                </button>
              ))}
          </nav>
          <div className="sidebar-note">
            <ShieldCheck size={20} />
            <strong>Reviewed by you</strong>
            <p>
              AI can draft a change.
              <br />
              You decide what happens.
            </p>
          </div>
          <div className="account">
            <span className="avatar">{me.name.slice(0, 1)}</span>
            <div>
              <strong>{me.name}</strong>
              <small>{me.role}</small>
            </div>
            <button
              aria-label="Sign out"
              title="Sign out"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await api("/logout", "POST");
                  setCsrf("");
                  setMe(null);
                  setUsers([]);
                  setProposals([]);
                  setAudit([]);
                  setSelected("");
                  setConfirm(null);
                })
              }
            >
              <LogOut size={18} />
            </button>
          </div>
        </aside>
        <div className="workspace-main">
          <header className="topbar">
            <span>
              <LayoutGrid size={15} /> Workspace <ChevronRight size={14} />{" "}
              <strong>{titles[page][0]}</strong>
            </span>
            <Badge tone="success">Local workspace</Badge>
          </header>
          <main id="main" tabIndex={-1}>
            <div className="page-heading">
              <div>
                <span className="eyebrow">ACCESS MANAGEMENT</span>
                <h1>{titles[page][0]}</h1>
                <p>{titles[page][1]}</p>
              </div>
              {page === "directory" && me.role === "admin" && (
                <Button onClick={() => setCreating((v) => !v)}>
                  <Plus size={17} /> Add identity
                </Button>
              )}
            </div>
            {error && <Notice error>{error}</Notice>}
            {notice && <Notice>{notice}</Notice>}
            {creating && page === "directory" && (
              <Panel title="Add a managed identity">
                <form
                  className="create-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const data = new FormData(e.currentTarget);
                    void run(async () => {
                      await api("/users", "POST", {
                        name: data.get("name"),
                        email: data.get("email"),
                        role: data.get("role"),
                      });
                      setCreating(false);
                      setNotice(
                        "Identity added. This creates a managed record, not a sign-in account.",
                      );
                      await refresh(me);
                    });
                  }}
                >
                  <Field
                    id="new-name"
                    label="Full name"
                    name="name"
                    required
                    maxLength={80}
                  />
                  <Field
                    id="new-email"
                    label="Email"
                    name="email"
                    type="email"
                    required
                  />
                  <div className="field">
                    <label htmlFor="new-role">Role</label>
                    <select id="new-role" name="role">
                      <option>viewer</option>
                      <option>operator</option>
                      <option>admin</option>
                    </select>
                  </div>
                  <Button type="submit" disabled={busy}>
                    Create identity
                  </Button>
                  <Button
                    variant="secondary"
                    onClick={() => setCreating(false)}
                  >
                    Cancel
                  </Button>
                </form>
              </Panel>
            )}
            {page === "directory" && (
              <>
                <div className="stats">
                  <div>
                    <span>Total identities</span>
                    <strong>{users.length.toString().padStart(2, "0")}</strong>
                    <small>Across your workspace</small>
                  </div>
                  <div>
                    <span>Active access</span>
                    <strong>
                      {users
                        .filter((u) => u.active)
                        .length.toString()
                        .padStart(2, "0")}
                    </strong>
                    <small>
                      <span className="status-dot" /> Enabled identities
                    </small>
                  </div>
                  <div>
                    <span>Privileged roles</span>
                    <strong>
                      {users
                        .filter((u) => u.role !== "viewer")
                        .length.toString()
                        .padStart(2, "0")}
                    </strong>
                    <small>Operators & administrators</small>
                  </div>
                  <div>
                    <span>Awaiting your review</span>
                    <strong>
                      {proposals
                        .filter(
                          (p) =>
                            p.status === "pending" &&
                            p.expires * 1000 > Date.now(),
                        )
                        .length.toString()
                        .padStart(2, "0")}
                    </strong>
                    <small>Time-limited proposals</small>
                  </div>
                </div>
                <div className="directory-layout">
                  <Panel
                    title="People & permissions"
                    aside={<Badge>{visible.length} identities</Badge>}
                  >
                    <div className="table-toolbar">
                      <div className="search">
                        <Search size={16} />
                        <input
                          aria-label="Search identities"
                          placeholder="Search by name or email"
                          value={search}
                          onChange={(e) => setSearch(e.target.value)}
                        />
                      </div>
                      <select
                        aria-label="Filter by role"
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                      >
                        <option value="all">All roles</option>
                        <option value="viewer">Viewers</option>
                        <option value="operator">Operators</option>
                        <option value="admin">Administrators</option>
                      </select>
                    </div>
                    <div className="table-scroll">
                      <table
                        className={
                          flags?.effective.compact_rows ? "compact" : ""
                        }
                      >
                        <caption className="sr-only">
                          Managed identities, roles and current access status
                        </caption>
                        <thead>
                          <tr>
                            <th scope="col">Identity</th>
                            <th scope="col">Role</th>
                            <th scope="col">Status</th>
                            <th scope="col">
                              <span className="sr-only">Actions</span>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {visible.map((u) => (
                            <tr
                              key={u.id}
                              className={selected === u.id ? "selected" : ""}
                            >
                              <td>
                                <div className="identity">
                                  <span className="avatar">
                                    {u.name
                                      .split(" ")
                                      .slice(0, 2)
                                      .map((s) => s[0])
                                      .join("")}
                                  </span>
                                  <div>
                                    <strong>{u.name}</strong>
                                    <small>{u.email}</small>
                                  </div>
                                </div>
                              </td>
                              <td>
                                <Badge>{u.role}</Badge>
                              </td>
                              <td>
                                <span
                                  className={`status-dot ${u.active ? "" : "inactive"}`}
                                />
                                {u.active ? "Active" : "Suspended"}
                              </td>
                              <td>
                                <button
                                  className="text-button"
                                  disabled={busy}
                                  onClick={() => choose(u.id)}
                                  aria-label={`Manage ${u.name}`}
                                >
                                  Manage <ChevronRight size={15} />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {visible.length === 0 && (
                        <EmptyState title="No identities found">
                          Try a different name, email, or role filter.
                        </EmptyState>
                      )}
                    </div>
                    <div className="table-foot">
                      Changes are recorded in your workspace audit log.
                    </div>
                  </Panel>
                  <section
                    className="assistant-panel"
                    aria-label="Access change assistant"
                  >
                    <div className="assistant-title">
                      <span>
                        <Sparkles size={19} />
                      </span>
                      <Badge>
                        {flags?.ai_provider === "azure"
                          ? "Azure AI"
                          : "Demo assistant"}
                      </Badge>
                    </div>
                    <h2>
                      A little help.
                      <br />A thoughtful change.
                    </h2>
                    <p>
                      Select an identity, describe the change, and review the
                      proposal before applying it.
                    </p>
                    {chosen ? (
                      <>
                        <div className="selected-person">
                          <small>SELECTED IDENTITY</small>
                          <strong>{chosen.name}</strong>
                          <span>{chosen.email}</span>
                        </div>
                        {me.role === "viewer" ? (
                          <Notice>
                            Your viewer role can inspect identities. Changes
                            require an operator or administrator.
                          </Notice>
                        ) : (
                          <>
                            <label htmlFor="action">Manual change</label>
                            <select
                              id="action"
                              value={action}
                              onChange={(e) => setAction(e.target.value)}
                            >
                              <option value="suspend">Suspend access</option>
                              <option value="restore">Restore access</option>
                              <option value="change_role">Change role</option>
                            </select>
                            {action === "change_role" && (
                              <>
                                <label htmlFor="role">New role</label>
                                <select
                                  id="role"
                                  value={role}
                                  onChange={(e) =>
                                    setRole(e.target.value as Role)
                                  }
                                >
                                  <option>viewer</option>
                                  <option>operator</option>
                                  <option>admin</option>
                                </select>
                              </>
                            )}
                            <Button
                              variant="secondary"
                              disabled={busy}
                              onClick={() => void draft(false)}
                            >
                              Preview manual change
                            </Button>
                            {flags?.effective.ai_assistant && (
                              <>
                                <div className="divider">OR DESCRIBE IT</div>
                                <label htmlFor="prompt">
                                  Requested access change
                                </label>
                                <textarea
                                  id="prompt"
                                  value={prompt}
                                  maxLength={1000}
                                  onChange={(e) => setPrompt(e.target.value)}
                                  placeholder="e.g. Change role to viewer"
                                />
                                <small>
                                  Do not include sensitive information. Azure
                                  mode sends this text to your configured model.
                                </small>
                                <Button
                                  disabled={busy || prompt.trim().length < 3}
                                  onClick={() => void draft(true)}
                                >
                                  <Sparkles size={16} /> Draft a proposal
                                </Button>
                              </>
                            )}
                          </>
                        )}
                      </>
                    ) : (
                      <div className="assistant-empty">
                        <Users size={25} />
                        <strong>Start with an identity</strong>
                        <small>Choose “Manage” in the directory.</small>
                      </div>
                    )}
                    <div className="assistant-footer">
                      <ShieldCheck size={15} /> Nothing changes until you
                      confirm.
                    </div>
                  </section>
                </div>
              </>
            )}
            {page === "review" && (
              <Review
                proposals={proposals}
                users={users}
                busy={busy}
                onReview={(p) => {
                  focusReturn.current = document.activeElement as HTMLElement;
                  setConfirm(p);
                  setStarted(performance.now());
                  track("task_started", "review");
                }}
                onCancel={(p) =>
                  void run(async () => {
                    await api(`/proposals/${p.id}/cancel`, "POST");
                    await refresh(me);
                    setNotice("Proposal cancelled.");
                  })
                }
              />
            )}
            {page === "audit" && (
              <Panel
                title="Recent activity"
                aside={<Badge>Latest 200 events</Badge>}
              >
                <div className="table-scroll">
                  <table>
                    <caption className="sr-only">Workspace audit log</caption>
                    <thead>
                      <tr>
                        <th scope="col">Time</th>
                        <th scope="col">Action</th>
                        <th scope="col">Actor</th>
                        <th scope="col">Target</th>
                        <th scope="col">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {audit.map((a) => (
                        <tr key={a.id}>
                          <td>
                            {new Date(a.timestamp * 1000).toLocaleString()}
                          </td>
                          <td>{a.action}</td>
                          <td>
                            {users.find((u) => u.id === a.actor_id)?.name ??
                              a.actor_id}
                          </td>
                          <td>
                            {users.find((u) => u.id === a.target_id)?.name ??
                              a.target_id}
                          </td>
                          <td>
                            <details>
                              <summary>View change</summary>
                              <pre>
                                {JSON.stringify(JSON.parse(a.details), null, 2)}
                              </pre>
                            </details>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Panel>
            )}
            {page === "flags" && (
              <Panel title="Shared experience controls">
                <div className="flag-intro">
                  Cohorts are stable per identity and feature. Setting a rollout
                  to 0% also prevents existing AI proposals from being applied.
                </div>
                {flags?.flags.map((f) => (
                  <form
                    key={`${f.name}-${f.version}`}
                    className="flag-row"
                    onSubmit={(e) => {
                      e.preventDefault();
                      const form = new FormData(e.currentTarget);
                      void run(async () => {
                        await api(`/flags/${f.name}`, "PUT", {
                          percent: Number(form.get("percent")),
                          version: f.version,
                        });
                        await refresh(me);
                        setNotice("Rollout updated.");
                      });
                    }}
                  >
                    <div>
                      <h3>
                        {f.name === "ai_assistant"
                          ? "AI-assisted proposals"
                          : "Compact directory rows"}
                      </h3>
                      <p>
                        {f.name === "ai_assistant"
                          ? "Enable natural-language drafts with human confirmation."
                          : "Use a denser table across the shared directory experience."}
                      </p>
                      <Badge
                        tone={flags.effective[f.name] ? "success" : "neutral"}
                      >
                        Your cohort:{" "}
                        {flags.effective[f.name] ? "enabled" : "disabled"}
                      </Badge>
                    </div>
                    <div className="rollout-control">
                      <label htmlFor={`flag-${f.name}`}>
                        Rollout percentage
                      </label>
                      <input
                        id={`flag-${f.name}`}
                        name="percent"
                        type="number"
                        min="0"
                        max="100"
                        defaultValue={f.percent}
                        required
                        disabled={me.role !== "admin" || busy}
                      />
                      <Button
                        type="submit"
                        disabled={me.role !== "admin" || busy}
                      >
                        Save rollout
                      </Button>
                    </div>
                  </form>
                ))}
              </Panel>
            )}
            <footer>
              Atlas · Shared UX platform{" "}
              <span>Built for deliberate access decisions.</span>
            </footer>
          </main>
        </div>
      </div>
      <ConfirmDialog
        returnFocus={focusReturn.current}
        open={!!confirm}
        title="Review this access change"
        busy={busy}
        onCancel={() => setConfirm(null)}
        onConfirm={() => void apply()}
      >
        {confirm && (
          <>
            <p>
              You are changing access for{" "}
              <strong>
                {users.find((u) => u.id === confirm.target_id)?.name ??
                  confirm.target_id}
              </strong>
              .
            </p>
            <dl className="change-details">
              <div>
                <dt>Action</dt>
                <dd>{confirm.action.replaceAll("_", " ")}</dd>
              </div>
              {confirm.action === "change_role" && (
                <div>
                  <dt>New role</dt>
                  <dd>{confirm.role}</dd>
                </div>
              )}
              <div>
                <dt>Risk</dt>
                <dd>
                  {confirm.risk === 2
                    ? "High — privileged access"
                    : "Medium — access change"}
                </dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{confirm.provider}</dd>
              </div>
            </dl>
            <p>{confirm.reason}</p>
            <small>
              Expires {new Date(confirm.expires * 1000).toLocaleTimeString()}.
              Current permissions and identity version will be checked again.
            </small>
            {error && <Notice error>{error}</Notice>}
          </>
        )}
      </ConfirmDialog>
    </>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
