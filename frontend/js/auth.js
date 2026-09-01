/**
 * Wyrmwood Coffee showcase UI — login, role-based employee views.
 *
 * Each page sets data-page on <body>. Role comes from the JWT payload after login.
 * Permissions are enforced in the browser only (demo); the API does not check roles yet.
 */

const TOKEN_KEY = "wyrmwood_access_token";

/** What each role may do in this UI (frontend-only rules). */
const PERMISSIONS = {
  viewOwnProfile: ["employee", "manager", "admin"],
  listEmployees: ["manager", "admin"],
  viewAnyEmployee: ["manager", "admin"],
  createEmployee: ["admin"],
  updateEmployee: ["admin"],
  deleteEmployee: ["admin"],
};

// --- Token & session ---

function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
}

function parseJwtPayload(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

function getSession() {
  const token = getToken();
  if (!token) {
    return null;
  }
  const payload = parseJwtPayload(token);
  if (!payload?.sub || !payload?.role) {
    return null;
  }
  return {
    token,
    employeeId: String(payload.sub),
    role: payload.role,
  };
}

function can(action) {
  const session = getSession();
  if (!session) {
    return false;
  }
  return PERMISSIONS[action]?.includes(session.role) ?? false;
}

function requireLogin(redirectTo = "index.html") {
  if (!getSession()) {
    window.location.href = redirectTo;
    return null;
  }
  return getSession();
}

function requirePermission(action, redirectTo = "dashboard.html") {
  const session = requireLogin();
  if (!session) {
    return null;
  }
  if (!can(action)) {
    window.location.href = redirectTo;
    return null;
  }
  return session;
}

function authHeaders(contentType = "application/json") {
  const headers = {};
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  return headers;
}

function logout() {
  clearToken();
  window.location.href = "index.html";
}

function formatRoleLabel(role) {
  if (role === "admin") return "Admin";
  if (role === "manager") return "Manager";
  return "Employee";
}

// --- API helpers ---

function formatApiError(data) {
  if (!data) {
    return "Something went wrong. Please try again.";
  }
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(" ");
  }
  return "Something went wrong. Please try again.";
}

async function apiLogin(username, password) {
  const body = new URLSearchParams();
  body.set("username", username);
  body.set("password", password);

  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatApiError(data));
  }
  return data;
}

async function apiListEmployees() {
  const response = await fetch("/employees", { headers: authHeaders(null) });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatApiError(data));
  }
  return data;
}

async function apiGetEmployee(id) {
  const response = await fetch(`/employees/${id}`, { headers: authHeaders(null) });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatApiError(data));
  }
  return data;
}

async function apiCreateEmployee(payload) {
  const response = await fetch("/employees", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatApiError(data));
  }
  return data;
}

async function apiDeleteEmployee(id) {
  const response = await fetch(`/employees/${id}`, {
    method: "DELETE",
    headers: authHeaders(null),
  });

  if (response.ok) {
    return;
  }

  const data = await response.json().catch(() => null);
  if (response.status === 404 || response.status === 405) {
    throw new Error(
      "Delete is not available yet — the API needs a DELETE /employees/{id} endpoint."
    );
  }
  throw new Error(formatApiError(data));
}

// --- Validation (matches API EmployeeCreate) ---

const PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{};':\"\\|,.<>/?`~";

