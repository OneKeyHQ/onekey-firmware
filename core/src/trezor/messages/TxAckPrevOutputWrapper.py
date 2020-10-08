# Automatically generated by pb2py
# fmt: off
import protobuf as p

from .PrevOutput import PrevOutput

if __debug__:
    try:
        from typing import Dict, List  # noqa: F401
        from typing_extensions import Literal  # noqa: F401
    except ImportError:
        pass


class TxAckPrevOutputWrapper(p.MessageType):

    def __init__(
        self,
        *,
        output: PrevOutput,
    ) -> None:
        self.output = output

    @classmethod
    def get_fields(cls) -> Dict:
        return {
            3: ('output', PrevOutput, p.FLAG_REQUIRED),
        }