import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { X, Plus, Trash2, CheckCircle, AlertTriangle, Sliders, Shield } from 'lucide-react'

interface RuleConfig {
  id?: string
  metric_name: string
  threshold_value: number
  duration_minutes: number
  severity: string
  enabled: boolean
  recovery_confirmation_minutes: number
}

interface RuleConfigPanelProps {
  onClose: () => void
}

const API_KEY = import.meta.env.VITE_API_KEY || 'pulsewatch_dev_key_change_in_prod'
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const RuleConfigPanel: React.FC<RuleConfigPanelProps> = ({ onClose }) => {
  const [rules, setRules] = useState<RuleConfig[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [newRule, setNewRule] = useState<RuleConfig>({
    metric_name: '*',
    threshold_value: 0.8,
    duration_minutes: 5,
    severity: 'critical',
    enabled: true,
    recovery_confirmation_minutes: 5,
  })

  const client = axios.create({
    baseURL: API_BASE,
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
  })

  const fetchRules = async () => {
    try {
      setLoading(true)
      const res = await client.get<RuleConfig[]>('/config/rules/')
      setRules(res.data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch rules')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRules()
  }, [])

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await client.post('/config/rules/', newRule)
      setNewRule({
        metric_name: '*',
        threshold_value: 0.8,
        duration_minutes: 5,
        severity: 'critical',
        enabled: true,
        recovery_confirmation_minutes: 5,
      })
      fetchRules()
    } catch (err: any) {
      setError(err.message || 'Failed to create rule')
    }
  }

  const handleDeleteRule = async (id?: string) => {
    if (!id) return
    try {
      await client.delete(`/config/rules/${id}`)
      fetchRules()
    } catch (err: any) {
      setError(err.message || 'Failed to delete rule')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-4xl rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-2.5 text-blue-400 border border-blue-500/20">
              <Sliders className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white tracking-tight">Detection Rule Configuration</h2>
              <p className="text-xs text-slate-400">Configure real-time thresholds, durations, and alert severities</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="overflow-y-auto py-4 space-y-6 flex-1 pr-1">
          {error && (
            <div className="rounded-lg bg-rose-950/60 border border-rose-800 p-3 text-sm text-rose-300 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Add Rule Form */}
          <form onSubmit={handleCreateRule} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Plus className="h-4 w-4 text-blue-400" /> Add New Rule
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Metric Target</label>
                <input
                  type="text"
                  value={newRule.metric_name}
                  onChange={(e) => setNewRule({ ...newRule, metric_name: e.target.value })}
                  placeholder="e.g. cpu_usage or *"
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Threshold (0.0 - 1.0)</label>
                <input
                  type="number"
                  step="0.05"
                  min="0"
                  max="1"
                  value={newRule.threshold_value}
                  onChange={(e) => setNewRule({ ...newRule, threshold_value: parseFloat(e.target.value) })}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Severity</label>
                <select
                  value={newRule.severity}
                  onChange={(e) => setNewRule({ ...newRule, severity: e.target.value })}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                >
                  <option value="critical">Critical</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
                </select>
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Duration (Minutes)</label>
                <input
                  type="number"
                  min="1"
                  value={newRule.duration_minutes}
                  onChange={(e) => setNewRule({ ...newRule, duration_minutes: parseInt(e.target.value) || 1 })}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Recovery Window (Min)</label>
                <input
                  type="number"
                  min="1"
                  value={newRule.recovery_confirmation_minutes}
                  onChange={(e) => setNewRule({ ...newRule, recovery_confirmation_minutes: parseInt(e.target.value) || 1 })}
                  className="w-full rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-slate-200 focus:border-blue-500 focus:outline-none"
                  required
                />
              </div>
              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-500 transition shadow-lg shadow-blue-500/20"
                >
                  Save Rule
                </button>
              </div>
            </div>
          </form>

          {/* Rule List */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" /> Active Detection Rules ({rules.length})
            </h3>
            {loading ? (
              <p className="text-xs text-slate-400">Loading rules...</p>
            ) : rules.length === 0 ? (
              <div className="rounded-xl border border-slate-800/80 bg-slate-950/40 p-6 text-center text-xs text-slate-400">
                No custom detection rules configured. System is using baseline ML/ensemble models.
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/50">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="border-b border-slate-800 bg-slate-950 text-slate-400 uppercase">
                    <tr>
                      <th className="px-4 py-3">Metric</th>
                      <th className="px-4 py-3">Threshold</th>
                      <th className="px-4 py-3">Duration</th>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Auto-Recover</th>
                      <th className="px-4 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {rules.map((rule) => (
                      <tr key={rule.id} className="hover:bg-slate-900/60 transition">
                        <td className="px-4 py-3 font-medium text-white">{rule.metric_name}</td>
                        <td className="px-4 py-3 font-mono text-blue-400">{(rule.threshold_value * 100).toFixed(0)}%</td>
                        <td className="px-4 py-3">{rule.duration_minutes} min</td>
                        <td className="px-4 py-3">
                          <span
                            className={`rounded px-2 py-0.5 text-[10px] font-semibold uppercase ${
                              rule.severity === 'critical'
                                ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                                : rule.severity === 'warning'
                                ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            }`}
                          >
                            {rule.severity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-400">{rule.recovery_confirmation_minutes} min</td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => handleDeleteRule(rule.id)}
                            className="rounded p-1 text-slate-400 hover:bg-rose-950/60 hover:text-rose-400 transition"
                            title="Delete Rule"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-800 pt-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-200 hover:bg-slate-700 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default RuleConfigPanel
