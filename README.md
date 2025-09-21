# Carbon Credit Ledger API

This is a FastAPI-based service for tracking the lifecycle of carbon credits, from creation to retirement, using an event-sourcing pattern.

## Project Setup and Running with Docker

Follow these instructions to build and run the application and its database using Docker.


### Instructions

1.  **Clone the Repository**

    ```bash
    git clone <your-repository-url>
    cd backend
    ```

2.  **Configure Environment Variables**

    The application uses a `docker-compose.yml` file which defines the services. You may need to create or verify a `.env` file in the `d:/backend/` directory for database configuration if your setup requires it. A typical configuration would look like this:

    ```env
    # d:/backend/.env
    POSTGRES_USER=user
    POSTGRES_PASSWORD=password
    POSTGRES_DB=carbon_credits
    ```

3.  **Build and Run the Containers**

    From the `d:/backend/` directory, run the following command:

    ```bash
    docker-compose up --build -d
    ```

    This command will:
    -   Build the Docker image for the FastAPI application.
    -   Pull the official PostgreSQL image.
    -   Start both containers and connect them on a shared network.
    -   The `-d` flag runs the containers in detached mode.

4.  **Accessing the API**

    -   The API will be available at `http://localhost:8000`.
    -   Interactive API documentation (Swagger UI) can be accessed at `http://localhost:8000/docs`.

---

## Reflection Questions

### How did you design the ID so it’s always the same for the same input?

The current design does not generate the same ID for the same input. Instead, it uses a standard database-driven approach for ensuring unique record identification.

The `Record.id` column is defined as an `Integer` primary key:
```python
# d:\backend\backend\models\table.py
id = Column(Integer, primary_key=True, index=True)
```
When a new record is inserted, the PostgreSQL database automatically assigns a new, unique, and sequentially increasing integer. This guarantees that every record is unique, but it means that creating two records with identical data (e.g., same `project_name`, `quantity`, etc.) will result in two distinct records with different IDs.

If the requirement were to have a deterministic ID based on the input, one would typically use a hashing algorithm (e.g., SHA-256) on a concatenated string of the input fields that define uniqueness. However, this approach was not used here in favor of the simplicity and performance of auto-incrementing integers.

### Why did you use an event log instead of updating the record directly?

Using an event log (`events` table) instead of directly mutating a record's state is a pattern known as **Event Sourcing**. This design was chosen for several key reasons:

1.  Every change to a record is captured as an immutable `Event` (e.g., "created", "retired"). This provides a complete, chronological history of the asset, which is critical for auditing, compliance, and traceability in a system managing valuable assets like carbon credits.

2. The current state of any record can be reconstructed at any point in time by replaying its events. This is invaluable for debugging and understanding how a record reached a certain state.

### If two people tried to retire the same credit at the same time, what would break? How would you fix it?

This scenario describes a classic **race condition**. Without a proper locking mechanism, the system's integrity would be compromised.

**What Would Break (Without a Fix):**
1.  **Request A** fetches the record. It sees no "retired" event.
2.  **Request B** fetches the same record just after. It also sees no "retired" event.
3.  Request A creates a "retired" event and commits the transaction. The credit is now retired.
4.  Request B, unaware of Request A's action, also creates a "retired" event and commits its transaction.

The result is that the same carbon credit is retired twice, leading to two "retired" events in the log for a single credit. This corrupts the data and violates the fundamental business rule that a credit can only be retired once.

**How It Is Fixed in This Code:**

The issue is already solved in the `retire_record` function by using a **pessimistic lock**.

```python
# d:\backend\backend\routes\recordRoute.py
record = db.query(Record).filter(Record.id == record_id).with_for_update().first()
```

The `.with_for_update()` method tells SQLAlchemy to issue a `SELECT ... FOR UPDATE` SQL statement. This instructs the database to lock the row(s) matching the query for the duration of the transaction.

1.  **Request A**'s transaction starts and executes the `SELECT ... FOR UPDATE`, locking the record's row in the database.
2.  **Request B**'s transaction attempts the same query but is forced to wait because the row is locked by Request A.
3.  Request A checks for a "retired" event (finds none), adds a new one, and commits. The transaction ends, and the lock is released.
4.  **Request B**'s query now executes. It fetches the record, which *now includes the "retired" event* created by Request A.
5.  Request B's check `if any(e.event_type == "retired" for e in record.events)` evaluates to `True`, and it correctly raises an `HTTPException` for an already retired record.

This mechanism ensures atomicity and prevents the race condition, guaranteeing that only the first request can successfully retire the credit.