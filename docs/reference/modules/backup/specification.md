# Архитектурная спецификация модуля Backup

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Backup Module Core"
description: "Baseline architectural specification for the Open vAIR backup module."

entrypoints_layer:
  crud_adapters:
    - name: "BackupCrud"
      methods:
        - "create_backup"
        - "restore_backup"
        - "get_snapshots"
        - "initialize_backup_repository"
        - "delete_snapshot"
  endpoints:
    - path: "/"
      method: "POST"
    - path: "/restore"
      method: "POST"
    - path: "/"
      method: "GET"
    - path: "/repository"
      method: "POST"
    - path: "/{snapshot_id}"
      method: "DELETE"

domain_layer:
  models:
    - name: "AbstractBackuperFactory"
    - name: "BackuperFactory"

service_layer:
  managers:
    - name: "BackupServiceLayerManager"
  services:
    - name: "create_backup"
    - name: "delete_snapshot"
    - name: "restore_backup"
    - name: "get_snapshots"
    - name: "initialize_backup_repository"
```