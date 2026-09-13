import { Link } from 'react-router-dom'
import { ShieldCheck, ArrowLeft } from 'lucide-react'

export const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-blue-400" />
            <span className="text-lg font-bold text-white">Anomix Privacy Policy</span>
          </div>
          <Link to="/" className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-8 shadow-md space-y-6 text-slate-300 text-sm leading-relaxed">
          <h1 className="text-2xl font-bold text-white border-b border-slate-800 pb-4">Privacy Policy</h1>
          
          <p>Last updated: September 13, 2026</p>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">1. Telemetry & Data Collection</h2>
            <p>Anomix collects system performance metrics (including CPU usage, memory utilization, disk I/O, and network request rates) strictly for real-time anomaly detection and operational health analysis.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">2. Data Security & Storage</h2>
            <p>All ingested telemetry metrics are stored securely within your configured database instance and cached in isolated Redis stream channels. We do not transmit system metrics to third-party tracking services.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">3. Information Sharing</h2>
            <p>Anomix does not sell, rent, or trade your infrastructure telemetry or operational data. Telemetry is exclusively used by the autonomous anomaly detection algorithms running on your platform.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">4. Contact Information</h2>
            <p>If you have questions regarding data collection or infrastructure privacy, please contact your system administrator.</p>
          </section>
        </div>
      </main>
    </div>
  )
}
