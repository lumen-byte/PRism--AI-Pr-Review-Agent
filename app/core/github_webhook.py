import hashlib
import hmac


def validate_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Validates a GitHub Webhook signature.

    :param payload: The raw request body as bytes.
    :param signature: The value of the X-Hub-Signature-256 header.
    :param secret: The webhook secret.
    :return: True if the signature is valid, False otherwise.
    """
    if not signature or not signature.startswith("sha256="):
        return False

    hash_object = hmac.new(
        secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    return hmac.compare_digest(expected_signature, signature)
