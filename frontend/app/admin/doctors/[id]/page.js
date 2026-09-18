"use client";

import { useRouter, useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, ErrorState, Skeleton } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import DoctorForm from "@/features/doctors/DoctorForm";
import { getDoctor, updateDoctor } from "@/services/doctor-service";
import { getDoctorExternalData, syncDoctorExternalData } from "@/services/external-data-service";

export default function EditDoctorPage() {
  const { id } = useParams();
  const router = useRouter();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["doctor", id],
    queryFn: () => getDoctor(id),
  });

  const { data: externalData } = useQuery({
    queryKey: ["doctor-external", id],
    queryFn: () => getDoctorExternalData(id),
    enabled: !!id,
  });

  const syncMutation = useMutation({
    mutationFn: () => syncDoctorExternalData(id),
    onSuccess: () => {
      showToast("Google Places data synced.", "success");
      queryClient.invalidateQueries({ queryKey: ["doctor-external", id] });
    },
    onError: (err) => showToast(err.message || "Sync failed — Google Places may not be configured.", "error"),
  });

  async function handleSubmit(values) {
    try {
      await updateDoctor(id, values);
      showToast("Doctor updated successfully.", "success");
      router.push("/admin/doctors");
    } catch (err) {
      showToast(err.message || "Failed to update doctor.", "error");
    }
  }

  const enrichment = externalData?.data;

  return (
    <div>
      <PageHeader
        title="Edit Doctor"
        actions={
          <Button variant="secondary" onClick={() => syncMutation.mutate()} disabled={syncMutation.isPending}>
            <RefreshCw className={`h-4 w-4 ${syncMutation.isPending ? "animate-spin" : ""}`} aria-hidden="true" />
            {syncMutation.isPending ? "Syncing…" : "Sync from Google"}
          </Button>
        }
      />
      {isLoading && <Skeleton className="h-96 max-w-2xl" />}
      {isError && <ErrorState />}
      {data?.data && (
        <>
          <Card className="max-w-2xl">
            <DoctorForm defaultValues={data.data} onSubmit={handleSubmit} submitLabel="Save Changes" />
          </Card>
          <p className="mt-3 max-w-2xl text-xs text-slate-400">
            {enrichment
              ? `Last synced from Google: ${new Date(enrichment.last_synced_at).toLocaleString()} (rating ${enrichment.rating ?? "—"})`
              : "This doctor has not been synced with Google Places yet."}
          </p>
        </>
      )}
    </div>
  );
}
