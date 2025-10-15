from dataclasses import is_dataclass, fields
import os

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
