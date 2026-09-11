// The page everyone sees while the plan is being updated. Deliberately plain: what is
// happening, that nothing is broken, and that it will be back. Two drops fall on
// staggered timings so the mark never looks empty, and the bottle's oil level breathes.
export const metadata = {
  title: "Back shortly — JIVO Mark 2",
  description: "The September plan is being updated. Back shortly.",
};

export default function Maintenance() {
  return (
    <div className="fixed inset-0 z-50 bg-[#09090b] flex items-center justify-center px-5">
      <div className="text-center max-w-lg">
        <svg viewBox="0 0 160 190" className="mx-auto w-40 h-48" role="img" aria-label="Oil filling a bottle">
          <defs>
            <linearGradient id="jm-oil" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#fcd34d" />
              <stop offset="100%" stopColor="#f59e0b" />
            </linearGradient>
            <clipPath id="jm-bottle">
              <path d="M58 74 h44 v14 l12 18 v68 a8 8 0 0 1 -8 8 h-52 a8 8 0 0 1 -8 -8 v-68 l12 -18 z" />
            </clipPath>
          </defs>

          {/* two drops, offset in time, so a still frame always catches one */}
          <g className="jm-drop jm-drop-a">
            <path d="M80 6 L92 28 A14 14 0 1 1 68 28 Z" fill="url(#jm-oil)" />
          </g>
          <g className="jm-drop jm-drop-b">
            <path d="M80 6 L92 28 A14 14 0 1 1 68 28 Z" fill="url(#jm-oil)" opacity="0.55" />
          </g>

          {/* the oil already in the bottle */}
          <g clipPath="url(#jm-bottle)">
            <g className="jm-level">
              <rect x="40" y="120" width="80" height="120" fill="url(#jm-oil)" />
              {/* a soft surface on top of the oil */}
              <ellipse cx="80" cy="120" rx="42" ry="5" fill="#fde68a" opacity="0.55" />
            </g>
          </g>

          {/* bottle outline and neck, drawn over the oil */}
          <path d="M58 74 h44 v14 l12 18 v68 a8 8 0 0 1 -8 8 h-52 a8 8 0 0 1 -8 -8 v-68 l12 -18 z"
                fill="none" stroke="#52525b" strokeWidth="3.5" strokeLinejoin="round" />
          <rect x="66" y="62" width="28" height="12" rx="3" fill="none" stroke="#52525b" strokeWidth="3.5" />
        </svg>

        <h1 className="mt-7 text-2xl font-semibold text-zinc-100">We are updating this page</h1>
        <p className="mt-3 text-zinc-400 leading-relaxed">
          The September plan is being worked on right now. Nothing is broken and nothing is lost — the plan
          is safe. This page will come back on its own.
        </p>
        <p className="mt-2 text-zinc-500 text-sm">Thoda intezaar — page thodi der mein wapas aa jayega.</p>

        <div className="mt-7 flex items-center justify-center gap-2" aria-hidden="true">
          <span className="jm-dot jm-dot-1 h-1.5 w-1.5 rounded-full bg-amber-400/80" />
          <span className="jm-dot jm-dot-2 h-1.5 w-1.5 rounded-full bg-amber-400/80" />
          <span className="jm-dot jm-dot-3 h-1.5 w-1.5 rounded-full bg-amber-400/80" />
        </div>

        <p className="mt-7 text-xs text-zinc-600">JIVO Oil · September 2026 plan</p>
      </div>
    </div>
  );
}
