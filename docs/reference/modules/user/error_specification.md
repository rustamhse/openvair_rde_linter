# Архитектурная спецификация модуля Backup

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "User Module Core"
description: "Mutated architectural specification for the Open vAIR user module."

entrypoints_layer:
  crud_adapters:
    - name: "UserCrud"
      methods:
        - "get_user"
        - "get_users"
        - "create_user"
        - "change_password"
        - "delete_user"
        - "login" # ОШИБКА 30
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/all/"
      method: "GET"
    - path: "/{user_id}/create/"
      method: "POST"
    - path: "/{user_id}/"
      method: "DELETE"
    - path: "/{user_id}/change-password/"
      method: "PUT" # ОШИБКА 29
    - path: "/"
      method: "POST"
    - path: "/refresh"
      method: "POST"

service_layer:
  managers:
    - name: "UserServiceLayerManager" # ОШИБКА 31
  services:
    - name: "get_user"
    - name: "get_all_users"
    - name: "auth_user" # ОШИБКА 32
    - name: "create_user"
    - name: "change_password"
    - name: "delete_user"

adapters_layer:
  orm_models:
    - name: "Users" # ОШИБКА 33
  serializers:
    - name: "DataSerializer"
```