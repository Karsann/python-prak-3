import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, List

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class LogFormatter(ABC):
    @abstractmethod
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        pass

class PlainFormatter(LogFormatter):
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{level}] {time_str} - {message}"


class JSONFormatter(LogFormatter):
    def format(self, level: str, message: str, timestamp: datetime) -> str:
        data = {
            "level": level,
            "time": timestamp.isoformat(),
            "message": message
        }
        return json.dumps(data, ensure_ascii=False)

class ColorFormatter(LogFormatter):
    COLORS = {
        "DEBUG": "\033[90m",
        "INFO": "\033[92m",
        "WARNING": "\033[93m",
        "ERROR": "\033[91m"
    }
    RESET = "\033[0m"

    def format(self, level: str, message: str, timestamp: datetime) -> str:
        color = self.COLORS.get(level, "")
        time_str = timestamp.strftime("%H:%M:%S")
        return f"{color}[{level}] {time_str} - {message}{self.RESET}"

class FormatterFactory:
    _formatters = {
        "plain": PlainFormatter,
        "json": JSONFormatter,
        "color": ColorFormatter
    }

    @classmethod
    def register(cls, name: str, formatter_cls: type[LogFormatter]):
        cls._formatters[name] = formatter_cls

    @classmethod
    def create(cls, name: str) -> LogFormatter:
        if name not in cls._formatters:
            raise ValueError(f"Невідомий тип форматера: {name}")
        return cls._formatters[name]()

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._formatters.keys())

class Logger(metaclass=SingletonMeta):
    LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def __init__(self, formatter_name: str = "plain", min_level: str = "DEBUG"):
        if getattr(self, "_initialized", False):
            return
        self._formatter = FormatterFactory.create(formatter_name)
        self._min_level = min_level
        self._log_history: list[str] = []
        self._initialized = True

    def set_formatter(self, name: str):
        self._formatter = FormatterFactory.create(name)

    def log(self, level: str, message: str):
        if self.LEVELS.get(level, 0) >= self.LEVELS.get(self._min_level, 0):
            entry = self._formatter.format(level, message, datetime.now())
            print(entry)
            self._log_history.append(entry)

    def debug(self, msg: str):
        self.log("DEBUG", msg)

    def info(self, msg: str):
        self.log("INFO", msg)

    def warning(self, msg: str):
        self.log("WARNING", msg)

    def error(self, msg: str):
        self.log("ERROR", msg)

    def get_history(self) -> list[str]:
        return self._log_history[:]

def task_3_1():
    print("Завдання 3.1: Singleton та Factory Method")

    logger1 = Logger("plain", "DEBUG")
    logger2 = Logger("json", "INFO")
    print(f"Доказ патерну Singleton (logger1 is logger2): {logger1 is logger2}")

    print("\nВивід повідомлень різних рівнів:")
    logger1.info("Система запущена")
    logger1.warning("Мало пам'яті")
    logger1.error("Помилка з'єднання")

    print("\nЗміна форматера на JSON:")
    logger1.set_formatter("json")
    logger1.debug("Діагностика через JSON")

    print(f"\nДоступні форматери: {FormatterFactory.available()}")
    print(f"Всього записів у історії логів: {len(logger1.get_history())}")

class EventEmitter:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = {}

    def on(self, event: str, callback: Callable):
        if event not in self._listeners:
            self._listeners[event] = []
        self._listeners[event].append(callback)

    def off(self, event: str, callback: Callable):
        if event in self._listeners and callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event: str, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

@dataclass
class Task:
    title: str
    priority: int
    deadline: datetime
    completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

class SortStrategy(ABC):
    @abstractmethod
    def sort(self, tasks: List[Task]) -> List[Task]:
        pass

class SortByPriority(SortStrategy):
    def sort(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.priority)

class SortByDeadline(SortStrategy):
    def sort(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.deadline)

class SortByCreationDate(SortStrategy):
    def sort(self, tasks: List[Task]) -> List[Task]:
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

