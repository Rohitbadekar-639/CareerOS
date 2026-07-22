import Link from "next/link";

const links = [
  { href: "/app", label: "Feed" },
  { href: "/app/search", label: "Search" },
  { href: "/app/tracker", label: "Tracker" },
  { href: "/app/notifications", label: "Alerts" },
  { href: "/app/profile", label: "Profile" },
] as const;

export function AppNav({ email }: { email?: string | null }) {
  return (
    <header className="border-b border-neutral-200">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-6">
          <Link href="/app" className="text-lg font-semibold tracking-tight">
            CareerOS
          </Link>
          <nav className="flex gap-4 text-sm">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-neutral-600 underline-offset-4 hover:text-neutral-900 hover:underline"
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {email ? <span className="hidden text-neutral-500 sm:inline">{email}</span> : null}
          <form action="/auth/logout" method="post">
            <button className="rounded border border-neutral-300 px-3 py-1.5" type="submit">
              Sign out
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}
