# Automatically generated by pb2py
from .. import protobuf as p
from .StellarAssetType import StellarAssetType


class StellarPathPaymentOp(p.MessageType):
    FIELDS = {
        1: ('source_account', p.BytesType, 0),
        2: ('send_asset', StellarAssetType, 0),
        3: ('send_max', p.SVarintType, 0),
        4: ('destination_account', p.BytesType, 0),
        5: ('destination_asset', StellarAssetType, 0),
        6: ('destination_amount', p.SVarintType, 0),
        7: ('paths', StellarAssetType, p.FLAG_REPEATED),
    }
    MESSAGE_WIRE_TYPE = 212
