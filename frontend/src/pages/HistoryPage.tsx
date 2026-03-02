import AppShell from '../components/layout/AppShell'

export default function HistoryPage() {
  return (
    <AppShell activeTab="history">
      <div className="flex-1 flex flex-col items-center justify-center gap-4 px-6">
        <span className="material-symbols-outlined text-[56px] text-text-sub/40" style={{ fontVariationSettings: "'FILL' 0, 'wght' 200" }}>history</span>
        <div className="text-center">
          <h2 className="text-[18px] font-bold text-text-main">Consultation History</h2>
          <p className="text-[14px] text-text-sub mt-1.5">Past consultations will appear here.</p>
        </div>
      </div>
    </AppShell>
  )
}
