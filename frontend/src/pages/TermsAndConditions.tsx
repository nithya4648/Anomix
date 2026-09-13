import { Link } from 'react-router-dom'
import { FileText, ArrowLeft } from 'lucide-react'

export const TermsAndConditions = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900 px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-400" />
            <span className="text-lg font-bold text-white">Anomix Terms & Conditions</span>
          </div>
          <Link to="/" className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition">
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-12">
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-8 shadow-md space-y-6 text-slate-300 text-sm leading-relaxed">
          <h1 className="text-2xl font-bold text-white border-b border-slate-800 pb-4">Terms and Conditions</h1>
          
          <p>Last updated: September 13, 2026</p>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">1. Platform Usage & Scope</h2>
            <p>By deploying or accessing the Anomix Anomaly Detection platform, you agree to use the monitoring tools solely for infrastructure telemetry analysis and anomaly detection in compliance with applicable laws.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">2. System Availability & Service Levels</h2>
            <p>Anomix anomaly detection models (including IsolationForest, Z-Score, and LSTM Autoencoders) provide statistical indicators based on metric inputs. System alerts should be integrated into your existing operational monitoring workflows.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">3. Intellectual Property</h2>
            <p>All source code, platform branding, and machine learning pipeline components belong to the Anomix project contributors.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-lg font-semibold text-white">4. Limitation of Liability</h2>
            <p>Anomix is provided on an "AS IS" basis. Operators maintain responsibility for infrastructure incident response and system maintenance.</p>
          </section>
        </div>
      </main>
    </div>
  )
}
