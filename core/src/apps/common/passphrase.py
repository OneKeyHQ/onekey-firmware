from micropython import const

import storage.device
from trezor import wire, workflow
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

_MAX_PASSPHRASE_LEN = const(50)


def is_enabled() -> bool:
    return storage.device.is_passphrase_enabled()


async def get(ctx: wire.Context) -> str:
    if is_enabled():
        return await _request_from_user(ctx)
    else:
        return ""


async def _request_from_user(ctx: wire.Context) -> str:
    workflow.close_others()  # request exclusive UI access
    if storage.device.get_passphrase_always_on_device():
        from trezor.ui.layouts import request_passphrase_on_device

        passphrase = await request_passphrase_on_device(ctx, _MAX_PASSPHRASE_LEN)
    else:
        passphrase = await _request_on_host(ctx)
    if len(passphrase.encode()) > _MAX_PASSPHRASE_LEN:
        raise wire.DataError(
            f"Maximum passphrase length is {_MAX_PASSPHRASE_LEN} bytes"
        )

    return passphrase


async def _request_on_host(ctx: wire.Context) -> str:
    from trezor.messages import PassphraseAck, PassphraseRequest

    _entry_dialog()

    request = PassphraseRequest()
    ack = await ctx.call(request, PassphraseAck)
    if ack.on_device:
        from trezor.ui.layouts import request_passphrase_on_device

        if ack.passphrase is not None:
            raise wire.DataError("Passphrase provided when it should not be")
        return await request_passphrase_on_device(ctx, _MAX_PASSPHRASE_LEN)

    if ack.passphrase is None:
        raise wire.DataError(
            "Passphrase not provided and on_device is False. Use empty string to set an empty passphrase."
        )

    # # non-empty passphrase
    if ack.passphrase:
        from trezor.ui.layouts import require_confirm_passphrase

        await require_confirm_passphrase(ctx, ack.passphrase)

    return ack.passphrase


def _entry_dialog() -> None:
    from trezor.ui.layouts import draw_simple_text

    draw_simple_text(
        _(i18n_keys.TITLE__ENTER_PASSPHRASE),
        _(i18n_keys.SUBTITLE__ENTER_PASSPHRASE_ON_SOFTWARE),
    )
