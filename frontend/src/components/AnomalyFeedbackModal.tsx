import React, { useState } from 'react'
import { Anomaly, anomalyAPI } from '../api/client'
import { X, CheckCircle2, XCircle, HelpCircle, MessageSquare, Sparkles, Loader2 } from 'lucide-react'

interface AnomalyFeedbackModalProps {
  anomaly: Anomaly
  onClose: () => void
  onFeedbackSubmitted: (updatedAnomaly: Anomaly) => void
}

export const AnomalyFeedbackModal: React.FC<AnomalyFeedbackModalProps> = ({
  anomaly,
  onClose,
  onFeedbackSubmitted,
}) => {
  const [status, setStatus] = useState<'true_positive' | 'false_positive' | 'unreviewed'>(
    (anomaly.feedback_status as any) || 'true_positive'
  )
  const [note, setNote] = useState<string>(anomaly.feedback_note || '')
  const [submitting, setSubmitting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const response = await anomalyAPI.addFeedback(anomaly.id, status, note.trim() || undefined)
      onFeedbackSubmitted(response.data)
      onClose()
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to submit feedback')
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-500/20 p-2.5 text-indigo-400 border border-indigo-500/30">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">Provide ML Feedback</h3>
              <p className="text-xs text-slate-400">Help the ensemble model tune its detection accuracy</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Anomaly Details Card */}
        <div className="mt-4 rounded-xl border border-slate-800/80 bg-slate-950/60 p-3.5 text-xs text-slate-300 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Metric</span>
            <span className="font-semibold text-white font-mono">{anomaly.metric_name}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Observed Value</span>
            <span className="font-mono font-bold text-blue-400">{anomaly.value.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Confidence Score</span>
            <span className="font-mono font-semibold text-amber-400">
              {(anomaly.confidence_score * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Timestamp</span>
            <span className="text-slate-300">{new Date(anomaly.anomaly_timestamp).toLocaleString()}</span>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mt-4 rounded-lg bg-rose-950/60 border border-rose-800 p-3 text-xs text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          {/* Feedback Type Selection */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
              Classification
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                onClick={() => setStatus('true_positive')}
                className={`flex flex-col items-center justify-center gap-1.5 rounded-xl border p-3 text-xs font-medium transition-all ${
                  status === 'true_positive'
                    ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300 ring-1 ring-emerald-500/50 shadow-lg shadow-emerald-950/50'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <CheckCircle2 className={`h-5 w-5 ${status === 'true_positive' ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span>True Positive</span>
                <span className="text-[10px] text-slate-400 opacity-80">Real issue</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('false_positive')}
                className={`flex flex-col items-center justify-center gap-1.5 rounded-xl border p-3 text-xs font-medium transition-all ${
                  status === 'false_positive'
                    ? 'border-rose-500 bg-rose-950/40 text-rose-300 ring-1 ring-rose-500/50 shadow-lg shadow-rose-950/50'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <XCircle className={`h-5 w-5 ${status === 'false_positive' ? 'text-rose-400' : 'text-slate-500'}`} />
                <span>False Alarm</span>
                <span className="text-[10px] text-slate-400 opacity-80">Noise / Expected</span>
              </button>

              <button
                type="button"
                onClick={() => setStatus('unreviewed')}
                className={`flex flex-col items-center justify-center gap-1.5 rounded-xl border p-3 text-xs font-medium transition-all ${
                  status === 'unreviewed'
                    ? 'border-blue-500 bg-blue-950/40 text-blue-300 ring-1 ring-blue-500/50 shadow-lg shadow-blue-950/50'
                    : 'border-slate-800 bg-slate-950/40 text-slate-400 hover:border-slate-700 hover:text-slate-200'
                }`}
              >
                <HelpCircle className={`h-5 w-5 ${status === 'unreviewed' ? 'text-blue-400' : 'text-slate-500'}`} />
                <span>Unreviewed</span>
                <span className="text-[10px] text-slate-400 opacity-80">Reset label</span>
              </button>
            </div>
          </div>

          {/* Feedback Note */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
              <MessageSquare className="h-3.5 w-3.5" /> Investigation Note (Optional)
            </label>
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g., Scheduled cron job spike, valid traffic burst, or memory leak..."
              rows={3}
              className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-2.5 text-xs text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500/50 transition"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2 text-xs font-semibold text-white shadow-lg shadow-indigo-600/20 hover:bg-indigo-500 transition disabled:opacity-50"
            >
              {submitting && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
              <span>Save Feedback</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
