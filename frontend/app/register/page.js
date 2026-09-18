"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { registerSchema } from "@/schemas/auth-schemas";
import { Input } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import { registerMR } from "@/services/auth-service";
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

export default function RegisterPage() {
  const [submitted, setSubmitted] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values) {
    try {
      await registerMR(values);
      setSubmitted(true);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Something went wrong.";
      setError("root", { message });
    }
  }

  if (submitted) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="card max-w-md p-8 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-success-500" aria-hidden="true" />
          <h1 className="mt-4 text-lg font-bold text-slate-900">Registration submitted successfully</h1>
          <p className="mt-2 text-sm text-slate-500">Your account is waiting for admin approval.</p>
          <Link href="/login" className="btn-primary mt-6 inline-flex">Back to login</Link>
        </div>
      </main>
    );
  }

  return (
    <main className="dot-grid-bg flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg">
        <div className="mb-6"><Logo /></div>
        <div className="card p-6 shadow-sm">
          <h1 className="font-head text-lg font-bold text-slate-900">Register as a Medical Representative</h1>
          <form className="mt-5 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Full Name" id="full_name" error={errors.full_name?.message} {...register("full_name")} />
              <Input label="Mobile Number" id="mobile_number" placeholder="9876543210" error={errors.mobile_number?.message} {...register("mobile_number")} />
            </div>
            <Input label="Email" id="email" type="email" error={errors.email?.message} {...register("email")} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Password" id="password" type="password" error={errors.password?.message} {...register("password")} />
              <Input label="Confirm Password" id="confirm_password" type="password" error={errors.confirm_password?.message} {...register("confirm_password")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Company Name" id="company_name" error={errors.company_name?.message} {...register("company_name")} />
              <Input label="Employee ID" id="employee_id" error={errors.employee_id?.message} {...register("employee_id")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="City" id="city" error={errors.city?.message} {...register("city")} />
              <Input label="State" id="state" error={errors.state?.message} {...register("state")} />
            </div>
            <Input label="Assigned Area" id="assigned_area" error={errors.assigned_area?.message} {...register("assigned_area")} />

            {errors.root && (
              <p role="alert" className="text-sm text-danger-600">
                {errors.root.message}
              </p>
            )}
            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Submitting…" : "Register"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-primary-600 hover:underline">
              Login
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}
