# Архитектурная спецификация модуля Volume

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Volume Module Core"
description: "Baseline architectural specification for the Open vAIR volume module."

entrypoints_layer:
  crud_adapters:
    - name: "VolumeCrud"
      methods:
        - "get_volume"
        - "get_all_volumes"
        - "create_volume"
        - "delete_volume"
        - "extend_volume"
        - "edit_volume"
        - "attach_volume"
        - "detach_volume"
        - "create_from_template"
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/{volume_id}/"
      method: "GET"
    - path: "/create/"
      method: "POST"
    - path: "/{volume_id}/"
      method: "DELETE"
    - path: "/{volume_id}/extend/"
      method: "POST"
    - path: "/{volume_id}/edit/"
      method: "PUT"
    - path: "/{volume_id}/attach/"
      method: "POST"
    - path: "/{volume_id}/detach/"
      method: "DELETE"
    - path: "/from_template/"
      method: "POST"

domain_layer:
  models:
    - name: "AbstractVolumeFactory"
    - name: "VolumeFactory"

service_layer:
  managers:
    - name: "VolumeServiceLayerManager"
  services:
    - name: "get_volume"
    - name: "get_all_volumes"
    - name: "create_volume"
    - name: "clone_volume"
    - name: "extend_volume"
    - name: "delete_volume"
    - name: "edit_volume"
    - name: "attach_volume"
    - name: "detach_volume"
    - name: "create_from_template"
    - name: "monitoring"

adapters_layer:
  orm_models:
    - name: "Volume"
    - name: "VolumeAttachVM"
  serializers:
    - name: "DataSerializer"
    - name: "VolumeDomainSerializer"
    - name: "AttachmentWebSerializer"
    - name: "VolumeWebSerializer"
```