# Архитектурная спецификация модуля Template

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Template Module Core"
description: "Baseline architectural specification for the Open vAIR template module."

entrypoints_layer:
  crud_adapters:
    - name: "TemplateCrud"
      methods:
        - "get_all_templates"
        - "get_template"
        - "create_template"
        - "edit_template"
        - "delete_template"
  endpoints:
    - path: "/"
      method: "GET"
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
    - name: "TemplateFactory"

service_layer:
  managers:
    - name: "TemplateServiceLayerManager"
  # В твоем parser.py функции внутри services.py трактуются как сервисы
  services:
    - name: "get_all_templates"
    - name: "create_template"
    - name: "edit_template"
    - name: "delete_template"

adapters_layer:
  orm_models:
    - name: "Template"
  serializers:
    - name: "ApiSerializer"
    - name: "DomainSerializer"
    - name: "CreateSerializer"
```