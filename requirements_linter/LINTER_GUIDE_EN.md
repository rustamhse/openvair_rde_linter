# RDE Linter: Complete Practical Guide (EN)

This is a full, practical guide for your YAML contract linter in
`requirements_linter`.

What the linter does:
- reads `specs/<feature>.yaml`;
- scans Python files under `openvair/modules/<feature>/`;
- compares spec vs code using AST only (no app runtime, no tests).

---

## 1. What the linter checks

The linter validates three contract blocks per layer.

### 1.1 `required_classes`

For each class in the spec:
- class with exact name must exist in that layer;
- all listed methods must exist as public methods.

### 1.2 `required_module_functions`

For each file contract:
- `relative_path` is resolved relative to module root
  (`openvair/modules/<feature>/`);
- listed function names must be top-level callables in that file.

### 1.3 `required_http_endpoints` (optional, usually `entrypoints`)

For FastAPI routes, linter compares:
- `method`,
- `path`,
- `handler`,
- `parameters` rows with fields:
  `(name, kind, required, type_hint)`.

Important:
- matching direction is **spec -> code**;
- extra code not declared in spec is not an error;
- missing declared contract entries are errors.

---

## 2. Minimal valid YAML contract

```yaml
meta:
  source: openvair/modules/my_feature
  maintainer_notes: "RDE contract"

feature: my_feature

layers:
  domain:
    required_classes:
      - name: MyDomainService
        methods:
          - create
          - delete

  entrypoints:
    required_classes:
      - name: MyCrud
        methods:
          - get_items
    required_module_functions:
      - relative_path: entrypoints/api.py
        functions:
          - get_items
    required_http_endpoints:
      - method: GET
        path: /items
        handler: get_items
        parameters:
          - name: crud
            kind: depends
            required: true
            type_hint: MyCrud
```

---

## 3. How to write specs that pass reliably

### 3.1 Exact names only

The checker is strict:
- `SchedulerCRUD` != `SchedulerCrud`
- `update_job` != `edit_job`
- `schemas.CreateJobRequest` != `CreateJobRequest`

### 3.2 `relative_path` must be real

If function lives in:
- `openvair/modules/user/entrypoints/api.py`

then YAML must use:
- `entrypoints/api.py`

### 3.3 HTTP route matching is strict

Routes are matched by triple:
- `(METHOD, FULL_PATH, HANDLER_NAME)`.

If triple is missing:
- you get `No matching HTTP route in code ...`.

If route exists but parameters differ:
- you get `parameter contract mismatch` with both signatures printed.

### 3.4 Parameter kind inference details

In route extraction:
- `Depends(...)` -> `kind: depends`
- `Body(...)`, `Form(...)`, `File(...)` -> `kind: body`
- annotations like `schemas.Model` are usually inferred as `body`
- otherwise usually `query`

Best practice:
- generate draft spec first, then manually trim/adjust.

---

## 4. How to run the linter

## 4.1 Single module (recommended for development)

From repo root:

```bash
python requirements_linter/rde_linter.py specs/user.yaml openvair/modules/user
```

Exit codes:
- `0` - no mismatches;
- `1` - mismatches found.

### 4.2 Important default behavior

If you run without args:

```bash
python requirements_linter/rde_linter.py
```

it checks only default pair:
- `specs/storage.yaml`
- `openvair/modules/storage`

So your edited spec may not be checked unless you pass explicit paths.

### 4.3 Lint all specs

```bash
python requirements_linter/lint_repo_specs.py
```

For each `specs/*.yaml`:
- use `feature` if present;
- fallback to filename stem if `feature` is absent;
- resolve module dir as `openvair/modules/<feature>`;
- lint spec vs module.

---

## 5. Typical error messages and root causes

These are real comparator/CLI message patterns.

### 5.1 `Layer '<name>' not found under scanned sources ...`

Cause:
- no Python files discovered for this layer after filtering;
- or layer naming/path is wrong.

Fix:
- verify module folder structure and layer name;
- verify files are under recognized layers.

### 5.2 `class <Name> not found in code artifacts`

Cause:
- class name mismatch or wrong layer.

Fix:
- align class name in code/spec;
- move class to correct layer if needed.

### 5.3 `Class <Name> does not contain expected method <method>`

Cause:
- method missing or not public.

Fix:
- add method, or fix method name in YAML.

### 5.4
`File '<relative_path>' does not expose expected top-level callable ...`

Cause:
- function not top-level;
- wrong filename/path;
- wrong callable name.

### 5.5
`Module file '<relative_path>' was not scanned for functions ...`

Cause:
- file missing, filtered out, or path not under a known layer.

### 5.6 `No matching HTTP route in code for ...`

Cause:
- method/path/handler mismatch;
- route not extractable by static AST logic.

### 5.7 `parameter contract mismatch`

Cause:
- mismatch in `(name, kind, required, type_hint)` rows.

Fix:
- mirror actual handler signature exactly in YAML.

### 5.8 `required_http_endpoints must be a list`

Cause:
- wrong YAML type.

### 5.9 `required_http_endpoints entry must be a mapping`

Cause:
- one list item is not an object/map.

### 5.10
`HTTP endpoint spec must include non-empty method, path, handler`

Cause:
- one of required fields is missing/empty.

### 5.11
`Spec layer=... uses disallowed class name '$module_functions$' ...`

Cause:
- reserved internal sentinel name used as class contract name.

### 5.12
`skip — bounded context directory missing (openvair/modules/<feature>)`

Cause:
- spec points to module folder that does not exist.

---

## 6. FastAPI extraction limitations (important)

Supported (MVP):
- `router = APIRouter(prefix="...")` with literal prefix;
- decorators like `@router.get("/path")` with literal path;
- top-level handlers.

Not reliably supported:
- dynamic prefix/path construction;
- route wrappers/metaprogramming;
- deriving contract via `include_router(...)`;
- non-literal route definitions.

---

## 7. Recommended workflow

1) Generate draft spec:

```bash
python requirements_linter/generate_openvair_specs.py --feature my_feature
```

2) Trim draft to public contract only.

3) Validate one module repeatedly:

```bash
python requirements_linter/rde_linter.py specs/my_feature.yaml openvair/modules/my_feature
```

4) Fix mismatches.

5) Validate all specs:

```bash
python requirements_linter/lint_repo_specs.py
```

---

## 8. Quick FAQ

### "Why route exists but linter still fails?"

Most often:
- handler name mismatch;
- inferred `kind` mismatch (`query` vs `body`);
- `type_hint` mismatch;
- route prefix/path normalized differently.

### "Why does linter miss my layer?"

Check:
- files are `.py`;
- files are under recognized layer folder;
- symbols are public names.

### "Safest way to update spec after refactor?"

Regenerate first, then manually simplify.

---

## 9. Command cheat sheet

```bash
# Single module
python requirements_linter/rde_linter.py specs/user.yaml openvair/modules/user

# All specs
python requirements_linter/lint_repo_specs.py

# Generate draft
python requirements_linter/generate_openvair_specs.py --feature user

# Linter tests
python -m pytest requirements_linter/tests -v --override-ini addopts=
```

---

If you want, next step can be adding module-specific spec templates
(for CRUD API modules, worker modules, etc.) so writing new specs is mostly
copy/adapt instead of starting from scratch.
