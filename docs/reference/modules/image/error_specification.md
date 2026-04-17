# Архитектурная спецификация модуля Backup

Ниже представлен формальный RDE-контракт модуля, описывающий его DDD-слои.
Линтер автоматически найдет этот блок по маркеру `yaml rde-spec`.

```yaml rde-spec
feature: "Image Module Core"
description: "Mutated architectural specification for the Open vAIR image module."

entrypoints_layer:
  crud_adapters:
    - name: "ImageCrud"
      methods:
        - "get_image"
        - "get_all_images"
        - "upload_image"
        - "delete_image"
        - "attach_image"
        - "detach_image"
        - "download_image" # ОШИБКА 20
  endpoints:
    - path: "/"
      method: "GET"
    - path: "/{image_id}/"
      method: "GET"
    - path: "/upload/"
      method: "POST"
    - path: "/{image_id}/"
      method: "DELETE"
    - path: "/{image_id}/attach/"
      method: "PUT" # ОШИБКА 19
    - path: "/{image_id}/detach/"
      method: "DELETE"

domain_layer:
  models:
    - name: "BaseImageFactory" # ОШИБКА 21
    - name: "ImageFactory"

service_layer:
  managers:
    - name: "ImageServiceLayerManager"
  services:
    - name: "get_image"
    - name: "get_all_images"
    - name: "upload_image"
    - name: "delete_image"
    - name: "attach_image"
    - name: "detach_image"
    - name: "healthcheck" # ОШИБКА 22

adapters_layer:
  orm_models:
    - name: "Image"
  serializers:
    - name: "ImageSerializer" # ОШИБКА 23
```