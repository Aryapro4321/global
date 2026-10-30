# ba_meta require api 9

from __future__ import annotations

import bascenev1 as ba
import babase
import bauiv1 as bui
from bauiv1lib import party


MOD_NAME = 'SpamButton'

CREATOR_TEXT = (
    'Mod:SpamButton Creator:Belingham '
    'Id Telegram:@Darkofgang: ON'
)

SPAM_MESSAGE = 'Spam!'
SPAM_INTERVAL = 0.5
SPAM_MAX_COUNT = 50

_SPAM_PLUGIN = None
_SPAM_WINDOW = None


def _load_spam_settings():
    try:
        saved = babase.app.config.get('BSLifeSpamButton_Settings', {})
        if isinstance(saved, dict):
            return {
                'message': str(saved.get('message', SPAM_MESSAGE)),
                'interval': float(saved.get('interval', SPAM_INTERVAL)),
                'count': int(saved.get('count', SPAM_MAX_COUNT)),
            }
    except Exception as exc:
        print('SPAM LOAD ERROR:', repr(exc))
    return {'message': SPAM_MESSAGE, 'interval': SPAM_INTERVAL, 'count': SPAM_MAX_COUNT}


def _save_spam_settings(data):
    try:
        babase.app.config['BSLifeSpamButton_Settings'] = data
        babase.app.config.commit()
    except Exception as exc:
        print('SPAM SAVE ERROR:', repr(exc))


# ============================================================
# SETTINGS WINDOW
# ============================================================

class SpamSettingsWindow:

    def __init__(self):
        global _SPAM_WINDOW

        self._root_widget = bui.containerwidget(size=(520, 440), transition='in_scale')

        bui.textwidget(
            parent=self._root_widget, position=(0, 390), size=(520, 35),
            text='SPAM SETTINGS', h_align='center', v_align='center', scale=1.0,
        )

        bui.textwidget(
            parent=self._root_widget, position=(20, 365), size=(480, 22),
            text=CREATOR_TEXT, h_align='center', v_align='center', scale=0.42,
        )

        bui.textwidget(
            parent=self._root_widget, position=(40, 325), size=(440, 30),
            text='Message To Spam', h_align='center', v_align='center', scale=0.72,
        )

        self._msg_field = bui.textwidget(
            parent=self._root_widget, position=(60, 275), size=(400, 45),
            editable=True, text=self._plugin_msg(),
            h_align='center', v_align='center', scale=0.85,
        )

        bui.textwidget(
            parent=self._root_widget, position=(40, 235), size=(200, 30),
            text='Interval (sec)', h_align='center', v_align='center', scale=0.70,
        )

        self._interval_field = bui.textwidget(
            parent=self._root_widget, position=(60, 190), size=(180, 42),
            editable=True, text=str(self._plugin_interval()),
            h_align='center', v_align='center', scale=0.85,
        )

        bui.textwidget(
            parent=self._root_widget, position=(290, 235), size=(200, 30),
            text='Max Count', h_align='center', v_align='center', scale=0.70,
        )

        self._count_field = bui.textwidget(
            parent=self._root_widget, position=(290, 190), size=(180, 42),
            editable=True, text=str(self._plugin_count()),
            h_align='center', v_align='center', scale=0.85,
        )

        bui.buttonwidget(
            parent=self._root_widget, position=(145, 130), size=(230, 50),
            label='SAVE', button_type='square', autoselect=True, text_scale=0.65,
            on_activate_call=bui.Call(self._save),
        )

        close_button = bui.buttonwidget(
            parent=self._root_widget, position=(180, 12), size=(160, 42),
            label='CLOSE', button_type='square', autoselect=True, text_scale=0.65,
            on_activate_call=bui.Call(self._close),
        )

        try:
            bui.containerwidget(edit=self._root_widget, cancel_button=close_button)
        except Exception:
            pass

    def _plugin_msg(self):
        return _SPAM_PLUGIN._message if _SPAM_PLUGIN else SPAM_MESSAGE

    def _plugin_interval(self):
        return _SPAM_PLUGIN._interval if _SPAM_PLUGIN else SPAM_INTERVAL

    def _plugin_count(self):
        return _SPAM_PLUGIN._max_count if _SPAM_PLUGIN else SPAM_MAX_COUNT

    def _save(self):
        try:
            msg = str(bui.textwidget(query=self._msg_field)).strip()
            interval_text = str(bui.textwidget(query=self._interval_field)).strip()
            count_text = str(bui.textwidget(query=self._count_field)).strip()
        except Exception:
            return

        if not msg:
            ba.screenmessage('ENTER MESSAGE', color=(1.0, 0.3, 0.3))
            return

        try:
            interval = max(0.1, float(interval_text))
        except Exception:
            ba.screenmessage('INVALID INTERVAL', color=(1.0, 0.3, 0.3))
            return

        try:
            count = max(1, int(count_text))
        except Exception:
            ba.screenmessage('INVALID COUNT', color=(1.0, 0.3, 0.3))
            return

        if _SPAM_PLUGIN:
            _SPAM_PLUGIN._message = msg
            _SPAM_PLUGIN._interval = interval
            _SPAM_PLUGIN._max_count = count
            _save_spam_settings({'message': msg, 'interval': interval, 'count': count})

        ba.screenmessage('SPAM SETTINGS SAVED', color=(0.2, 1.0, 0.2))

    def _close(self):
        global _SPAM_WINDOW
        try:
            bui.containerwidget(edit=self._root_widget, transition='out_scale')
        except Exception:
            pass
        _SPAM_WINDOW = None


