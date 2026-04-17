# Архитектурная спецификация модуля Storage

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Storage Module Core"
description: "Mutated architectural specification for the Open vAIR storage module."

entrypoints_layer:
  crud_adapters:
    - name: "StorageCrud"
      methods:
        - "get_storage"
        - "get_all_storages"
        - "create_storage"
        - "delete_storage"
        - "get_local_disks"
        - "create_local_partition"
        - "get_local_disk_partitions_info"
        - "delete_local_partition"
        - "format_disk" # ОШИБКА 7
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/local-disks/"
      method: "GET"
    - path: "/local-disks/create_partition/"
      method: "POST"
    - path: "/local-disks/partition_info/"
      method: "GET"
    - path: "/local-disks/delete_partition/"
      method: "DELETE"
    - path: "/{storage_id}/"
      method: "GET"
    - path: "/add/" # ОШИБКА 6
      method: "POST"
    - path: "/{storage_id}/delete/"
      method: "DELETE"

domain_layer:
  models:
    - name: "AbstractStorageFactory"
    - name: "StorageBuilder" # ОШИБКА 8

service_layer:
  managers:
    - name: "StorageServiceLayerManager"
  services:
    - name: "get_storage"
    - name: "get_all_storages"
    - name: "create_local_partition"
    - name: "get_local_disk_partitions_info"
    - name: "remove_local_partition" # ОШИБКА 9
    - name: "create_storage"
    - name: "delete_storage"
    - name: "get_local_disks"
    - name: "monitoring"

adapters_layer:
  orm_models:
    - name: "Storage"
    - name: "StorageExtraSpecs"
  serializers:
    - name: "DataSerializer"
    - name: "BackupSerializer" # ОШИБКА 10
```