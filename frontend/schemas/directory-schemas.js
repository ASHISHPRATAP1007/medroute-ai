import { z } from "zod";

export const shopSchema = z.object({
  name: z.string().trim().min(1, "Name is required."),
  contact_person: z.string().optional().or(z.literal("")),
  phone: z.string().optional().or(z.literal("")),
  email: z.string().email("Enter a valid email.").optional().or(z.literal("")),
  address: z.string().trim().min(1, "Address is required."),
  area: z.string().optional().or(z.literal("")),
  city: z.string().trim().min(1, "City is required."),
  state: z.string().trim().min(1, "State is required."),
  pincode: z.string().regex(/^\d{6}$/, "Pincode must be 6 digits.").optional().or(z.literal("")),
});

export const stockistSchema = z.object({
  name: z.string().trim().min(1, "Name is required."),
  company_name: z.string().optional().or(z.literal("")),
  contact_person: z.string().optional().or(z.literal("")),
  phone: z.string().optional().or(z.literal("")),
  email: z.string().email("Enter a valid email.").optional().or(z.literal("")),
  address: z.string().trim().min(1, "Address is required."),
  area: z.string().optional().or(z.literal("")),
  city: z.string().trim().min(1, "City is required."),
  state: z.string().trim().min(1, "State is required."),
  pincode: z.string().regex(/^\d{6}$/, "Pincode must be 6 digits.").optional().or(z.literal("")),
  coverage_area: z.string().optional().or(z.literal("")),
});
