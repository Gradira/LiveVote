from models import Event


def get_latest_events(limit: int = 20) -> list[Event]:
    return [
        event for event in Event.select()
        .order_by(Event.timestamp.desc())
        .limit(limit)
    ]

def _compute_power_milestones(old_value: float, new_value: float, base: int, minimum: int = 1) -> list[int]:
    milestones: list[int] = []
    if new_value <= old_value:
        return milestones
    # find the first milestone above old_value
    p = 0
    while base ** p <= old_value:
        p += 1
    # keep adding milestones until we exceed new_value
    while True:
        milestone = base ** p
        if milestone > new_value:
            break
        if milestone < minimum:
            p += 1
            continue
        milestones.append(milestone)
        p += 1
    return milestones
