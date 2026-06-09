import { z } from "zod";
import { PASSWORD_REGEX } from "./password-validation";

export const signIn2Schema = z.object({
  login: z.string().min(1, "Please enter your login"),
  password: z.string().min(1, "Please enter your password"),
});

export type SignIn2Schema = z.infer<typeof signIn2Schema>;
