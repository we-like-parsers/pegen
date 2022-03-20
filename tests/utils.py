import importlib.util
import sys
import token
from typing import  Any, Final, cast


ALL_TOKENS = token.tok_name
EXACT_TOKENS = token.EXACT_TOKEN_TYPES  # type: ignore
NON_EXACT_TOKENS = {
    name for index, name in token.tok_name.items() if index not in EXACT_TOKENS.values()
}


def import_file(full_name: str, path: str) -> Any:
    """Import a python module from a path"""

    spec = importlib.util.spec_from_file_location(full_name, path)
    mod = importlib.util.module_from_spec(spec)

    # We assume this is not None and has an exec_module() method.
    # See https://docs.python.org/3/reference/import.html?highlight=exec_module#loading
    loader = cast(Any, spec.loader)
    loader.exec_module(mod)
    return mod


def print_memstats() -> bool:
    MiB: Final = 2 ** 20
    try:
        import psutil  # type: ignore
    except ImportError:
        return False
    print("Memory stats:")
    process = psutil.Process()
    meminfo = process.memory_info()
    res = {}
    res["rss"] = meminfo.rss / MiB
    res["vms"] = meminfo.vms / MiB
    if sys.platform == "win32":
        res["maxrss"] = meminfo.peak_wset / MiB
    else:
        # See https://stackoverflow.com/questions/938733/total-memory-used-by-python-process
        import resource  # Since it doesn't exist on Windows.

        rusage = resource.getrusage(resource.RUSAGE_SELF)
        if sys.platform == "darwin":
            factor = 1
        else:
            factor = 1024  # Linux
        res["maxrss"] = rusage.ru_maxrss * factor / MiB
    for key, value in res.items():
        print(f"  {key:12.12s}: {value:10.0f} MiB")
    return True
