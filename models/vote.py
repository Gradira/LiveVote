from models import Vote


def get_latest_votes(limit: int = 20) -> list[Vote]:
    return [
        vote for vote in Vote.select()
        .where(Vote.redacted == False)
        .order_by(Vote.timestamp.desc())
        .limit(limit)
    ]
