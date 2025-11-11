# Трекер личных расходов

Простой трекер личных расходов.

## Текущий статус

⚠️ **Разработка бэкенда**: На текущий момент фокус на разработке API. Фронтенд будет разрабатываться позднее.

## Технологический стек

-   **Бэкенд**: FastAPI
    
-   **База данных**: PostgreSQL
    
-   **ORM**: SQLModel
    
-   **Миграции**: Alembic
    
-   **Управление зависимостями**: Poetry
    

## Установка

### Предварительные требования

-   Python 3.14+
    
-   PostgreSQL 18+
    
-   Poetry 2
    

### Настройка

1.  **Клонировать репозиторий**
    
    ```bash
    git clone https://github.com/ilyakutilin/expense-tracker.git
    cd expense-tracker
    ```
    
2.  **Создать и активировать виртуальное окружение**
    
    ```bash
    python -m venv venv
    venv\Scripts\activate.bat # для Windows
    source venv/bin/activate # для Linux и MacOS
    ```

3.  **Установить зависимости с Poetry**
    
    ```bash
    poetry install
    ```
