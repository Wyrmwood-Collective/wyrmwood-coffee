# Configuration and secrets (start here if you are new to `.env` files)

**The one rule:** git may contain the *names* of our settings. It must never contain
the *values* of passwords, database logins, or signing keys.

| File or place | Goes in git? | Has real passwords? | What it is |
| --- | --- | --- | --- |
| `.env.example` | Yes | No — fake placeholders only | A cheat sheet of every setting the app needs |
| `.env.local` | No | Yes — your machine only | Your personal copy, filled in with real local values |
| The computer that runs the app (your laptop, GitHub Actions, or staging) | Nothing to commit | Yes, but they live *outside* git | Environment variables the operating system hands to Python |

If a teammate asks “which one is safe to commit?”, the answer is **only
`.env.example`**.

---

## What is an environment variable?

Python does not have to hard-code a database password in a `.py` file. At
startup it can ask the operating system: “what is `DEV_DATABASE_URL`?” That
answer is an **environment variable** — a named value that lives *around* the
program, not inside it.

That is useful because:

- Your laptop, GitHub Actions, and staging can each use a different database
  without changing the code.
- The password never has to sit in a file that git will copy to GitHub.

## What is a `.env` file?

Typing `set DEV_DATABASE_URL=...` in a terminal every time is annoying. A
`.env` file is a plain text list of `NAME=value` lines. When the app starts,
[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
reads that file and treats those lines as environment variables.

We use two files with the same *shape* and different *jobs*:

1. **`.env.example`** — checked into git on purpose. It shows *which* names
   exist. The values are obviously fake (`USER:PASSWORD`,
   `change-me-must-be-at-least-32-characters`) so nobody copies a real secret
   into GitHub.
2. **`.env.local`** — you create this on your laptop by copying `.env.example`
   and replacing the fakes with your real local Postgres login and a random
   JWT key. Git is told to ignore it (see `.gitignore`), so `git add .` will
   not upload it.

An older filename, `.env`, is also ignored and still loaded if you already
have one. Prefer `.env.local`. If both exist, `.env.local` wins.

**Why not put the real password in `.env.example`?** Git keeps every old
version forever. Deleting the line later does not erase it from history.
Anyone with repo access (or a leaked clone) could still read it.

---

## Set up your laptop

1. Copy the template:

   ```shell
   copy .env.example .env.local
   ```

   (On macOS/Linux: `cp .env.example .env.local`.)

2. In `.env.local`, replace `USER` and `PASSWORD` in `DEV_DATABASE_URL` and
   `TEST_DATABASE_URL` with the Postgres username and password on *your*
   machine. You do not need a real `STAGING_DATABASE_URL` locally unless you
   are testing against staging.

3. Replace `JWT_SECRET_KEY` with a random string at least 32 characters long.
   You do not need to invent one by hand:

   ```shell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Paste the printed value after `JWT_SECRET_KEY=`. Each developer can have a
   different key; that is expected.

4. Run `uv run dev`. If something required is missing or you left a
   placeholder in place, the app **stops immediately** and prints the name of
   the setting. That is intentional — better a clear crash than a half-working
   server.

---

## Three environments, three database URLs

`APP_ENVIRONMENT` picks which database URL the app uses:

| `APP_ENVIRONMENT` | Database setting used | Typical use |
| --- | --- | --- |
| `dev` | `DEV_DATABASE_URL` | Your laptop. Local Postgres on `localhost`. |
| `test` | `TEST_DATABASE_URL` | `pytest` and GitHub Actions. Disposable test database. |
| `staging` | `STAGING_DATABASE_URL` | The deployed API. Real hosted Postgres, not localhost. |

On your laptop, keep `APP_ENVIRONMENT=dev` and fill in `DEV_DATABASE_URL`.

When the API is deployed to staging, the host sets `APP_ENVIRONMENT=staging`
and `STAGING_DATABASE_URL` as environment variables. Do **not** copy
`.env.local` onto that server and do **not** put the staging connection
string in this repo.

**CI today:** `.github/workflows/ci.yml` sets `APP_ENVIRONMENT=test`,
`TEST_DATABASE_URL`, and `JWT_SECRET_KEY` for a throwaway Postgres container.
Those values are not staging secrets.

---

## Every setting, in plain language

These names must appear in `.env.example`. The database URLs and JWT key are
secrets.

| Name | Secret? | Why it exists | If the real value leaked |
| --- | --- | --- | --- |
| `DEV_DATABASE_URL` | Yes | Local Postgres on your laptop when `APP_ENVIRONMENT=dev`. | Someone could read or change data on your local database. Rotate the password if you reuse it elsewhere. |
| `TEST_DATABASE_URL` | Yes | Postgres for pytest / CI when `APP_ENVIRONMENT=test`. | Usually only test data. Still rotate if you reused the password elsewhere. Never reuse the staging password here. |
| `STAGING_DATABASE_URL` | Yes | Hosted Postgres when `APP_ENVIRONMENT=staging`. | Attacker could read or change staging data (customers, employees, vendors, etc.). Rotate the database password and treat staging data as possibly accessed. |
| `JWT_SECRET_KEY` | Yes | Private string used to sign login tokens. | Attacker could mint tokens and pretend to be any employee until the key is rotated. Everyone must log in again after rotation. |
| `APP_ENVIRONMENT` | No | Switches between `dev`, `test`, and `staging`. | Not a password. Wrong values make the app connect to the wrong database. |
| `JWT_ALGORITHM` | No | Signing method (`HS256`). Leave unless the team changes it. | Not a secret. |
| `JWT_EXPIRATION_MINUTES` | No | How long login tokens stay valid (default `30`). | Not a secret. |

---

## How we stop a later sprint from putting secrets back in git

A written rule is easy to forget. These checks fail the PR instead:

1. Git ignores `.env` and `.env.local`, so they should not show up in `git add`.
2. The app will not start if a secret is missing or still looks like the
   example placeholder.
3. Tests in `test/test_settings.py` fail CI if those env files are tracked, or
   if `.env.example` is missing a required name, or if `JWT_SECRET_KEY` gets a
   default baked into Python.
4. **Gitleaks** (a secret scanner) runs in GitHub Actions and fails the build
   if a password-like string is in the project files.
5. The PR checklist asks you to confirm you did not commit `.env.local`.

If you add a new secret: give it **no default** in `settings.py`, add a fake
value to `.env.example`, and add a row to the table above.

---

## Decision: we will not rewrite git history

We looked through past commits. Nobody committed a real database password.
`.env.example` only ever had placeholders. `.env` / `.env.local` were never
tracked.

Rewriting history would make every teammate re-clone for no benefit. **Do not
rewrite history for WC-51.**

If someone *does* commit a real secret later: change that password/key the
same day (the leak is already in git). History cleanup is a separate, painful
follow-up — it does not undo the leak by itself.