def _open_spam_settings():
    global _SPAM_WINDOW
    if _SPAM_WINDOW is not None:
        return
    try:
        _SPAM_WINDOW = SpamSettingsWindow()
    except Exception as exc:
        print('SPAM SETTINGS OPEN ERROR:', repr(exc))


# ============================================================
# SPAM BUTTON
# ============================================================

def _update_spam_button(window):
    button = getattr(window, '_spam_button', None)
    if button is None:
        return
    active = _SPAM_PLUGIN is not None and _SPAM_PLUGIN._spamming
    try:
        bui.buttonwidget(
            edit=button,
            label='STOP SPAM' if active else 'SPAM',
            color=(0.9, 0.2, 0.2) if active else (0.8, 0.3, 0.3),
        )
    except Exception:
        pass


def _toggle_spam(window):
    plugin = _SPAM_PLUGIN
    if plugin is None:
        return
    if plugin._spamming:
        plugin.stop_spam()
    else:
        plugin.start_spam()
    _update_spam_button(window)


# ============================================================
# PARTY UI
# ============================================================

_previous_party_init = party.PartyWindow.__init__


def _spam_party_init(self, origin=(0, 0)):
    _previous_party_init(self, origin)
    try:
        if getattr(self, '_spam_added', False):
            return
        self._spam_added = True

        bui.textwidget(
            parent=self._root_widget, position=(20, 18), size=(380, 22),
            text=CREATOR_TEXT, h_align='left', v_align='center', scale=0.38,
        )

        self._spam_button = bui.buttonwidget(
            parent=self._root_widget, position=(320, 156), size=(90, 35),
            scale=0.75, label='SPAM', button_type='square', autoselect=True,
            text_scale=0.48, color=(0.8, 0.3, 0.3),
            on_activate_call=bui.Call(_toggle_spam, self),
        )

        bui.buttonwidget(
            parent=self._root_widget, position=(320, 199), size=(90, 35),
            scale=0.75, label='SPAM CFG', button_type='square', autoselect=True,
            text_scale=0.43,
            on_activate_call=bui.Call(_open_spam_settings),
        )

    except Exception as exc:
        print('SPAM PARTY BUTTON ERROR:', repr(exc))


if not getattr(party.PartyWindow, '_spam_init_patch', False):
    party.PartyWindow.__init__ = _spam_party_init
    party.PartyWindow._spam_init_patch = True


# ============================================================
# PLUGIN
# ============================================================

# ba_meta export babase.Plugin
class SpamButton(babase.Plugin):

    def __init__(self):
        global _SPAM_PLUGIN
        _SPAM_PLUGIN = self

        settings = _load_spam_settings()
        self._message = settings['message']
        self._interval = settings['interval']
        self._max_count = settings['count']

        self._spamming = False
        self._sent_count = 0
        self._timer = None

        ba.screenmessage(CREATOR_TEXT, color=(0.2, 1.0, 0.2))

    def start_spam(self):
        if self._spamming:
            return
        if not self._message.strip():
            ba.screenmessage('SPAM MESSAGE EMPTY', color=(1.0, 0.3, 0.3))
            return

        self._spamming = True
        self._sent_count = 0
        ba.screenmessage('SPAM STARTED', color=(0.2, 1.0, 0.2))
        self._schedule_next()

    def stop_spam(self):
        if not self._spamming:
            return
        self._spamming = False
        self._timer = None
        ba.screenmessage('SPAM STOPPED', color=(1.0, 0.3, 0.3))

    def _schedule_next(self):
        if not self._spamming:
            return

        if self._sent_count >= self._max_count:
            ba.screenmessage(
                'SPAM FINISHED ({} msgs)'.format(self._sent_count),
                color=(1.0, 0.7, 0.2),
            )
            self._spamming = False
            return

        # ✅ روش صحیح ارسال در API 9
        try:
            with babase.ContextRef.empty():
                ba.chatmessage(self._message)
            self._sent_count += 1
        except Exception as exc:
            print('SPAM SEND ERROR:', repr(exc))
            self._spamming = False
            return

        babase.apptimer(
            self._interval,
            babase.Call(self._schedule_next),
        )