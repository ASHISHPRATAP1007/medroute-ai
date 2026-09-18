"use client";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Feedback";
import { useAuth } from "@/hooks/use-auth";

export default function AdminSettingsPage() {
  const { user } = useAuth();

  return (
    <div className="max-w-lg">
      <PageHeader title="Settings" description="Application information and your account role." />
      <Card>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Application</dt><dd>MedRoute AI — Phase 1</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Environment</dt><dd>{process.env.NODE_ENV}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Your Role</dt><dd>{user?.role}</dd></div>
        </dl>
      </Card>
      <p className="mt-4 text-sm text-slate-400">Additional configuration options will be available in future phases.</p>
    </div>
  );
}
