from typing import TYPE_CHECKING

from trezor import ui, utils, wire
from trezor.crypto import random
from trezor.enums import BackupType, ButtonRequestType
from trezor.lvglui.i18n import gettext as _, keys as i18n_keys
from trezor.lvglui.scrs.reset_device import CheckWord

from ...components.common.confirm import is_confirmed
from ...components.tt.button import ButtonDefault
from ...components.tt.checklist import Checklist
from ...components.tt.confirm import Confirm
from ...components.tt.info import InfoConfirm
from ...components.tt.reset import Slip39NumInput
from .common import interact, raise_if_cancelled

if TYPE_CHECKING:
    from typing import Sequence

    NumberedWords = Sequence[tuple[int, str]]

if __debug__:
    pass


async def show_share_words(
    ctx: wire.GenericContext,
    share_words: Sequence[str],
    share_index: int | None = None,
    group_index: int | None = None,
) -> None:

    if share_index is None:
        header_title = _(i18n_keys.TITLE__MANUAL_BACKUP)
    elif group_index is None:
        header_title = f"Recovery share #{share_index + 1}"
    else:
        header_title = f"Group {group_index + 1} - Share {share_index + 1}"
    # shares_words_check = []  # check we display correct data
    from trezor.lvglui.scrs.reset_device import MnemonicDisplay

    screen = MnemonicDisplay(header_title, share_words)
    # make sure we display correct data
    # utils.ensure(share_words == shares_words_check)

    # confirm the share
    await raise_if_cancelled(
        interact(
            ctx,
            screen,
            "backup_words",
            ButtonRequestType.ResetDevice,
        )
    )


async def confirm_word(
    ctx: wire.GenericContext,
    share_index: int | None,
    share_words: Sequence[str],
    offset: int,
    count: int,
    group_index: int | None = None,
) -> bool:
    # remove duplicates
    non_duplicates = list(set(share_words))
    # remove current checked words
    non_duplicates.remove(share_words[offset])
    # shuffle list
    random.shuffle(non_duplicates)
    # take 3 words as choices
    choices = [non_duplicates[-1], non_duplicates[0], share_words[offset]]
    # shuffle again so the confirmed word is not always the first choice
    random.shuffle(choices)

    # let the user pick a word
    title = _(i18n_keys.TITLE__CHECK_WORD_STR).format(offset + 1)
    subtitle = _(i18n_keys.SUBTITLE__DEVICE_BACKUP_CHECK_WORD)
    options = f"{choices[0]}\n{choices[1]}\n{choices[2]}"
    selector = CheckWord(title, subtitle, options=options)
    # selector.selector.set_style_text_font(font_MONO28, lv.PART.MAIN | lv.STATE.DEFAULT)
    # selector.selector.set_flag()
    selected_word: str = await ctx.wait(selector.request())
    # confirm it is the correct one
    is_correct = selected_word == share_words[offset]
    if is_correct:
        selector.tip_correct()
    else:
        selector.tip_incorrect()
    from trezor import loop

    await loop.sleep(240)

    return is_correct


def _split_share_into_pages(
    share_words: Sequence[str],
) -> tuple[NumberedWords, list[NumberedWords], NumberedWords]:
    share = list(enumerate(share_words))  # we need to keep track of the word indices
    first = share[:2]  # two words on the first page
    length = len(share_words)
    if length in (12, 20, 24):
        middle = share[2:-2]
        last = share[-2:]  # two words on the last page
    elif length in (18, 33):
        middle = share[2:]
        last = []  # no words at the last page, because it does not add up
    else:
        # Invalid number of shares. SLIP-39 allows 20 or 33 words, BIP-39 12 or 24
        raise RuntimeError

    chunks = utils.chunks(middle, 4)  # 4 words on the middle pages
    return first, list(chunks), last


async def slip39_show_checklist(
    ctx: wire.GenericContext, step: int, backup_type: BackupType
) -> None:
    checklist = Checklist("Backup checklist", ui.ICON_RESET)
    if backup_type is BackupType.Slip39_Basic:
        checklist.add("Set number of shares")
        checklist.add("Set threshold")
        checklist.add(("Write down and check", "all recovery shares"))
    elif backup_type is BackupType.Slip39_Advanced:
        checklist.add("Set number of groups")
        checklist.add("Set group threshold")
        checklist.add(("Set size and threshold", "for each group"))
    checklist.select(step)

    await raise_if_cancelled(
        interact(
            ctx,
            Confirm(checklist, confirm="Continue", cancel=None),
            "slip39_checklist",
            ButtonRequestType.ResetDevice,
        )
    )


