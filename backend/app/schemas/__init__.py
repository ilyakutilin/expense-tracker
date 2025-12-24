from typing import Annotated

from pydantic.types import StringConstraints

StrippedStr = Annotated[str, StringConstraints(strip_whitespace=True)]