class TaskModel(EventEmitter):
    def __init__(self):
        super().__init__()
        self._tasks: List[Task] = []

    def add_task(self, title: str, priority: int, deadline: datetime):
        task = Task(title, priority, deadline)
        self._tasks.append(task)
        self.emit("task_added", task)

    def complete_task(self, index: int):
        if 0 <= index < len(self._tasks):
            task = self._tasks[index]
            task.completed = True
            self.emit("task_completed", task)

    def remove_task(self, index: int):
        if 0 <= index < len(self._tasks):
            task = self._tasks.pop(index)
            self.emit("task_removed", task)

    def get_tasks(self, include_completed: bool = True) -> List[Task]:
        if include_completed:
            return self._tasks[:]
        return [t for t in self._tasks if not t.completed]

    def get_statistics(self) -> dict:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.completed)
        return {
            "total": total,
            "completed": completed,
            "active": total - completed
        }

class TaskView:
    def show_tasks(self, tasks: List[Task], title: str = "Завдання"):
        print(f"\nТаблиця: {title}")
        print(f"{'№':<3} | {'Назва':<15} | {'Пріоритет':<9} | {'Дедлайн':<16} | {'Статус'}")
        for i, t in enumerate(tasks):
            status = "Виконано" if t.completed else "Активне"
            date_str = t.deadline.strftime("%Y-%m-%d %H:%M")
            print(f"{i:<3} | {t.title:<15} | {t.priority:<9} | {date_str:<16} | {status}")

    def show_message(self, message: str):
        print(f"[INFO] {message}")

    def show_statistics(self, stats: dict):
        print(f"\nСтатистика завдань: Всього={stats['total']}, Виконано={stats['completed']}, Активних={stats['active']}")

class TaskController:
    def __init__(self, model: TaskModel, view: TaskView):
        self._model = model
        self._view = view
        self._sort_strategy: SortStrategy = SortByPriority()

        self._model.on("task_added", lambda t: self._view.show_message(f"Додано: {t.title}"))
        self._model.on("task_completed", lambda t: self._view.show_message(f"Завершено: {t.title}"))
        self._model.on("task_removed", lambda t: self._view.show_message(f"Видалено: {t.title}"))

    def set_sort_strategy(self, strategy: SortStrategy):
        self._sort_strategy = strategy

    def add_task(self, title: str, priority: int, deadline: datetime):
        self._model.add_task(title, priority, deadline)

    def complete_task(self, index: int):
        self._model.complete_task(index)

    def show_all(self):
        tasks = self._model.get_tasks()
        sorted_tasks = self._sort_strategy.sort(tasks)
        self._view.show_tasks(sorted_tasks, "Всі завдання")

    def show_active(self):
        tasks = self._model.get_tasks(include_completed=False)
        sorted_tasks = self._sort_strategy.sort(tasks)
        self._view.show_tasks(sorted_tasks, "Активні завдання")

    def show_stats(self):
        self._view.show_statistics(self._model.get_statistics())

def task_3_2():
    print("\nЗавдання 3.2: Observer, Strategy та MVC")

    model = TaskModel()
    view = TaskView()
    ctrl = TaskController(model, view)

    now = datetime.now()
    ctrl.add_task("Здати лабу 1", 1, now + timedelta(days=1))
    ctrl.add_task("Купити хліб", 4, now + timedelta(days=3))
    ctrl.add_task("Вивчити патерни", 2, now + timedelta(hours=5))
    ctrl.add_task("Помити посуд", 5, now + timedelta(hours=2))

    print("\nСортування за замовчуванням (SortByPriority):")
    ctrl.show_all()

    print("\nЗміна стратегії на SortByDeadline:")
    ctrl.set_sort_strategy(SortByDeadline())
    ctrl.show_all()

    print("\nПозначення завдання №0 як виконане:")
    ctrl.complete_task(0)

    print("\nВідображення лише активних завдань:")
    ctrl.show_active()

    ctrl.show_stats()

if __name__ == "__main__":
    task_3_1()
    task_3_2()
