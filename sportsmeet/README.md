# Sports Meet Management System (Admin-only)

## Quickstart (Docker)

1. Create `.env` from the example:

```bash
cp .env.example .env
```

Or using Make:

```bash
make env
```

2. Build and start:

```bash
docker compose up --build
```

Or:

```bash
make up
```

3. Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Or:

```bash
make migrate
```

4. Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Or:

```bash
make superuser
```

5. Open Django Admin:

- http://localhost:8000/admin/

## Useful Make targets

```bash
make help
```

## Notes

- RBAC is enforced in Django Admin using `has_view/add/change/delete_permission`.
- Roles:
  - `ADMIN`
  - `FACULTY_COORDINATOR`
  - `STUDENT_COORDINATOR`
  - `FACULTY`
  - `STUDENT`
# sportsmeet
