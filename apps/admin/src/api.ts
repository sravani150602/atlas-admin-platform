export type Role = "admin" | "operator" | "viewer";
export type Identity = {
  id: string;
  name: string;
  email: string;
  role: Role;
  active: number;
  version: number;
};
export type Me = Identity & { csrf: string };
export type Proposal = {
  id: string;
  target_id: string;
  action: string;
  role: Role;
  reason: string;
  provider: string;
  risk: number;
  status: string;
  created: number;
  expires: number;
};
export type Flags = {
  flags: { name: string; percent: number; version: number }[];
  effective: Record<string, boolean>;
  ai_provider: string;
};
export type Audit = {
  id: number;
  timestamp: number;
  actor_id: string;
  action: string;
  target_id: string;
  details: string;
};
let csrf = "";
export function setCsrf(value: string) {
  csrf = value;
}
export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check the form values and try again.",
    );
  return data as T;
}
export function track(name: string, surface: string, duration_ms = 0) {
  void api("/events", "POST", {
    name,
    surface,
    duration_ms: Math.min(3600000, Math.max(0, Math.round(duration_ms))),
  }).catch(() => {});
}
