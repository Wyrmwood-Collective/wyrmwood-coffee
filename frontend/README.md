
## Run the demo

1. Start the API (from the project root):

   ```shell
   uv run dev
   ```

2. Open the app in your browser:

   ```
   http://127.0.0.1:8000/app/
   ```

The UI is served from the same origin as the API, so you do not need CORS or a
second dev server.

## Role permissions (frontend only)

The UI reads `role` from the JWT after login. These rules are **not enforced by
the API yet** — they only control what each user sees in the browser.

| Action | Employee | Manager | Admin |
| --- | --- | --- | --- |
| View own profile | Yes | Yes | Yes |
| List team roster | No | Yes | Yes |
| View any employee detail | No | Yes | Yes |
| See hourly rates in roster | No | No | Yes |
| Create employee | No | No | Yes |
| Delete employee | No | No | Yes* |
| Update employee | No | No | Soon* |

\* Delete calls `DELETE /employees/{id}` when you click delete — it will show a
friendly message until the backend adds that endpoint. Update is noted in the UI
for when `PUT /employees/{id}` exists.

## Pages

| File | Who can open it | Purpose |
| --- | --- | --- |
| `index.html` | Everyone (logged out) | Login |
| `dashboard.html` | All logged-in roles | Own profile |
| `employees.html` | Manager, admin | Team roster |
| `signup.html` | Admin only | Create employee |

If you open a page you are not allowed to use, you are redirected to the
dashboard.

## API calls used

| Page | Endpoint | Notes |
| --- | --- | --- |
| Login | `POST /auth/login` | Form-encoded `username` + `password` |
| Create | `POST /employees` | Full `EmployeeCreate` JSON |
| Roster | `GET /employees` | List all employees |
| Profile / detail | `GET /employees/{id}` | Single employee |
| Delete (admin) | `DELETE /employees/{id}` | UI only until API exists |

## Editing tips

- Permission rules live at the top of `js/auth.js` in the `PERMISSIONS` object.
- Add a nav link in `mountAppChrome()` when you add a new page.
- Change colors → CSS variables at the top of `css/style.css`.
