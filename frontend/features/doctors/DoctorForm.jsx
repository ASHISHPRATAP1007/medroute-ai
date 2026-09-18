"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { Input, Select } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import { doctorSchema } from "@/schemas/doctor-schema";
import { listSpecializations } from "@/services/doctor-service";

export default function DoctorForm({ defaultValues, onSubmit, submitLabel = "Save Doctor" }) {
  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const specializations = specData?.data || [];

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(doctorSchema), defaultValues });

  return (
    <form
      className="space-y-4"
      noValidate
      onSubmit={handleSubmit((values) =>
        onSubmit({
          ...values,
          latitude: values.latitude === "" ? null : Number(values.latitude),
          longitude: values.longitude === "" ? null : Number(values.longitude),
        })
      )}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Full Name" id="full_name" error={errors.full_name?.message} {...register("full_name")} />
        <Select
          label="Specialization" id="specialization_id" error={errors.specialization_id?.message}
          options={[{ value: "", label: "Select specialization" }, ...specializations.map((s) => ({ value: s.id, label: s.name }))]}
          {...register("specialization_id")}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Qualification" id="qualification" {...register("qualification")} />
        <Input label="Phone" id="phone" error={errors.phone?.message} {...register("phone")} />
      </div>
      <Input label="Email" id="email" type="email" error={errors.email?.message} {...register("email")} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Clinic Name" id="clinic_name" {...register("clinic_name")} />
        <Input label="Hospital Name" id="hospital_name" {...register("hospital_name")} />
      </div>
      <Input label="Address" id="address" error={errors.address?.message} {...register("address")} />
      <div className="grid gap-4 sm:grid-cols-3">
        <Input label="Area" id="area" {...register("area")} />
        <Input label="City" id="city" error={errors.city?.message} {...register("city")} />
        <Input label="State" id="state" error={errors.state?.message} {...register("state")} />
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <Input label="Pincode" id="pincode" error={errors.pincode?.message} {...register("pincode")} />
        <Input label="Latitude" id="latitude" type="number" step="any" error={errors.latitude?.message} {...register("latitude")} />
        <Input label="Longitude" id="longitude" type="number" step="any" error={errors.longitude?.message} {...register("longitude")} />
      </div>

      <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
        {isSubmitting ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}
