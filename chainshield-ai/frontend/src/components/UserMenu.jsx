export default function UserMenu() {
  return (
    <button className="flex items-center gap-3 px-2 py-1.5 rounded-lg hover:bg-slate-900">
      <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-slate-300">
        IA
      </div>

      <div className="hidden sm:block text-left">
        <p className="text-xs font-medium text-slate-200">
          Investigator
        </p>
        <p className="text-[10px] text-slate-500">
          Analyst
        </p>
      </div>

      <svg
        className="w-3.5 h-3.5 text-slate-500"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="m6 9 6 6 6-6" />
      </svg>
    </button>
  )
}