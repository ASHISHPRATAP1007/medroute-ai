import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});

export const registerSchema = z
  .object({
    full_name: z.string().trim().min(2, "Full name is required."),
    mobile_number: z
      .string()
      .trim()
      .regex(/^[6-9]\d{9}$/, "Enter a valid 10-digit Indian mobile number."),
    email: z.string().email("Enter a valid email address."),
    password: z
      .string()
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^\w\s]).{8,}$/,
        "Password must be 8+ characters with uppercase, lowercase, a number, and a special character."
      ),
    confirm_password: z.string(),
    company_name: z.string().trim().min(1, "Company name is required."),
    employee_id: z.string().trim().min(1, "Employee ID is required."),
    city: z.string().trim().min(1, "City is required."),
    state: z.string().trim().min(1, "State is required."),
    assigned_area: z.string().trim().min(1, "Assigned area is required."),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  });
