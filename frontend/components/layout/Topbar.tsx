interface TopbarProps {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}

export function Topbar({ title, description, actions }: TopbarProps) {
  return (
    <header className="flex items-center justify-between border-b border-line bg-canvas px-4 py-4 md:px-8 md:py-5">
      <div className="min-w-0">
        <h1 className="font-display text-lg text-ink">{title}</h1>
        {description && <p className="mt-0.5 hidden text-sm text-ink-muted sm:block">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  );
}
