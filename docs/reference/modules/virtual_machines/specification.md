# Архитектурная спецификация модуля Virtual Machines

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Virtual Machines Module Core"
description: "Baseline architectural specification for the Open vAIR virtual machines module."

entrypoints_layer:
  crud_adapters:
    - name: "VMCrud"
      methods:
        - "get_vm"
        - "get_all_vms"
        - "create_vm"
        - "delete_vm"
        - "start_vm"
        - "shut_off_vm"
        - "edit_vm"
        - "vnc"
        - "clone_vm"
        - "get_snapshots"
        - "get_snapshot"
        - "create_snapshot"
        - "revert_snapshot"
        - "delete_snapshot"
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/{vm_id}/"
      method: "GET"
    - path: "/create/"
      method: "POST"
    - path: "/{vm_id}/"
      method: "DELETE"
    - path: "/{vm_id}/start/"
      method: "POST"
    - path: "/{vm_id}/shut-off/"
      method: "POST"
    - path: "/{vm_id}/edit/"
      method: "POST"
    - path: "/{vm_id}/vnc/"
      method: "GET"
    - path: "/{vm_id}/clone/"
      method: "POST"
    - path: "/{vm_id}/snapshots/"
      method: "GET"
    - path: "/{vm_id}/snapshots/{snap_id}"
      method: "GET"
    - path: "/{vm_id}/snapshots/"
      method: "POST"
    - path: "/{vm_id}/snapshots/{snap_id}/revert"
      method: "POST"
    - path: "/{vm_id}/snapshots/{snap_id}"
      method: "DELETE"

domain_layer:
  models:
    - name: "AbstractVMDriverFactory"
    - name: "VMDriverFactory"

service_layer:
  managers:
    - name: "VMServiceLayerManager"
  services:
    - name: "get_vm"
    - name: "get_all_vms"
    - name: "create_vm"
    - name: "delete_vm"
    - name: "start_vm"
    - name: "shut_off_vm"
    - name: "edit_vm"
    - name: "vnc"
    - name: "clone_vm"
    - name: "get_snapshot"
    - name: "get_snapshots"
    - name: "create_snapshot"
    - name: "revert_snapshot"
    - name: "delete_snapshot"
```