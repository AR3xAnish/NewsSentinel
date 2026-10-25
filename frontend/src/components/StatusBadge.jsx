import React from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle, AlertCircle, Info } from 'lucide-react';

export default function StatusBadge({ status, confidence, size = 'md' }) {
  const normStatus = (status || 'UNVERIFIED').toUpperCase();

  const configs = {
    CORROBORATED: {
      label: 'Corroborated',
      className: 'bg-emerald-50 text-emerald-800 border-emerald-300',
      icon: CheckCircle2,
      iconClass: 'text-emerald-600',
    },
    PARTIALLY_CORROBORATED: {
      label: 'Partially Corroborated',
      className: 'bg-amber-50 text-amber-800 border-amber-300',
      icon: Info,
      iconClass: 'text-amber-600',
    },
    CONFLICTING: {
      label: 'Conflicting Details',
      className: 'bg-rose-50 text-rose-800 border-rose-300',
      icon: AlertTriangle,
      iconClass: 'text-rose-600',
    },
    UNVERIFIED: {
      label: 'Unverified',
      className: 'bg-slate-100 text-slate-700 border-slate-300',
      icon: HelpCircle,
      iconClass: 'text-slate-500',
    },
    INSUFFICIENT_EVIDENCE: {
      label: 'Single-Source / Insufficient',
      className: 'bg-purple-50 text-purple-800 border-purple-300',
      icon: AlertCircle,
      iconClass: 'text-purple-600',
    },
  };

  const current = configs[normStatus] || configs.UNVERIFIED;
  const Icon = current.icon;
  const isSmall = size === 'sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium border rounded-full ${
        isSmall ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
      } ${current.className}`}
    >
      <Icon className={isSmall ? 'w-3 h-3' : 'w-3.5 h-3.5'} />
      <span>{current.label}</span>
      {confidence !== undefined && confidence !== null && (
        <span className="opacity-75 font-mono text-[10px] ml-0.5">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </span>
  );
}
