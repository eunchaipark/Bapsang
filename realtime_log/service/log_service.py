from realtime_log.repository.log_repo import insert_log


async def save_log(payload):

    action_type = payload["action_type"]

    if action_type not in ["CLICK", "LIKE"]:
        raise ValueError("invalid action_type")

    await insert_log(payload)