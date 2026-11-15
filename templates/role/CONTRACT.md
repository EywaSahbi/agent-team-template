# <role>/ contract (v0 — owner `<login>`)

What this folder publishes for other roles. Consumers build against this file, not against the code.
Consumers: <roles>.
Changes: additive → `CONTRACT` message to the consumers and lead. Breaking → the consumers `ACK` first; after M1 it is a human `DECISION`.

## Interface

<!-- Pick what applies; delete the rest. Write types once and reuse the names. -->

**HTTP** on `http://localhost:<port>`:

```ts
type Thing = {
  id: string;
  // every field: type, unit, range, and what it means
};
```

| Method + path | Request | Response | Errors |
|---|---|---|---|
| `GET /health` | | `{ "ok": true }` | |
| `POST /<things>` | `Thing` without `id` | `Thing` | `422` invalid input |

**Files** under `<role>/<path>/`: <format, schema, naming rule, who writes them, who reads them>.

## Guarantees

<What is always true: validation, units, ordering, determinism, latency, what happens when a dependency is down.>

## Run it / mock it

```bash
cd <role> && <run>      # the real thing
```

Before it lands: <stub or mock consumers can use, e.g. a fixture file or a canned response>.

## Changelog

- v0 (<date>): first draft.
