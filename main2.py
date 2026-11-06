import functools
import time

def cache(max_size: int = 128):
    def decorator(func):
        _cache = {}
        _call_order = []

        @functools.wraps(func)
        def wrapper(*args):
            if args in _cache:
                print(f"cache hit для аргументів: {args}")
                _call_order.remove(args)
                _call_order.append(args)
                return _cache[args]

            print(f"cache miss для аргументів: {args}")
            res = func(*args)
            _cache[args] = res
            _call_order.append(args)

            if len(_cache) > max_size:
                oldest = _call_order.pop(0)
                del _cache[oldest]

            return res

        wrapper.cache_info = lambda: {
            "size": len(_cache),
            "max_size": max_size
        }
        wrapper.cache_clear = lambda: (_cache.clear(), _call_order.clear())
        return wrapper

    return decorator

def rate_limit(max_calls: int, period: float = 60.0):
    def decorator(func):
        call_times = []

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            nonlocal call_times
            call_times = [t for t in call_times if now - t <= period]

            if len(call_times) >= max_calls:
                raise RuntimeError(f"Перевищено ліміт викликів ({max_calls} за {period}с)")

            call_times.append(now)
            return func(*args, **kwargs)

        return wrapper

    return decorator

def log(level: str = "INFO"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[{level}] Виклик {func.__name__}({args}, {kwargs})")
            start = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                print(f"[{level}] {func.__name__} -> {result} (час: {elapsed:.5f}c)")
                return result
            except Exception as e:
                print(f"[ERROR] {func.__name__} виняток: {e}")
                raise

        return wrapper

    return decorator

@cache(max_size=64)
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

@rate_limit(max_calls=5, period=10.0)
def send_notification(message: str) -> str:
    return f"Надіслано: {message}"

@log(level="DEBUG")
def divide(a: float, b: float) -> float:
    return a / b

def task_2_1():
    print("Завдання 2.1: Декоратори функцій")
    print("Обчислення числа Фібоначчі:")
    fib_res = fibonacci(10)
    print("Результат fibonacci(10):", fib_res)
    print("Статистика кешу:", fibonacci.cache_info())

    print("\nТест обмеження частоти викликів (rate_limit):")
    try:
        for i in range(6):
            print(send_notification(f"Повідомлення {i + 1}"))
    except RuntimeError as e:
        print("Перехоплено очікувану помилку:", e)

    print("\nТест логування (log):")
    divide(10.0, 2.0)
    try:
        divide(10.0, 0.0)
    except ZeroDivisionError:
        print("Помилку ділення на нуль успішно спіймано")

def auto_repr(cls):
    arg_count = cls.__init__.__code__.co_argcount
    param_names = cls.__init__.__code__.co_varnames[1:arg_count]

    def __repr__(self):
        params_str = ", ".join(f"{name}={getattr(self, name)!r}" for name in param_names)
        return f"{cls.__name__}({params_str})"

    cls.__repr__ = __repr__
    return cls

def frozen(cls):
    orig_init = cls.__init__

    def new_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self._frozen = True

    def new_setattr(self, name, value):
        if getattr(self, "_frozen", False):
            raise AttributeError(f"Клас {cls.__name__} заморожений для змін")
        object.__setattr__(self, name, value)

    cls.__init__ = new_init
    cls.__setattr__ = new_setattr
    return cls

def log_methods(cls):
    for attr_name, attr_val in list(cls.__dict__.items()):
        if callable(attr_val) and not attr_name.startswith("_"):
            def make_wrapper(func):
                @functools.wraps(func)
                def wrapper(self, *args, **kwargs):
                    print(f"[LOG METHOD] Виклик {func.__name__} з аргументами {args}")
                    res = func(self, *args, **kwargs)
                    print(f"[LOG METHOD] {func.__name__} повернув {res}")
                    return res
                return wrapper
            setattr(cls, attr_name, make_wrapper(attr_val))
    return cls

@auto_repr
class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

@frozen
class ImmutableConfig:
    def __init__(self, host: str, port: int, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug

@log_methods
class MathService:
    def add(self, a: float, b: float) -> float:
        return a + b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Ділення на нуль")
        return a / b

def task_2_2():
    print("\nЗавдання 2.2: Декоратори класів")
    p = Point(3.0, 4.0)
    print("Результат auto_repr:", repr(p))

    print("\nТест frozen класу:")
    cfg = ImmutableConfig("localhost", 8080, debug=True)
    print(f"Конфіг: host={cfg.host}, port={cfg.port}")
    try:
        cfg.host = "remote"
    except AttributeError as e:
        print("Перехоплено очікувану помилку:", e)

    print("\nТест log_methods:")
    svc = MathService()
    svc.add(10.0, 20.0)
    svc.multiply(3.0, 7.0)
    try:
        svc.divide(10.0, 0.0)
    except ValueError as e:
        print("Перехоплено ValueError:", e)

if __name__ == "__main__":
    task_2_1()
    task_2_2()
