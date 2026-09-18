import Link from "next/link";
import { Stethoscope, Building2, MapPin } from "lucide-react";

const STEPS = [
  { title: "Register", description: "Sign up with your company and territory details." },
  { title: "Get approved", description: "Your admin reviews and approves your account." },
  { title: "Discover your territory", description: "See the areas and territories assigned to you." },
  { title: "Find relevant doctors", description: "Search doctors, shops and stockists near you." },
  { title: "Manage your field work", description: "Plan visits directly from what you discover." },
];

function Logo() {
  return (
    <div className="font-head flex items-center gap-2 text-lg font-bold text-slate-900">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2L4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4z" fill="#2B3A67" />
        <path d="M12 7v10M7.5 12h9" stroke="#E8A33D" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      MedRoute AI
    </div>
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <header className="border-b border-slate-100">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <nav className="flex items-center gap-3">
            <Link href="/login" className="px-4 py-2 text-sm font-medium text-slate-700">Login</Link>
            <Link href="/register" className="btn-primary">Register as MR</Link>
          </nav>
        </div>
      </header>

      <section className="dot-grid-bg border-b border-slate-100">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div>
            <p className="mono mb-4 text-xs text-primary-600">FIELD INTELLIGENCE FOR MEDICAL REPS</p>
            <h1 className="font-head text-5xl font-extrabold leading-[1.05] tracking-tight text-slate-900">
              Find the right doctor.
              <br />
              Plan the right visit.
            </h1>
            <p className="mt-6 max-w-md text-lg text-slate-600">
              MedRoute AI maps every doctor, clinic and stockist in your territory — and tells
              you exactly who&apos;s worth visiting next.
            </p>
            <div className="mt-8 flex gap-3">
              <Link href="/register" className="btn-primary px-6 py-3 text-base">Register as MR</Link>
              <Link href="/login" className="btn-secondary px-6 py-3 text-base">Login</Link>
            </div>
          </div>

          <div className="card-tabbed p-5 shadow-sm">
            <div className="flex items-center justify-between border-b border-dashed border-slate-200 pb-3">
              <span className="mono text-xs text-slate-400">TODAY&apos;S FIELD LOG</span>
              <span className="mono text-xs text-success-500">● 3 planned</span>
            </div>
            <div className="mt-4 space-y-3">
              {[
                { name: "Dr. Ritu Malhotra", meta: "Cardiologist · Gomti Nagar", score: "92/100", tone: "bg-signal-50 text-signal-600" },
                { name: "Dr. Aman Kapoor", meta: "General Physician · Indira Nagar", score: "78/100", tone: "bg-primary-50 text-primary-600" },
                { name: "Dr. Sana Iqbal", meta: "Dermatologist · Aliganj", score: "64/100", tone: "bg-slate-100 text-slate-500", faded: true },
              ].map((row) => (
                <div key={row.name} className={`flex items-center justify-between ${row.faded ? "opacity-60" : ""}`}>
                  <div>
                    <p className="font-medium text-slate-900">{row.name}</p>
                    <p className="text-sm text-slate-400">{row.meta}</p>
                  </div>
                  <span className={`mono rounded px-2 py-1 text-xs ${row.tone}`}>{row.score}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl gap-5 px-6 py-16 sm:grid-cols-3">
        <div className="card p-6">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
            <Stethoscope className="h-4 w-4 text-primary-600" aria-hidden="true" />
          </div>
          <p className="font-head font-semibold text-slate-900">Doctor directory</p>
          <p className="mt-1 text-sm text-slate-500">Search by specialization, city, and area — filtered to your assigned territory only.</p>
        </div>
        <div className="card p-6">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
            <Building2 className="h-4 w-4 text-primary-600" aria-hidden="true" />
          </div>
          <p className="font-head font-semibold text-slate-900">Shops &amp; stockists</p>
          <p className="mt-1 text-sm text-slate-500">Every distributor and medical store mapped to the same territory hierarchy.</p>
        </div>
        <div className="card p-6">
          <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50">
            <MapPin className="h-4 w-4 text-primary-600" aria-hidden="true" />
          </div>
          <p className="font-head font-semibold text-slate-900">Territory-aware routing</p>
          <p className="mt-1 text-sm text-slate-500">Your daily plan is ordered by distance, not by whoever&apos;s on top of the list.</p>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-6 pb-24">
        <h2 className="font-head text-center text-xl font-bold text-slate-900">How it works</h2>
        <ol className="mt-8 space-y-4">
          {STEPS.map((step, i) => (
            <li key={step.title} className="flex items-start gap-3">
              <span className="mono flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-medium text-primary-700">
                {i + 1}
              </span>
              <div>
                <p className="font-medium text-slate-900">{step.title}</p>
                <p className="text-sm text-slate-500">{step.description}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}