async def slip39_prompt_threshold(
    ctx: wire.GenericContext, num_of_shares: int, group_id: int | None = None
) -> int:
    count = num_of_shares // 2 + 1
    # min value of share threshold is 2 unless the number of shares is 1
    # number of shares 1 is possible in advnaced slip39
    min_count = min(2, num_of_shares)
    max_count = num_of_shares

    while True:
        shares = Slip39NumInput(
            Slip39NumInput.SET_THRESHOLD, count, min_count, max_count, group_id
        )
        confirmed = is_confirmed(
            await interact(
                ctx,
                Confirm(
                    shares,
                    confirm="Continue",
                    cancel="Info",
                    major_confirm=True,
                    cancel_style=ButtonDefault,
                ),
                "slip39_threshold",
                ButtonRequestType.ResetDevice,
            )
        )

        count = shares.input.count
        if confirmed:
            break

        text = "The threshold sets the number of shares "
        if group_id is None:
            text += "needed to recover your wallet. "
            text += f"Set it to {count} and you will need "
            if num_of_shares == 1:
                text += "1 share."
            elif num_of_shares == count:
                text += f"all {count} of your {num_of_shares} shares."
            else:
                text += f"any {count} of your {num_of_shares} shares."
        else:
            text += "needed to form a group. "
            text += f"Set it to {count} and you will "
            if num_of_shares == 1:
                text += "need 1 share "
            elif num_of_shares == count:
                text += f"need all {count} of {num_of_shares} shares "
            else:
                text += f"need any {count} of {num_of_shares} shares "
            text += f"to form Group {group_id + 1}."
        info = InfoConfirm(text)
        await info

    return count


async def slip39_prompt_number_of_shares(
    ctx: wire.GenericContext, group_id: int | None = None
) -> int:
    count = 5
    min_count = 1
    max_count = 16

    while True:
        shares = Slip39NumInput(
            Slip39NumInput.SET_SHARES, count, min_count, max_count, group_id
        )
        confirmed = is_confirmed(
            await interact(
                ctx,
                Confirm(
                    shares,
                    confirm="Continue",
                    cancel="Info",
                    major_confirm=True,
                    cancel_style=ButtonDefault,
                ),
                "slip39_shares",
                ButtonRequestType.ResetDevice,
            )
        )
        count = shares.input.count
        if confirmed:
            break

        if group_id is None:
            info = InfoConfirm(
                "Each recovery share is a "
                "sequence of 20 words. "
                "Next you will choose "
                "how many shares you "
                "need to recover your "
                "wallet."
            )
        else:
            info = InfoConfirm(
                "Each recovery share is a "
                "sequence of 20 words. "
                "Next you will choose "
                "the threshold number of "
                "shares needed to form "
                f"Group {group_id + 1}."
            )
        await info

    return count


async def slip39_advanced_prompt_number_of_groups(ctx: wire.GenericContext) -> int:
    count = 5
    min_count = 2
    max_count = 16

    while True:
        shares = Slip39NumInput(Slip39NumInput.SET_GROUPS, count, min_count, max_count)
        confirmed = is_confirmed(
            await interact(
                ctx,
                Confirm(
                    shares,
                    confirm="Continue",
                    cancel="Info",
                    major_confirm=True,
                    cancel_style=ButtonDefault,
                ),
                "slip39_groups",
                ButtonRequestType.ResetDevice,
            )
        )
        count = shares.input.count
        if confirmed:
            break

        info = InfoConfirm(
            "Each group has a set "
            "number of shares and "
            "its own threshold. In the "
            "next steps you will set "
            "the numbers of shares "
            "and the thresholds."
        )
        await info

    return count


async def slip39_advanced_prompt_group_threshold(
    ctx: wire.GenericContext, num_of_groups: int
) -> int:
    count = num_of_groups // 2 + 1
    min_count = 1
    max_count = num_of_groups

    while True:
        shares = Slip39NumInput(
            Slip39NumInput.SET_GROUP_THRESHOLD, count, min_count, max_count
        )
        confirmed = is_confirmed(
            await interact(
                ctx,
                Confirm(
                    shares,
                    confirm="Continue",
                    cancel="Info",
                    major_confirm=True,
                    cancel_style=ButtonDefault,
                ),
                "slip39_group_threshold",
                ButtonRequestType.ResetDevice,
            )
        )
        count = shares.input.count
        if confirmed:
            break
        else:
            info = InfoConfirm(
                "The group threshold "
                "specifies the number of "
                "groups required to "
                "recover your wallet. "
            )
            await info

    return count
