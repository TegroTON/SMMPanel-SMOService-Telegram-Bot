import re

PATTERN = re.compile(r"(?<!^)(?=[A-Z])")


def camel_to_snake(name: str) -> str:
    return PATTERN.sub("_", name).lower()