function validatePassword(password) {
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
    `[${PASSWORD_SPECIAL_CHARS.replace(/[\\^$.*+?()[\]{}|]/g, "\\$&")}]`
  );
  if (!specialPattern.test(password)) {
    return "Password must include at least one special character.";
  }
  return null;
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function validateHourlyRate(value) {
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

// --- UI helpers ---

function showMessage(element, text, type) {
  element.hidden = false;
  element.textContent = text;
  element.className = `message message-${type}`;
}

function hideMessage(element) {
  element.hidden = true;
  element.textContent = "";
}

function setFormLoading(form, isLoading) {
  const submit = form.querySelector("[type='submit']");
  if (submit) {
    submit.disabled = isLoading;
    submit.textContent = isLoading ? "Please wait…" : submit.dataset.label;
  }
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderProfileList(employee, viewerRole, options = {}) {
  const { limited = false } = options;
  const rows = [
    ["Name", `${employee.first_name} ${employee.last_name}`],
    ["Username", employee.username],
    ["Role", employee.role],
  ];

  if (!limited) {
    rows.push(
      ["Status", employee.active ? "Active" : "Inactive"],
      ["Hourly rate", `$${employee.hourly_rate}`],
      ["Employee ID", employee.id],
      ["Hire date", employee.hire_date],
      ["Termination date", employee.term_date ?? "—"]
    );
  } else {
    rows.push(["Hire date", employee.hire_date]);
  }

  return rows
    .map(
      ([label, value]) =>
        `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></li>`
    )
    .join("");
}

function mountAppChrome(session) {
  const nav = document.getElementById("app-nav");
  const badge = document.getElementById("role-badge");
  if (!nav || !badge) {
    return;
  }

  badge.textContent = formatRoleLabel(session.role);
  badge.className = `role-badge role-badge-${session.role}`;

  const links = [{ href: "dashboard.html", label: "My profile" }];

  if (can("listEmployees")) {
    links.push({ href: "employees.html", label: "Team roster" });
  }
  if (can("createEmployee")) {
    links.push({ href: "signup.html", label: "Create employee" });
  }

  nav.innerHTML = links
    .map((link) => `<a class="nav-link" href="${link.href}">${link.label}</a>`)
    .join("");

  const logoutButton = document.getElementById("logout-button");
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }
}

// --- Login page ---

function initLogin() {
  if (getSession()) {
    window.location.href = "dashboard.html";
    return;
  }

  const form = document.getElementById("login-form");
  const message = document.getElementById("form-message");
  const submit = form.querySelector("[type='submit']");
  submit.dataset.label = submit.textContent;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage(message);

    const username = form.username.value.trim();
    const password = form.password.value;

    if (!username || !password) {
      showMessage(message, "Enter both username and password.", "error");
      return;
    }

    setFormLoading(form, true);

    try {
      const result = await apiLogin(username, password);
      setToken(result.access_token);
      window.location.href = "dashboard.html";
    } catch (error) {
      showMessage(message, error.message, "error");
    } finally {
      setFormLoading(form, false);
    }
  });
}

// --- Create employee (admin only) ---

function initSignup() {
  const session = requirePermission("createEmployee");
  if (!session) {
    return;
  }

  mountAppChrome(session);

  const form = document.getElementById("signup-form");
  const message = document.getElementById("form-message");
  const submit = form.querySelector("[type='submit']");
  submit.dataset.label = submit.textContent;

  if (!form.hire_date.value) {
    form.hire_date.value = todayIsoDate();
  }
  if (!form.hourly_rate.value) {
    form.hourly_rate.value = "15.00";
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    hideMessage(message);

    const firstName = form.first_name.value.trim();
    const lastName = form.last_name.value.trim();
    const username = form.username.value.trim();
    const password = form.password.value;
    const confirmPassword = form.confirm_password.value;
    const role = form.role.value;
    const hourlyRate = form.hourly_rate.value.trim();
    const hireDate = form.hire_date.value;
    const termDate = form.term_date.value;
    const active = form.active.checked;

    if (
      !firstName ||
      !lastName ||
      !username ||
      !password ||
      !role ||
      !hourlyRate ||
      !hireDate
    ) {
      showMessage(message, "Fill in all required fields.", "error");
      return;
    }

    if (password !== confirmPassword) {
      showMessage(message, "Passwords do not match.", "error");
      return;
    }

    const passwordError = validatePassword(password);
    if (passwordError) {
      showMessage(message, passwordError, "error");
      return;
    }

    const hourlyRateError = validateHourlyRate(hourlyRate);
    if (hourlyRateError) {
      showMessage(message, hourlyRateError, "error");
      return;
    }

    if (termDate && termDate <= hireDate) {
      showMessage(message, "Termination date must be after hire date.", "error");
      return;
    }

    setFormLoading(form, true);

    const payload = {
      first_name: firstName,
      last_name: lastName,
      username,
      password,
      role,
      hourly_rate: hourlyRate,
      hire_date: hireDate,
      active,
    };

    if (termDate) {
      payload.term_date = termDate;
    }

    try {
      await apiCreateEmployee(payload);

      showMessage(message, "Employee created successfully.", "success");
      form.reset();
      form.hire_date.value = todayIsoDate();
      form.hourly_rate.value = "15.00";
      form.active.checked = true;

      setTimeout(() => {
        window.location.href = "employees.html";
      }, 1200);
    } catch (error) {
      showMessage(message, error.message, "error");
    } finally {
      setFormLoading(form, false);
    }
  });
}

// --- Dashboard (own profile) ---

