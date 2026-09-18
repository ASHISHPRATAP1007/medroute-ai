import { z } from "zod";

export const doctorSchema = z.object({
  full_name: z.string().trim().min(1, "Full name is required."),
  specialization_id: z.string().min(1, "Specialization is required."),
  qualification: z.string().optional().or(z.literal("")),
  phone: z.string().optional().or(z.literal("")),
  email: z.string().email("Enter a valid email.").optional().or(z.literal("")),
  clinic_name: z.string().optional().or(z.literal("")),
  hospital_name: z.string().optional().or(z.literal("")),
  address: z.string().trim().min(1, "Address is required."),
  area: z.string().optional().or(z.literal("")),
  city: z.string().trim().min(1, "City is required."),
  state: z.string().trim().min(1, "State is required."),
  pincode: z.string().regex(/^\d{6}$/, "Pincode must be 6 digits.").optional().or(z.literal("")),
  latitude: z.union([z.string(), z.number()]).optional().or(z.literal("")),
  longitude: z.union([z.string(), z.number()]).optional().or(z.literal("")),
});
