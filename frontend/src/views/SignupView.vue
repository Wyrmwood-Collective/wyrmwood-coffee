<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { apiCreateEmployee } from "@/api/employees";
import AppChrome from "@/components/AppChrome.vue";
import LogoutButton from "@/components/LogoutButton.vue";
import FormMessage from "@/components/FormMessage.vue";
import type { EmployeeRole } from "@/types/employee";

const router = useRouter();

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

const PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?`~";

function validatePassword(password: string): string | null {
  if (password.length < 8) {
    return "Password must be at least 8 characters.";
  }
  if (!/[A-Z]/.test(password)) {
    return "Password must include at least one capital letter.";
  }
  if (!/[0-9]/.test(password)) {
    return "Password must include at least one number.";
  }
  const specialPattern = new RegExp(
    `[${PASSWORD_SPECIAL_CHARS.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&")}]`,
  );
  if (!specialPattern.test(password)) {
    return "Password must include at least one special character.";
  }
  return null;
}

function validateHourlyRate(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Enter an hourly rate.";
  }
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) {
    return "Hourly rate must be a positive number with up to 2 decimal places.";
  }
  const rate = Number(trimmed);
  if (!Number.isFinite(rate) || rate <= 0) {
    return "Hourly rate must be greater than 0.";
  }
  return null;
}

const firstName = ref("");
const lastName = ref("");
const username = ref("");
const password = ref("");
const confirmPassword = ref("");
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const role = ref<EmployeeRole>("employee");
const hourlyRate = ref("15.00");
const hireDate = ref(todayIsoDate());
const termDate = ref("");
const active = ref(true);

const errorMessage = ref("");
const successMessage = ref("");
const submitting = ref(false);

function resetForm() {
  firstName.value = "";
  lastName.value = "";
  username.value = "";
  password.value = "";
  confirmPassword.value = "";
  showPassword.value = false;
  showConfirmPassword.value = false;
  role.value = "employee";
  hourlyRate.value = "15.00";
  hireDate.value = todayIsoDate();
  termDate.value = "";
  active.value = true;
}

async function handleSubmit() {
  errorMessage.value = "";
  successMessage.value = "";

  const trimmedFirstName = firstName.value.trim();
  const trimmedLastName = lastName.value.trim();
  const trimmedUsername = username.value.trim();
  const trimmedHourlyRate = hourlyRate.value.trim();

  if (
    !trimmedFirstName ||
    !trimmedLastName ||
    !trimmedUsername ||
    !password.value ||
    !role.value ||
    !trimmedHourlyRate ||
    !hireDate.value
  ) {
    errorMessage.value = "Fill in all required fields.";
    return;
  }

  if (password.value !== confirmPassword.value) {
    errorMessage.value = "Passwords do not match.";
    return;
  }

  const passwordError = validatePassword(password.value);
  if (passwordError) {
    errorMessage.value = passwordError;
    return;
  }

  const hourlyRateError = validateHourlyRate(trimmedHourlyRate);
  if (hourlyRateError) {
    errorMessage.value = hourlyRateError;
    return;
  }

  if (termDate.value && termDate.value <= hireDate.value) {
    errorMessage.value = "Termination date must be after hire date.";
    return;
  }

  submitting.value = true;
  try {
    await apiCreateEmployee({
      first_name: trimmedFirstName,
      last_name: trimmedLastName,
      username: trimmedUsername,
      password: password.value,
      role: role.value,
      hourly_rate: trimmedHourlyRate,
      hire_date: hireDate.value,
      ...(termDate.value ? { term_date: termDate.value } : {}),
      active: active.value,
    });

    successMessage.value = "Employee created successfully.";
    resetForm();

    setTimeout(() => {
      router.push({ name: "employees" });
    }, 1200);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Something went wrong.";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="page">
    <section class="card card-wide">
      <header class="brand">
        <h1>Wyrmwood Coffee</h1>
        <p>Admin — create employee</p>
      </header>

      <AppChrome />

      <h2>New employee</h2>

      <FormMessage :text="errorMessage" type="error" />
      <FormMessage :text="successMessage" type="success" />

      <form @submit.prevent="handleSubmit">
        <p class="form-section-title">Account</p>

        <div class="form-field">
          <label for="first_name">First name</label>
          <input id="first_name" v-model="firstName" type="text" required />
        </div>

        <div class="form-field">
          <label for="last_name">Last name</label>
          <input id="last_name" v-model="lastName" type="text" required />
        </div>

        <div class="form-field">
          <label for="username">Username</label>
          <input id="username" v-model="username" type="text" autocomplete="username" required />
        </div>

        <div class="form-field">
          <label for="password">Password</label>

          <div class="password-field">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              required
            />

            <button
              class="password-toggle"
              type="button"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              @click="showPassword = !showPassword"
            >
              <svg
                v-if="showPassword"
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M3 3l18 18" />
                <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                <path d="M9.9 4.2A10.6 10.6 0 0 1 12 4c5 0 9 4 10 8a12.7 12.7 0 0 1-2 3.7" />
                <path d="M6.6 6.6C4.3 8 2.7 10 2 12c1 4 5 8 10 8a10.4 10.4 0 0 0 4.1-.8" />
              </svg>

              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </div>

          <p class="hint">
            At least 8 characters with a capital letter, a number, and a special character.
          </p>
        </div>

        <div class="form-field">
          <label for="confirm_password">Confirm password</label>

          <div class="password-field">
            <input
              id="confirm_password"
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              autocomplete="new-password"
              required
            />

            <button
              class="password-toggle"
              type="button"
              :aria-label="showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'"
              @click="showConfirmPassword = !showConfirmPassword"
            >
              <svg
                v-if="showConfirmPassword"
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M3 3l18 18" />
                <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
                <path d="M9.9 4.2A10.6 10.6 0 0 1 12 4c5 0 9 4 10 8a12.7 12.7 0 0 1-2 3.7" />
                <path d="M6.6 6.6C4.3 8 2.7 10 2 12c1 4 5 8 10 8a10.4 10.4 0 0 0 4.1-.8" />
              </svg>

              <svg
                v-else
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
          </div>
        </div>

        <p class="form-section-title">Employment</p>

        <div class="form-field">
          <label for="role">Role</label>
          <select id="role" v-model="role" required>
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>

        <div class="form-field">
          <label for="hourly_rate">Hourly rate (USD)</label>
          <input
            id="hourly_rate"
            v-model="hourlyRate"
            type="number"
            min="0.01"
            step="0.01"
            placeholder="15.00"
            required
          />
          <p class="hint">Must be greater than 0, up to 2 decimal places.</p>
        </div>

        <div class="form-field">
          <label for="hire_date">Hire date</label>
          <input id="hire_date" v-model="hireDate" type="date" required />
        </div>

        <div class="form-field">
          <label for="term_date">Termination date (optional)</label>
          <input id="term_date" v-model="termDate" type="date" />
          <p class="hint">Leave blank for active employees. Must be after hire date.</p>
        </div>

        <div class="form-field-checkbox">
          <label for="active">
            <input id="active" v-model="active" type="checkbox" />
            Employee is active
          </label>
        </div>

        <button class="btn btn-primary" type="submit" :disabled="submitting">
          {{ submitting ? "Please wait…" : "Create employee" }}
        </button>
      </form>

      <LogoutButton />
    </section>
  </main>
</template>
