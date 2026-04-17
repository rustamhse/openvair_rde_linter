# Протокол воспроизведения эксперимента: Сравнение RDE-линтера и LLM

Данный протокол описывает шаги, необходимые для воспроизведения эксперимента по выявлению 43 искусственно внедренных архитектурных дефектов (Requirements Mutation) в проекте Open vAIR.

## Подготовительный этап
Все команды должны выполняться из корневой директории проекта `openvair`. Убедитесь, что мутированные спецификации (файлы `error_specification.md` с 43 внедренными ошибками) размещены в соответствующих директориях:
* `docs\reference\modules\template\error_specification.md`
* `docs\reference\modules\storage\error_specification.md`
* `docs\reference\modules\backup\error_specification.md`
* `docs\reference\modules\event_store\error_specification.md`
* `docs\reference\modules\image\error_specification.md`
* `docs\reference\modules\network\error_specification.md`
* `docs\reference\modules\user\error_specification.md`
* `docs\reference\modules\virtual_machines\error_specification.md`
* `docs\reference\modules\volume\error_specification.md`

---

## Этап 1. Запуск детерминированного RDE-линтера (на базе AST)

Для проверки всех модулей с помощью разработанного инструмента необходимо последовательно запустить скрипт статического анализа для каждого модуля.

**Команды для ручного запуска (Windows/Linux/macOS):**

```bash
python -m openvair.requirements_linter.cli --spec docs\reference\modules\template\error_specification.md --target openvair/modules/template

python -m openvair.requirements_linter.cli --spec docs\reference\modules\storage\error_specification.md --target openvair/modules/storage

python -m openvair.requirements_linter.cli --spec docs\reference\modules\backup\error_specification.md --target openvair/modules/backup

python -m openvair.requirements_linter.cli --spec docs\reference\modules\event_store\error_specification.md --target openvair/modules/event_store

python -m openvair.requirements_linter.cli --spec docs\reference\modules\image\error_specification.md --target openvair/modules/image

python -m openvair.requirements_linter.cli --spec docs\reference\modules\network\error_specification.md --target openvair/modules/network

python -m openvair.requirements_linter.cli --spec docs\reference\modules\user\error_specification.md --target openvair/modules/user

python -m openvair.requirements_linter.cli --spec docs\reference\modules\virtual_machines\error_specification.md --target openvair/modules/virtual_machines

python -m openvair.requirements_linter.cli --spec docs\reference\modules\volume\error_specification.md --target openvair/modules/volume
```

**Ожидаемый результат:** В консоли будет выведено ровно 43 сообщения об ошибках формата `[DDD Violation]`. Зафиксируйте общее время выполнения (ожидаемое время: менее 2 секунд).

---

## Этап 2. Запуск верификации через генеративную модель (LLM)

Для сопоставимости результатов генеративная модель должна работать в режиме строгого бинарного сравнения, аналогично AST-линтеру.

**Порядок действий:**
1. Откройте интерфейс выбранной Большой Языковой Модели (рекомендуется использовать модели класса Pro с поддержкой загрузки файлов и большим контекстным окном).
2. Соберите в один архив (или загрузите папками) все 9 файлов `error_specification.md` и все Python-файлы из директории `openvair/modules/`.
3. Отправьте модели следующий строгий системный промпт вместе с файлами:

**Системный промпт для LLM:**

```text
Ты — строгий статический анализатор архитектуры (RDE-linter), работающий по принципу точного совпадения строк (Strict String Matching). Твоя задача — провести пакетную сверку архитектурных спецификаций (в формате YAML) с фактическим исходным кодом Python для 9 модулей проекта Open vAIR (архитектура Domain-Driven Design). 

КРИТИЧЕСКОЕ ПРАВИЛО: 
Запрещено использовать семантическое сходство, синонимы, лемматизацию или догадки. Сравнение должно быть строго бинарным. Если в спецификации указано "Template", а в коде "TemplateModel" — это ОШИБКА. Если указано "GET", а в коде "POST" — это ОШИБКА. 

АЛГОРИТМ РАБОТЫ (выполни для КАЖДОГО переданного модуля):
1. Сопоставь файл спецификации (блок `yaml rde-spec`) с исходным кодом соответствующего модуля.
2. Проанализируй Python-файлы конкретного модуля по следующим правилам извлечения:
   - Entrypoints (Endpoints): Ищи декораторы `@router.<method>('<path>', ...)`. Сопоставь HTTP-метод и точный путь.
   - Entrypoints (CRUD): Ищи класс, оканчивающийся на `Crud`. Извлеки все его публичные методы.
   - Domain (Models): Ищи классы в слое domain, имена которых НЕ оканчиваются на `Exception` или `Error`.
   - Service (Managers): Ищи классы в слое service, имена которых оканчиваются на `Manager`.
   - Service (Services): Ищи публичные методы внутри менеджеров или публичные функции в `services.py`.
   - Adapters (ORM Models): Ищи классы в `orm.py`, наследующиеся от базового декларативного класса.
   - Adapters (Serializers): Ищи классы в `serializer.py`, содержащие в названии `Serializer`.
3. Сравни извлеченные из кода сущности с эталонным контрактом этого модуля. ВСЁ, что заявлено в YAML, ОБЯЗАНО присутствовать в коде с идентичным названием. (Лишнее в коде — игнорируй, нехватка или опечатка в коде по сравнению с YAML — ошибка).

ФОРМАТ ВЫВОДА:
Ты должен выдать ТОЛЬКО единый сводный отчет о десинхронизации. Не пиши рассуждений, вступлений или выводов. Отчет должен быть сгруппирован по модулям. 
Используй строго следующий формат:

=== MODULE: <Имя модуля> ===
[DDD Violation] <Слой>: <Тип сущности> '<Ожидаемое значение>' is required but not implemented in the code.
...

Если в модуле нет расхождений, напиши: "✅ Perfect match!" под его названием.
```

**Ожидаемый результат:** Модель сгенерирует текстовый лог с перечислением выявленных ошибок. Зафиксируйте количество найденных дефектов (Recall) и время, затраченное моделью на обработку файлов и генерацию ответа (Execution Time).

---

## Этап 3. Сведение результатов

По итогам запусков необходимо сравнить:
1. **Полноту (Recall):** Соотношение найденных ошибок к общему числу заложенных мутаций (43/43).
2. **Время выполнения (Execution Time):** Скорость локальной работы AST-линтера против задержки ответа API языковой модели.