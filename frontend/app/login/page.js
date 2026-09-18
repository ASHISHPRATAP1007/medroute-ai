"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { loginSchema } from "@/schemas/auth-schemas";
import { Input } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/use-auth";
import { useToast } from "@/components/ui/Toast";
import { ApiError } from "@/lib/api-client";

function Logo() {
  return (
    <div className="font-head flex items-center justify-center gap-2 text-lg font-bold text-slate-900">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 2L4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4z" fill="#2B3A67" />
        <path d="M12 7v10M7.5 12h9" stroke="#E8A33D" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      MedRoute AI
    </div>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { login, user } = useAuth();
  const { showToast } = useToast();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values) {
    try {
      const current = await login(values.email, values.password);
      showToast("Welcome back!", "success");
      router.push(current.role === "MR" ? "/mr/dashboard" : "/admin/dashboard");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong.";
      setError("root", { message });
    }
  }

  return (
    <main className="dot-grid-bg flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6"><Logo /></div>
        <div className="card p-6 shadow-sm">
          <h1 className="font-head text-lg font-bold text-slate-900">Log in to your account</h1>
          <form className="mt-5 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <Input label="Email" id="email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
            <Input label="Password" id="password" type="password" autoComplete="current-password" error={errors.password?.message} {...register("password")} />
            {errors.root && (
              <p role="alert" className="text-sm text-danger-600">
                {errors.root.message}
              </p>
            )}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Logging in…" : "Login"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-500">
            New Medical Representative?{" "}
            <Link href="/register" className="font-medium text-primary-600 hover:underline">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
