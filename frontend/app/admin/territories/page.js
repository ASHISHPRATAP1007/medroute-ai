"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import Button from "@/components/ui/Button";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Badge from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import {
  listCities, createCity, listAreas, createArea, listTerritories, createTerritory,
  assignMRToTerritory, removeMRFromTerritory,
} from "@/services/territory-service";
import { listMRs } from "@/services/mr-service";

export default function AdminTerritoriesPage() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const [selectedTerritory, setSelectedTerritory] = useState("");
  const [selectedMR, setSelectedMR] = useState("");

  const { data: citiesData } = useQuery({ queryKey: ["cities"], queryFn: listCities });
  const { data: areasData } = useQuery({ queryKey: ["areas"], queryFn: () => listAreas() });
  const { data: territoriesData, isLoading, isError } = useQuery({ queryKey: ["territories"], queryFn: listTerritories });
  const { data: mrsData } = useQuery({ queryKey: ["admin-mrs-all"], queryFn: () => listMRs({ status: "APPROVED", page_size: 100 }) });

  const cities = citiesData?.data || [];
  const areas = areasData?.data || [];
  const territories = territoriesData?.data || [];
  const approvedMRs = mrsData?.data?.items || [];

  const cityForm = useForm();
  const areaForm = useForm();
  const territoryForm = useForm();

  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: ["cities"] });
    queryClient.invalidateQueries({ queryKey: ["areas"] });
    queryClient.invalidateQueries({ queryKey: ["territories"] });
  };

  const createCityMutation = useMutation({
    mutationFn: createCity,
    onSuccess: () => { showToast("City created.", "success"); invalidateAll(); cityForm.reset(); },
    onError: (err) => showToast(err.message || "Failed to create city.", "error"),
  });
  const createAreaMutation = useMutation({
    mutationFn: createArea,
    onSuccess: () => { showToast("Area created.", "success"); invalidateAll(); areaForm.reset(); },
    onError: (err) => showToast(err.message || "Failed to create area.", "error"),
  });
  const createTerritoryMutation = useMutation({
    mutationFn: createTerritory,
    onSuccess: () => { showToast("Territory created.", "success"); invalidateAll(); territoryForm.reset(); },
    onError: (err) => showToast(err.message || "Failed to create territory.", "error"),
  });
  const assignMutation = useMutation({
    mutationFn: () => assignMRToTerritory(selectedTerritory, selectedMR),
    onSuccess: () => { showToast("MR assigned to territory.", "success"); invalidateAll(); },
    onError: (err) => showToast(err.message || "Failed to assign MR.", "error"),
  });
  const removeMutation = useMutation({
    mutationFn: ({ territoryId, mrId }) => removeMRFromTerritory(territoryId, mrId),
    onSuccess: () => { showToast("MR removed from territory.", "success"); invalidateAll(); },
    onError: (err) => showToast(err.message || "Failed to remove MR.", "error"),
  });

  return (
    <div>
      <PageHeader title="Territories" description="Manage cities, areas, territories, and MR assignments." />

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <h2 className="mb-3 font-medium text-slate-900">New City</h2>
          <form className="space-y-3" onSubmit={cityForm.handleSubmit((v) => createCityMutation.mutate(v))}>
            <Input label="Name" id="city_name" {...cityForm.register("name", { required: true })} />
            <Input label="State" id="city_state" {...cityForm.register("state", { required: true })} />
            <Button type="submit" className="w-full"><Plus className="h-4 w-4" aria-hidden="true" />Add City</Button>
          </form>
        </Card>

        <Card>
          <h2 className="mb-3 font-medium text-slate-900">New Area</h2>
          <form className="space-y-3" onSubmit={areaForm.handleSubmit((v) => createAreaMutation.mutate(v))}>
            <Select label="City" id="area_city" options={[{ value: "", label: "Select city" }, ...cities.map((c) => ({ value: c.id, label: c.name }))]} {...areaForm.register("city_id", { required: true })} />
            <Input label="Name" id="area_name" {...areaForm.register("name", { required: true })} />
            <Input label="Pincode" id="area_pincode" {...areaForm.register("pincode")} />
            <Button type="submit" className="w-full"><Plus className="h-4 w-4" aria-hidden="true" />Add Area</Button>
          </form>
        </Card>

        <Card>
          <h2 className="mb-3 font-medium text-slate-900">New Territory</h2>
          <form className="space-y-3" onSubmit={territoryForm.handleSubmit((v) => createTerritoryMutation.mutate(v))}>
            <Select label="Area" id="territory_area" options={[{ value: "", label: "Select area" }, ...areas.map((a) => ({ value: a.id, label: a.name }))]} {...territoryForm.register("area_id", { required: true })} />
            <Input label="Name" id="territory_name" {...territoryForm.register("name", { required: true })} />
            <Input label="Description" id="territory_description" {...territoryForm.register("description")} />
            <Button type="submit" className="w-full"><Plus className="h-4 w-4" aria-hidden="true" />Add Territory</Button>
          </form>
        </Card>
      </div>

      <Card className="mt-6">
        <h2 className="mb-3 font-medium text-slate-900">Assign MR to Territory</h2>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Select id="assign_territory" className="sm:max-w-xs" value={selectedTerritory} onChange={(e) => setSelectedTerritory(e.target.value)}
            options={[{ value: "", label: "Select territory" }, ...territories.map((t) => ({ value: t.id, label: t.name }))]} />
          <Select id="assign_mr" className="sm:max-w-xs" value={selectedMR} onChange={(e) => setSelectedMR(e.target.value)}
            options={[{ value: "", label: "Select MR" }, ...approvedMRs.map((m) => ({ value: m.id, label: m.full_name }))]} />
          <Button disabled={!selectedTerritory || !selectedMR} onClick={() => assignMutation.mutate()}>Assign</Button>
        </div>
      </Card>

      <div className="mt-6">
        <h2 className="mb-3 font-medium text-slate-900">All Territories</h2>
        {isLoading && <SkeletonRows count={3} />}
        {isError && <ErrorState />}
        {territories.length === 0 && !isLoading && <EmptyState title="No territories created yet." />}
        <div className="space-y-3">
          {territories.map((territory) => (
            <Card key={territory.id}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">{territory.name}</p>
                  {territory.description && <p className="text-sm text-slate-500">{territory.description}</p>}
                </div>
                <Badge status={territory.status} />
              </div>
              {territory.mr_links && territory.mr_links.length > 0 && (
                <ul className="mt-3 divide-y divide-slate-100 border-t border-slate-100 pt-2">
                  {territory.mr_links.map((link) => (
                    <li key={link.id} className="flex items-center justify-between py-1.5 text-sm">
                      <span className="text-slate-600">MR ID: {link.mr_id}</span>
                      <Button
                        variant="danger" className="!px-2 !py-1 text-xs"
                        onClick={() => removeMutation.mutate({ territoryId: territory.id, mrId: link.mr_id })}
                      >
                        Remove
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
