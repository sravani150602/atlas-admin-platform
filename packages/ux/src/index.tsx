import {
  useEffect,
  useRef,
  type ReactNode,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
} from "react";

export function Button({
  variant = "primary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
}) {
  return <button type="button" className={`button ${variant}`} {...props} />;
}
export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning";
}) {
  return <span className={`badge ${tone}`}>{children}</span>;
}
export function Field({
  label,
  id,
  hint,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  id: string;
  hint?: string;
}) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        aria-describedby={hint ? `${id}-hint` : undefined}
        {...props}
      />
      {hint && <small id={`${id}-hint`}>{hint}</small>}
    </div>
  );
}
export function Notice({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={`notice ${error ? "error" : ""}`}
      role={error ? "alert" : "status"}
    >
      {children}
    </div>
  );
}
export function EmptyState({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Panel({
  title,
  children,
  aside,
}: {
  title: string;
  children: ReactNode;
  aside?: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
        {aside}
      </div>
      {children}
    </section>
  );
}
export function ConfirmDialog({
  open,
  title,
  children,
  busy,
  onCancel,
  onConfirm,
  returnFocus,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  busy: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  returnFocus?: HTMLElement | null;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (!open) {
      if (dialog.open) dialog.close();
      return;
    }
    const previous =
      returnFocus ?? (document.activeElement as HTMLElement | null);
    if (!dialog.open) dialog.showModal();
    return () => {
      if (dialog.open) dialog.close();
      previous?.focus();
    };
  }, [open]);
  useEffect(() => {
    const dialog = ref.current;
    // A draft can open the dialog while its request is still finishing. Move
    // focus to the safe action once disabled controls become available.
    if (
      open &&
      !busy &&
      dialog &&
      (document.activeElement === dialog ||
        !dialog.contains(document.activeElement))
    ) {
      dialog.querySelector<HTMLButtonElement>("button")?.focus();
    }
  }, [open, busy]);
  return (
    <dialog
      ref={ref}
      aria-labelledby="confirm-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onCancel();
      }}
    >
      <h2 id="confirm-title">{title}</h2>
      {children}
      <div className="dialog-actions">
        <Button
          variant="secondary"
          autoFocus
          disabled={busy}
          onClick={onCancel}
        >
          Go back
        </Button>
        <Button disabled={busy} onClick={onConfirm}>
          {busy ? "Applying…" : "Confirm change"}
        </Button>
      </div>
    </dialog>
  );
}
