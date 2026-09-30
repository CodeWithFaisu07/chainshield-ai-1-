import UserMenu from './UserMenu.jsx'

export default function Header() {
  return (
    <header className="h-16 shrink-0 bg-slate-950/95 border-b border-slate-800 flex items-center justify-between px-5">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-full max-w-md">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m16.5 16.5 4 4" />
          </svg>

          <input
            type="text"
            placeholder="Search transactions, wallets, IP addresses..."
            className="w-full h-9 bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 text-xs text-slate-200 placeholder:text-slate-600 focus:outline-none focus:border-sky-500/50"
          />
        </div>
      </div>

      <div className="flex items-center gap-4 ml-4">
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-900">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-[11px] text-slate-400">
            Local Dataset
          </span>
        </div>

        <button
          className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-900 flex items-center justify-center"
          aria-label="Notifications"
        >
          <svg
            className="w-4 h-4"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
            <path d="M10 21h4" />
          </svg>
        </button>

        <UserMenu />
      </div>
    </header>
  )
}