function initDashboard() {
  const session = requireLogin();
  if (!session) {
    return;
  }

  mountAppChrome(session);

  const message = document.getElementById("form-message");
  const welcome = document.getElementById("welcome-text");
  const profileList = document.getElementById("profile-list");
  const accessNote = document.getElementById("access-note");

  if (accessNote) {
    const notes = {
      employee: "You can view your own profile only.",
      manager: "You can view the team roster. Creating or removing employees requires an admin.",
      admin: "You have full employee management access in this demo UI.",
    };
    accessNote.textContent = notes[session.role] ?? "";
  }

  apiGetEmployee(session.employeeId)
    .then((employee) => {
      welcome.textContent = `Welcome, ${employee.first_name}!`;
      const limited = session.role === "employee";
      profileList.innerHTML = renderProfileList(employee, session.role, { limited });
    })
    .catch((error) => {
      welcome.textContent = "Welcome back!";
      showMessage(message, error.message, "error");
    });
}

// --- Team roster (manager + admin) ---

function initEmployees() {
  const session = requirePermission("listEmployees");
  if (!session) {
    return;
  }

  mountAppChrome(session);

  const message = document.getElementById("form-message");
  const tableBody = document.getElementById("employees-table-body");
  const detailPanel = document.getElementById("employee-detail");
  const detailList = document.getElementById("employee-detail-list");
  const detailTitle = document.getElementById("employee-detail-title");
  const createLink = document.getElementById("create-employee-link");
  const rosterNote = document.getElementById("roster-note");

  if (createLink) {
    createLink.hidden = !can("createEmployee");
  }

  if (rosterNote) {
    rosterNote.textContent =
      session.role === "admin"
        ? "Admins can create and delete employees (delete requires a future API endpoint)."
        : "Managers can browse the roster but cannot create or remove employees.";
  }

  let employees = [];

  function showEmployeeDetail(employee) {
    detailPanel.hidden = false;
    detailTitle.textContent = `${employee.first_name} ${employee.last_name}`;
    detailList.innerHTML = renderProfileList(employee, session.role);

    const actions = document.getElementById("employee-detail-actions");
    if (actions) {
      actions.innerHTML = "";

      if (can("deleteEmployee")) {
        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "btn btn-danger btn-inline";
        deleteButton.textContent = "Delete employee";
        deleteButton.addEventListener("click", async () => {
          const name = `${employee.first_name} ${employee.last_name}`;
          if (!window.confirm(`Delete ${name}? This cannot be undone.`)) {
            return;
          }
          hideMessage(message);
          deleteButton.disabled = true;
          try {
            await apiDeleteEmployee(employee.id);
            detailPanel.hidden = true;
            employees = employees.filter((row) => row.id !== employee.id);
            renderTable();
            showMessage(message, `${name} was deleted.`, "success");
          } catch (error) {
            showMessage(message, error.message, "error");
          } finally {
            deleteButton.disabled = false;
          }
        });
        actions.appendChild(deleteButton);
      }

      if (can("updateEmployee")) {
        const editNote = document.createElement("p");
        editNote.className = "hint";
        editNote.textContent =
          "Update will be available when the API adds PUT /employees/{id}.";
        actions.appendChild(editNote);
      }
    }
  }

  function renderTable() {
    const showRate = session.role === "admin";

    tableBody.innerHTML = employees
      .map((employee) => {
        const rateCell = showRate
          ? `<td>$${escapeHtml(employee.hourly_rate)}</td>`
          : "";
        const actionCell = `<td><button type="button" class="btn-text" data-action="view" data-id="${employee.id}">View</button></td>`;

        return `
          <tr>
            <td>${escapeHtml(employee.first_name)} ${escapeHtml(employee.last_name)}</td>
            <td>${escapeHtml(employee.username)}</td>
            <td>${escapeHtml(employee.role)}</td>
            <td>${employee.active ? "Active" : "Inactive"}</td>
            ${rateCell}
            ${actionCell}
          </tr>
        `;
      })
      .join("");

    tableBody.querySelectorAll("[data-action='view']").forEach((button) => {
      button.addEventListener("click", () => {
        const id = button.dataset.id;
        const employee = employees.find((row) => String(row.id) === id);
        if (employee) {
          showEmployeeDetail(employee);
        }
      });
    });
  }

  const rateHeader = document.getElementById("rate-header");
  if (rateHeader) {
    rateHeader.hidden = session.role !== "admin";
  }

  apiListEmployees()
    .then((data) => {
      employees = data;
      renderTable();
    })
    .catch((error) => {
      showMessage(message, error.message, "error");
    });
}

// --- Boot ---

document.addEventListener("DOMContentLoaded", () => {
  const page = document.body.dataset.page;

  if (page === "login") {
    initLogin();
  } else if (page === "signup") {
    initSignup();
  } else if (page === "dashboard") {
    initDashboard();
  } else if (page === "employees") {
    initEmployees();
  }
});
