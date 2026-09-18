"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { useAuth } from "@/hooks/use-auth";
import { listMyTerritories } from "@/services/territory-service";

export default function MRProfilePage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useQuery({ queryKey: ["my-territories"], queryFn: listMyTerritories });
  const territories = data?.data || [];

  if (!user) return <Skeleton className="h-64 max-w-lg" />;

  return (
    <div className="max-w-lg">
      <PageHeader title="My Profile" description="Your account details. Role and status are managed by your admin." />

      <Card>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between"><dt className="text-slate-500">Name</dt><dd className="font-medium text-slate-900">{user.full_name}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Email</dt><dd>{user.email}</dd></div>
          <div className="flex justify-between"><dt className="text-slate-500">Phone</dt><dd>{user.phone}</dd></div>
        </dl>
      </Card>

      <Card className="mt-4">
        <h2 className="mb-3 font-medium text-slate-900">Assigned Territories</h2>
        {isLoading && <Skeleton className="h-10" />}
        {isError && <ErrorState />}
        {!isLoading && territories.length === 0 && <p className="text-sm text-slate-500">No territories assigned yet.</p>}
        <ul className="space-y-2">
          {territories.map((t) => (
            <li key={t.id} className="text-sm text-slate-700">{t.name}</li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
