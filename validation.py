from dataclasses import is_dataclass, fields
import os, traceback, datetime

ART_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(ART_DIR, exist_ok=True)

class ValidationError(Exception):
    def __init__(self, file_name, missing_fields=None, reason=None):
        if missing_fields:
            msg = f"[{file_name}] Missing required field(s): {', '.join(missing_fields)}"
        else:
            msg = f"[{file_name}] Validation failed: {reason}"
        super().__init__(msg)
        self.file_name = file_name
        self.missing_fields = missing_fields or []
        self.reason = reason

def _is_empty(v):
    if v is None:
        return True
    if isinstance(v, str) and not v.strip():
        return True
    if isinstance(v, (list, tuple, set, dict)) and len(v) == 0:
        return True
    return False

def validate_dataclass(obj, required, file_path):
    file_name = os.path.basename(file_path)

    if obj is None:
        raise ValidationError(file_name, reason="data is None")
    if not is_dataclass(obj):
        raise ValidationError(file_name, reason=f"expected dataclass, got {type(obj).__name__}")

    # Build a mapping of field -> value from the dataclass instance
    values = {f.name: getattr(obj, f.name) for f in fields(obj)}

    # Validate only the required fields
    missing = [name for name in required if _is_empty(values.get(name))]
    if missing:
        raise ValidationError(file_name, missing_fields=missing)

def dump_debug(level_name, driver, err):
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    base = os.path.join(ART_DIR, level_name)
    try:
        html = driver.page_source if driver else ""
    except Exception:
        html = ""
    with open(f"{base}_{ts}_page.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open(f"{base}_{ts}_error.txt", "w", encoding="utf-8") as f:
        f.write("".join(traceback.format_exception(type(err), err, err.__traceback__)))
