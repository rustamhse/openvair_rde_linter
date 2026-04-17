# Архитектурная спецификация модуля Backup

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Event Store Module Core"
description: "Mutated architectural specification for the Open vAIR event_store module."

entrypoints_layer:
  crud_adapters:
    - name: "EventCrud"
      methods:
        - "get_all_events" # ОШИБКА 16
        - "new_get_all_events_by_module"
        - "new_get_last_events"
        - "new_add_event"
        - "add_event"
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/download"
      method: "POST" # ОШИБКА 15

service_layer:
  managers:
    - name: "EventStoreManager" # ОШИБКА 17
  services:
    - name: "get_all_events"
    - name: "get_all_events_by_module"
    - name: "get_last_events"
    - name: "add_event"

adapters_layer:
  orm_models:
    - name: "Event" # ОШИБКА 18
  serializers:
    - name: "ApiSerializer"
    - name: "CreateSerializer"
    - name: "DataSerializer"
```