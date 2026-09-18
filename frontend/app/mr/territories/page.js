"use client";

import { useQuery } from "@tanstack/react-query";
import { Map } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Badge from "@/components/ui/Badge";
import { listMyTerritories } from "@/services/territory-service";

export default function MRTerritoriesPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["my-territories"], queryFn: listMyTerritories });
  const territories = data?.data || [];

  return (
    <div>
      <PageHeader title="My Territories" description="Territories currently assigned to you by your admin." />

      {isLoading && <SkeletonRows count={3} />}
      {isError && <ErrorState />}
      {!isLoading && territories.length === 0 && (
        <EmptyState
          icon={Map}
          title="No territories assigned yet."
          description="Contact your administrator to get a territory assigned to your account."
        />
      )}

      <div className="space-y-3">
        {territories.map((t) => (
          <Card key={t.id}>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-slate-900">{t.name}</p>
                {t.description && <p className="text-sm text-slate-500">{t.description}</p>}
              </div>
              <Badge status={t.status} />
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
