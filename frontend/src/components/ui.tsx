import type { ButtonHTMLAttributes, InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { twMerge } from 'tailwind-merge'

export function Button({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button className={twMerge('inline-flex h-8 items-center justify-center gap-2 border border-purple-700 bg-purple-700 px-3 text-xs font-semibold text-white transition hover:bg-purple-800 disabled:cursor-not-allowed disabled:opacity-45', className)} {...props} />
}
export function SecondaryButton({ className, ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <Button className={twMerge('border-slate-300 bg-white text-slate-800 hover:border-purple-500 hover:bg-purple-50', className)} {...props} />
}
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) { return <input className={twMerge('h-8 w-full border border-slate-300 bg-white px-2 text-sm outline-none focus:border-purple-600 focus:ring-1 focus:ring-purple-200', className)} {...props} /> }
export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) { return <select className={twMerge('h-8 w-full border border-slate-300 bg-white px-2 text-sm outline-none focus:border-purple-600', className)} {...props} /> }
export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) { return <textarea className={twMerge('w-full border border-slate-300 bg-white p-2 text-sm outline-none focus:border-purple-600', className)} {...props} /> }
export function Field({ label, children }: { label: string; children: React.ReactNode }) { return <label className="grid gap-1 text-xs font-semibold text-slate-600"><span>{label}</span>{children}</label> }
export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'success' | 'danger' | 'warning'; children: React.ReactNode }) { const tones = { neutral: 'border-slate-300 bg-slate-100 text-slate-700', success: 'border-emerald-200 bg-emerald-50 text-emerald-800', danger: 'border-red-200 bg-red-50 text-red-800', warning: 'border-amber-300 bg-amber-50 text-amber-900' }; return <span className={`inline-flex border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide ${tones[tone]}`}>{children}</span> }
export function Empty({ children }: { children: React.ReactNode }) { return <div className="grid min-h-32 place-items-center border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">{children}</div> }
