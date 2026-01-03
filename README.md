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

## Running Locally (No Docker)

If you don't have Docker installed, you can use the following local setup commands:

1. **One-time Setup**: Initialize the environment, install dependencies, and create an admin account (`admin`/`admin`):
   ```bash
   make local-setup
   ```

2. **Run the Server**:
   ```bash
   make local-run
   ```

3. **Access the Admin Interface**:
   - [http://localhost:8000/admin/](http://localhost:8000/admin/)

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
