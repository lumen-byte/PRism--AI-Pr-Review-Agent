def webhook_delivery_key(delivery_id: str) -> str:
    return f"webhook_delivery:{delivery_id}"


def pr_lock_key(repo_name: str, pr_number: int) -> str:
    return f"pr_lock:{repo_name}:{pr_number}"


def pr_status_key(repo_name: str, pr_number: int) -> str:
    return f"pr_status:{repo_name}:{pr_number}"
