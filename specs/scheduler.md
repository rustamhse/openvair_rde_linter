# Open vAIR contract: scheduler

Архитектурный контракт модуля `scheduler` для RDE-линтера.
Источник кода: `openvair/modules/scheduler`.

Машиночитаемый контракт — блок ``rde`` ниже.

```rde
meta:
  source: openvair/modules/scheduler
feature: scheduler
layers:
  adapters:
    required_classes:
    - name: Base
      methods: []
    - name: SchedulerJob
      methods: []
    - name: SqlAlchemySchedulerRepository
      methods:
      - add
      - get
      - get_all
      - update
      - delete
      - get_by_name
    - name: SchedulerJobSerializer
      methods:
      - to_web
      - to_domain
      - to_db
  domain:
    required_classes:
    - name: BaseScheduler
      methods:
      - create
      - edit
      - delete
    - name: AbstractSchedulerFactory
      methods:
      - get_scheduler
    - name: SchedulerFactory
      methods:
      - get_scheduler
    - name: CronJobScheduler
      methods:
      - create
      - edit
      - delete
    - name: SchedulerDomainException
      methods: []
    - name: CronJobNotFound
      methods: []
    - name: InvalidCronExpression
      methods: []
    - name: SchedulerDomainManager
      methods:
      - create_job
      - edit_job
      - delete_job
  entrypoints:
    required_classes:
    - name: SchedulerCRUD
      methods:
      - get_jobs
      - get_job
      - create_job
      - update_job
      - delete_job
    - name: CreateJobRequest
      methods: []
    - name: UpdateJobRequest
      methods: []
    - name: DeleteJobRequest
      methods: []
    - name: JobResponse
      methods: []
    - name: JobListResponse
      methods: []
    - name: JobStatusResponse
      methods: []
    - name: CreateJobResponse
      methods: []
    - name: ErrorResponse
      methods: []
    - name: DeleteResponse
      methods: []
    required_module_functions:
    - relative_path: entrypoints/api.py
      functions:
      - get_jobs
      - get_job
      - create_job
      - update_job
      - delete_job
    required_http_endpoints:
    - method: GET
      path: /scheduler/jobs
      handler: get_jobs
      parameters:
      - name: crud
        kind: depends
        required: true
        type_hint: SchedulerCRUD
      - name: params
        kind: depends
        required: true
        type_hint: Params
    - method: GET
      path: /scheduler/jobs/{job_id}
      handler: get_job
      parameters:
      - name: crud
        kind: depends
        required: true
        type_hint: SchedulerCRUD
      - name: job_id
        kind: query
        required: true
        type_hint: UUID
    - method: POST
      path: /scheduler/jobs
      handler: create_job
      parameters:
      - name: crud
        kind: depends
        required: true
        type_hint: SchedulerCRUD
      - name: data
        kind: body
        required: true
        type_hint: schemas.CreateJobRequest
    - method: PATCH
      path: /scheduler/jobs/{job_id}
      handler: update_job
      parameters:
      - name: crud
        kind: depends
        required: true
        type_hint: SchedulerCRUD
      - name: data
        kind: body
        required: true
        type_hint: schemas.UpdateJobRequest
      - name: job_id
        kind: query
        required: true
        type_hint: UUID
    - method: DELETE
      path: /scheduler/jobs/{job_id}
      handler: delete_job
      parameters:
      - name: crud
        kind: depends
        required: true
        type_hint: SchedulerCRUD
      - name: job_id
        kind: query
        required: true
        type_hint: UUID
      - name: data
        kind: body
        required: true
        type_hint: schemas.DeleteJobRequest
  service_layer:
    required_classes:
    - name: SchedulerService
      methods:
      - get_all_jobs
      - create_job
      - edit_job
      - delete_job
    - name: SchedulerSqlAlchemyUnitOfWork
      methods: []
    - name: SchedulerServiceLayerManager
      methods:
      - get_all_jobs_here_is_error
      - create_job
      - edit_job
      - delete_job
    - name: SchedulerServiceException
      methods: []
    - name: JobNotFoundError
      methods: []
    - name: JobAlreadyExistsError
      methods: []
    - name: InvalidJobDataError
      methods: []
    - name: JobExecutionError
      methods: []
```
