# Wyrmwood Collective Coffee Shop API

- [Group Jira](https://catalystit.atlassian.net/jira/software/projects/WC/summary)
- [Group Confluence](https://catalystit.atlassian.net/wiki/spaces/WC1/overview)

## Development Setup

Install `uv` and clone the repository:

```shell
winget -e --id=astral-sh.uv
git clone git@github.com:bverble-catalyte/wyrmwood-coffee.git
```

Copy the example environment file and fill in your local values (database URLs, JWT secret, etc.):

```shell
cp .env.example .env
```

Run the development server:

```shell
uv run dev
```

Run test suite:

```shell
uv run pytest
```
## Hosted PostgreSQL Database

The development database is hosted on Neon PostgreSQL.

- Provider: Neon
- Project: Wyrmwood-Collective Coffee API
- Branch: production
- Database: wyrmwood_collective
- Port: 5432
- SSL: Required
- Environment variable: DEV_DATABASE_URL

Connection credentials are stored locally in the `.env` file and must not be committed to source control.

Example:

```
APP_ENVIRONMENT=dev
STAGING_DATABASE_URL=postgresql://<user>:<password>@ep-divine-rain-axt5p0um-pooler.c-4.us-east-2.aws.neon.tech/wyrmwood_collective?sslmode=require&channel_binding=require
DEV_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/wyrmwood_coffee
TEST_DATABASE_URL=postgresql+psycopg://postgres:<password>@localhost:5432/wyrmwood_coffee_test
JWT_SECRET_KEY= replace-me-with-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30
```

Team members should retrieve the current database credentials through the approved team credential-sharing method rather than placing passwords in GitHub, Jira, or documentation.
