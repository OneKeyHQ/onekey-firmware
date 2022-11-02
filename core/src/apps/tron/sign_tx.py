from trezor import wire
from trezor.crypto.curve import secp256k1
from trezor.crypto.hashlib import sha256
from trezor.messages import TronSignedTx, TronSignTx

from apps.common import paths
from apps.common.keychain import Keychain, auto_keychain
from apps.tron.address import _address_base58, get_address_from_public_key
from apps.tron.serialize import serialize

from . import layout, tokens


@auto_keychain(__name__)
async def sign_tx(
    ctx: wire.Context, msg: TronSignTx, keychain: Keychain
) -> TronSignedTx:
    """Parse and sign TRX transaction"""

    validate(msg)
    address_n = msg.address_n or ()
    await paths.validate_path(ctx, keychain, msg.address_n)
    node = keychain.derive(address_n)

    seckey = node.private_key()
    public_key = secp256k1.publickey(seckey, False)
    address = get_address_from_public_key(public_key[:65])

    try:
        await _require_confirm_by_type(ctx, msg, address)
    except AttributeError:
        raise wire.DataError("The transaction has invalid asset data field")

    raw_data = serialize(msg, address)
    data_hash = sha256(raw_data).digest()

    signature = secp256k1.sign(seckey, data_hash, False)

    signature = signature[1:65] + bytes([(~signature[0] & 0x01) + 27])
    return TronSignedTx(signature=signature, serialized_tx=raw_data)


async def _require_confirm_by_type(ctx, transaction, owner_address):
    # Confirm extra data if exist
    if transaction.data:
        await layout.require_confirm_data(ctx, transaction.data, len(transaction.data))

    # Confirm transaction
    contract = transaction.contract
    if contract.transfer_contract:
        from trezor.ui.layouts import confirm_final

        if contract.transfer_contract.amount is None:
            raise wire.DataError("Invalid Tron transfer amount")

        await layout.require_confirm_tx(
            ctx,
            contract.transfer_contract.to_address,
            contract.transfer_contract.amount,
        )
        await confirm_final(ctx)

        return

    if contract.trigger_smart_contract:
        # check if TRC20 transfer/approval
        data = contract.trigger_smart_contract.data
        action = None

        if data is None:
            raise wire.DataError("Invalid Tron contract call data")

        if (
            data[:16]
            == b"\xa9\x05\x9c\xbb\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ):
            action = "Transfer"
        elif (
            data[:16]
            == b"\x09\x5e\xa7\xb3\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        ):
            action = "Approve"

        if action == "Transfer":
            token = tokens.token_by_address(
                "TRC20", contract.trigger_smart_contract.contract_address
            )
            recipient = _address_base58(b"\x41" + data[16:36])
            value = int.from_bytes(data[36:68], "big")
            await layout.require_confirm_trigger_trc20(
                ctx,
                False if token is tokens.UNKNOWN_TOKEN else True,
                contract.trigger_smart_contract.contract_address,
                value,
                token,
                recipient,
            )
            if transaction.fee_limit:
                await layout.require_confirm_fee(
                    ctx,
                    token,
                    from_address=owner_address,
                    to_address=contract.trigger_smart_contract.contract_address,
                    value=value,
                    fee_limit=transaction.fee_limit,
                    network="TRON",
                )
        else:
            from trezor.ui.layouts.lvgl import confirm_blind_sign_common, confirm_final

            await confirm_blind_sign_common(ctx, owner_address, data)
            await confirm_final(ctx)

        return

    raise wire.DataError("Invalid transaction type")


def validate(msg: TronSignTx):
    if None in (msg.contract,):
        raise wire.ProcessError("Some of the required fields are missing (contract)")
