from engines.async_engine import AsyncEngine
from engines.parallel_engine import ParallelEngine
from engines.threading_engine import ThreadingEngine

ENGINE_MAP = {
    "threading": ThreadingEngine,
    "parallel": ParallelEngine,
    "async": AsyncEngine,
}


def available_engines():
    return sorted(ENGINE_MAP.keys())


def create_engine(name):
    normalized = str(name or "threading").strip().lower()
    if normalized not in ENGINE_MAP:
        raise ValueError(f"Unknown engine '{name}'. Available: {', '.join(available_engines())}")
    return ENGINE_MAP[normalized]()
