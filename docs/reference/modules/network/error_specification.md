# Архитектурная спецификация модуля Backup

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Network Module Core"
description: "Mutated architectural specification for the Open vAIR network module."

entrypoints_layer:
  crud_adapters:
    - name: "InterfaceCrud"
      methods:
        - "get_all_interfaces"
        - "get_interface"
        - "list_bridges" # ОШИБКА 25
        - "create_bridge"
        - "delete_bridge"
        - "turn_on_interface"
        - "turn_off_interface"
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/bridges/"
      method: "GET"
    - path: "/{iface_id}/"
      method: "GET"
    - path: "/create/"
      method: "POST"
    - path: "/delete/"
      method: "DELETE"
    - path: "/{name}/turn_on"
      method: "POST" # ОШИБКА 24
    - path: "/{name}/turn_off"
      method: "PUT"

domain_layer:
  models:
    - name: "AbstractInterfaceFactory"
    - name: "InterfaceFactory"

service_layer:
  managers:
    - name: "NetworkManager" # ОШИБКА 28
  services:
    - name: "get_all_interfaces"
    - name: "get_interface"
    - name: "get_bridges_list"
    - name: "add_bridge" # ОШИБКА 26
    - name: "delete_bridge"
    - name: "turn_on"
    - name: "turn_off"
    - name: "monitoring"

adapters_layer:
  orm_models:
    - name: "Interface"
    - name: "InterfaceExtraSpecs" # ОШИБКА 27
  serializers:
    - name: "DataSerializer"
```