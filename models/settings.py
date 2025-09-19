from typing import Optional

from models import Setting


def set_setting(key: str, value: str):
    Setting.insert(key=key, value=value).on_conflict(
        conflict_target=[Setting.key],
        preserve=[],
        update={Setting.value: value}
    ).execute()

def get_setting(key: str) -> Optional[str]:
    try:
        setting = Setting.get(Setting.key == key)
        return setting.value
    except Setting.table_exists():
        return None
