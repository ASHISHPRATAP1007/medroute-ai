"use client";

import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Feedback";
import { useToast } from "@/components/ui/Toast";
import DoctorForm from "@/features/doctors/DoctorForm";
import { createDoctor } from "@/services/doctor-service";

export default function NewDoctorPage() {
  const router = useRouter();
  const { showToast } = useToast();

  async function handleSubmit(values) {
    try {
      await createDoctor(values);
      showToast("Doctor created successfully.", "success");
      router.push("/admin/doctors");
    } catch (err) {
      showToast(err.message || "Failed to create doctor.", "error");
    }
  }

  return (
    <div>
      <PageHeader title="Add Doctor" description="Add a new doctor to the directory." />
      <Card className="max-w-2xl">
        <DoctorForm onSubmit={handleSubmit} submitLabel="Create Doctor" />
      </Card>
    </div>
  );
}
