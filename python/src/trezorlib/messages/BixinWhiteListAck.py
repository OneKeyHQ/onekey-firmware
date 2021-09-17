# Automatically generated by pb2py
# fmt: off
from .. import protobuf as p

if __debug__:
    try:
        from typing import Dict, List  # noqa: F401
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        pass


class BixinWhiteListAck(p.MessageType):
    MESSAGE_WIRE_TYPE = 912

    def __init__(
        self,
        *,
        address: List[str] = None,
    ) -> None:
        self.address = address if address is not None else []

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            1: ('address', p.UnicodeType, p.FLAG_REPEATED),
        }
