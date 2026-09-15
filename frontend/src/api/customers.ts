import { apiFetch } from "./client";
import type { CustomerRead } from "@/types/customer";

export function apiListCustomers(): Promise<CustomerRead[]> {
  return apiFetch<CustomerRead[]>("/customers", {}, { contentType: null });
}

export type CustomerLookup = {
  phone?: string;
  email?: string;
};

export type CustomerLookupResult =
  { ok: true; customer: CustomerRead; notice?: string } | { ok: false; error: string };

const PHONE_PATTERN = /^\d{3}-\d{3}-\d{4}$/;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function customerName(customer: CustomerRead): string {
  return `${customer.first_name} ${customer.last_name}`;
}

function findActiveByPhone(customers: CustomerRead[], phone: string): CustomerRead | undefined {
  return customers.find((customer) => customer.active && customer.phone === phone);
}

function findActiveByEmail(customers: CustomerRead[], email: string): CustomerRead | undefined {
  const normalized = email.toLowerCase();
  return customers.find(
    (customer) => customer.active && (customer.email?.toLowerCase() ?? "") === normalized,
  );
}

/**
 * Resolve an active customer from phone and/or email.
 *
 * - Uses whichever field is valid when the other is blank or malformed.
 * - If both are valid and point at different people, returns a conflict error.
 * - If both are valid and only one matches, uses the match and notes the miss.
 */
export function resolveActiveCustomer(
  customers: CustomerRead[],
  lookup: CustomerLookup,
): CustomerLookupResult {
  const rawPhone = lookup.phone?.trim() ?? "";
  const rawEmail = lookup.email?.trim() ?? "";

  if (!rawPhone && !rawEmail) {
    return { ok: false, error: "Enter a phone number or an email address." };
  }

  const phoneValid = rawPhone !== "" && PHONE_PATTERN.test(rawPhone);
  const emailValid = rawEmail !== "" && EMAIL_PATTERN.test(rawEmail);
  const phoneMalformed = rawPhone !== "" && !phoneValid;
  const emailMalformed = rawEmail !== "" && !emailValid;

  if (phoneMalformed && !rawEmail) {
    return { ok: false, error: "Enter a phone number as XXX-XXX-XXXX." };
  }
  if (emailMalformed && !rawPhone) {
    return { ok: false, error: "Enter a valid email address." };
  }
  if (phoneMalformed && emailMalformed) {
    return {
      ok: false,
      error: "Phone must be XXX-XXX-XXXX and email must be a valid address.",
    };
  }

  // One field malformed: fall back to the valid one.
  if (phoneMalformed && emailValid) {
    const byEmail = findActiveByEmail(customers, rawEmail);
    if (!byEmail) {
      return {
        ok: false,
        error: "No active customer found for that email. Phone was ignored (invalid format).",
      };
    }
    return {
      ok: true,
      customer: byEmail,
      notice: "Phone was ignored because it was not XXX-XXX-XXXX. Matched by email.",
    };
  }

  if (emailMalformed && phoneValid) {
    const byPhone = findActiveByPhone(customers, rawPhone);
    if (!byPhone) {
      return {
        ok: false,
        error: "No active customer found for that phone. Email was ignored (invalid format).",
      };
    }
    return {
      ok: true,
      customer: byPhone,
      notice: "Email was ignored because it was not a valid address. Matched by phone.",
    };
  }

  const byPhone = phoneValid ? findActiveByPhone(customers, rawPhone) : undefined;
  const byEmail = emailValid ? findActiveByEmail(customers, rawEmail) : undefined;

  if (phoneValid && emailValid) {
    if (byPhone && byEmail && byPhone.id !== byEmail.id) {
      return {
        ok: false,
        error:
          `Phone and email belong to different customers: ` +
          `#${byPhone.id} ${customerName(byPhone)} (phone) vs ` +
          `#${byEmail.id} ${customerName(byEmail)} (email). ` +
          `Search with only one field.`,
      };
    }
    if (byPhone && byEmail) {
      return { ok: true, customer: byPhone };
    }
    if (byPhone && !byEmail) {
      return {
        ok: true,
        customer: byPhone,
        notice: "Email did not match an active customer. Showing results for the phone match.",
      };
    }
    if (!byPhone && byEmail) {
      return {
        ok: true,
        customer: byEmail,
        notice: "Phone did not match an active customer. Showing results for the email match.",
      };
    }
    return {
      ok: false,
      error: "No active customer found for that phone or email.",
    };
  }

  if (phoneValid) {
    if (!byPhone) {
      return { ok: false, error: "No active customer found for that phone number." };
    }
    return { ok: true, customer: byPhone };
  }

  if (!byEmail) {
    return { ok: false, error: "No active customer found for that email." };
  }
  return { ok: true, customer: byEmail };
}
