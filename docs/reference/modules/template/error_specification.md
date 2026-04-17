# Архитектурная спецификация модуля Template

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Template Module Core"
description: "Mutated architectural specification for the Open vAIR template module."

entrypoints_layer:
  crud_adapters:
    - name: "TemplateCrud"
      methods:
        - "get_all_templates"
        - "get_template"
        - "create_template"
        - "edit_template"
        - "delete_template"
        - "export_template" # ОШИБКА 2
  endpoints:
    - path: "/"
      method: "PUT" # ОШИБКА 1
    - path: "/{template_id}"
      method: "GET"
    - path: "/"
      method: "POST"
    - path: "/{template_id}"
      method: "PATCH"
    - path: "/{template_id}"
      method: "DELETE"

domain_layer:
  models:
    - name: "AbstractTemplateFactory"
    - name: "TemplatesFactory" # ОШИБКА 3

service_layer:
  managers:
    - name: "TemplateServiceLayerManager"
  services:
    - name: "get_all_templates"
    - name: "create_template"
    - name: "update_template" # ОШИБКА 4
    - name: "delete_template"

adapters_layer:
  orm_models:
    - name: "TemplateModel" # ОШИБКА 5
  serializers:
    - name: "ApiSerializer"
    - name: "DomainSerializer"
    - name: "CreateSerializer"
```