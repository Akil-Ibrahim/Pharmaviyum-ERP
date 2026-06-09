import { z } from "zod";
import { PASSWORD_REGEX } from "./password-validation";

export const signInSchema = z.object({
  login: z.string().min(1, "Please enter your login"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(
      PASSWORD_REGEX,
      "Password must contain uppercase, lowercase, number, and special character (!@#$%^&*)",
    ),
});

export type SignInSchema = z.infer<typeof signInSchema>;
