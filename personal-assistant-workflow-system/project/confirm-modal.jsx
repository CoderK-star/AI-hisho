// confirm-modal.jsx — S08 Confirmation dialog (Human-in-the-loop)
//
// Usage:
//   const confirm = useConfirm();
//   confirm.open({
//     title: "確認",
//     description: "以下のメールを送信します。",
//     details: [{ label: "宛先", value: "example@email.com" }, ...],
//     warning: "この操作は取り消せません。",
//     actionLabel: "送信する",
//     destructive: false,   // true → red button + "削除する" semantics
//     onConfirm: () => { ... },
//   });
//
// Render <ConfirmModal {...confirm.props} /> once at the app root.

function useConfirm() {
  const [state, setState] = React.useState({ open: false, payload: null });
  const open = React.useCallback((payload) => {
    setState({ open: true, payload });
  }, []);
  const close = React.useCallback(() => {
    setState((s) => ({ ...s, open: false }));
  }, []);
  return {
    open,
    close,
    props: { state, close },
  };
}

function ConfirmModal({ state, close }) {
  const { open: isOpen, payload } = state;
  const cancelRef = React.useRef(null);

  React.useEffect(() => {
    if (!isOpen) return;
    // focus default (cancel) on open
    const t = setTimeout(() => cancelRef.current?.focus(), 30);
    const onKey = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      clearTimeout(t);
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen, close]);

  if (!isOpen || !payload) return null;

  const {
    title = "確認",
    description,
    details,
    warning,
    actionLabel = "実行する",
    destructive = false,
    onConfirm,
  } = payload;

  const handleConfirm = () => {
    if (typeof onConfirm === "function") onConfirm();
    close();
  };

  return (
    <div
      className="modal-root"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onMouseDown={(e) => { if (e.target === e.currentTarget) close(); }}
    >
      <div className="modal-overlay" />
      <div className="modal">
        <header className="modal-head">
          <div className={`modal-icon${destructive ? " is-danger" : ""}`}>
            {destructive ? (
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 1.5 14.5 13H1.5L8 1.5Z" />
                <path d="M8 6.5v3.5" />
                <circle cx="8" cy="11.7" r=".5" fill="currentColor" />
              </svg>
            ) : (
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="8" cy="8" r="6" />
                <path d="M8 5v3.5M8 11h.01" />
              </svg>
            )}
          </div>
          <div className="modal-head-text">
            <h2 className="modal-title">{title}</h2>
            {description && <p className="modal-desc">{description}</p>}
          </div>
        </header>

        {details && details.length > 0 && (
          <div className="modal-details">
            {details.map((d, i) => (
              <div className="modal-row" key={i}>
                <div className="modal-row-label">{d.label}</div>
                <div className={`modal-row-value${d.mono ? " is-mono" : ""}`}>{d.value}</div>
              </div>
            ))}
          </div>
        )}

        {warning && (
          <div className={`modal-warning${destructive ? " is-danger" : ""}`}>
            <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="8" cy="8" r="6" />
              <path d="M8 5v3.5M8 11h.01" />
            </svg>
            <span>{warning}</span>
          </div>
        )}

        <footer className="modal-foot">
          <div className="modal-foot-hint">
            <span className="kbd">Esc</span>
            <span>でキャンセル</span>
          </div>
          <div className="modal-foot-actions">
            <button ref={cancelRef} type="button" className="btn btn-ghost btn-md" onClick={close}>
              キャンセル
            </button>
            <button
              type="button"
              className={`btn btn-md ${destructive ? "btn-danger" : "btn-primary"}`}
              onClick={handleConfirm}
            >
              {actionLabel}
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}

Object.assign(window, { useConfirm, ConfirmModal });
