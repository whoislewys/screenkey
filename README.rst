=====================
Screencast your keys.
=====================

.. contents::

A screencast tool to display your keys, inspired by Screenflick_.

This is an almost-complete rewrite of screenkey_ 0.2, featuring:

- Several keyboard translation methods
- Key composition/input method support
- Configurable font/size/position
- Highlighting of recent keystrokes
- Improved backspace processing
- Normal/Emacs/Mac caps modes
- Multi-monitor support
- Dynamic recording control
- Switch for visible shift and modifier sequences only
- Repeats compression
- Countless bug fixes


Installation and basic usage
----------------------------

Execute without installation::

  ./screenkey

To install::

  `python3 setup.py install`

Dependencies:

- Python 3.7
- cairo (`sudo apt-get install -y libcairo2-dev`)
- libGI (`sudo apt install libgirepository1.0-dev`)
- PyGTK
- Pycairo
- setuptools (build only)
- DistUtils-Extra (build only)
- slop (https://github.com/naelstrof/slop)
- FontAwesome_ (for multimedia symbols)
- Python AppIndicator (required for Unity / GNOME Shell)

Install dependencies (on Debian/Ubuntu)::

  sudo apt-get install python-gtk2 python-setuptools python-distutils-extra

You can also install "screenkey" via ArchLinux's AUR package:

https://aur.archlinux.org/packages/screenkey

Toggle to enable/disable
--------
`Shift+Shift` (left and right shift simultaneously)


Settings
--------

Display time:
  Persistence (in seconds) of the output window after typing has
  stopped. Defaults to 2.5 seconds. When the window is persistent,
  display time still controls the time before the text is cleared.

Persistent window:
  Forces the output window to be always visible, irregardless of typing
  activity. Mostly useful for interactive window placement and/or
  "fixed" positioning.

Screen:
  Physical screen/monitor used for the output window.

Position:
  Position of the output window. The position is normally relative to
  the chosen screen. If a window has been selected with "Select
  window/region", the position becomes relative to the window. If
  "fixed" is chosen, the output window's position and size are specified
  explicitly. See `Interactive placement`_ for more details.

Font:
  Font used for the output window. A scalable font and wide Unicode
  coverage is required (the DejaVu family is *highly* recommended).

Size:
  Size of the font used in the output window. Chooses proportionally
  between 8/12/24% of the screen size. When "fixed" positioning is used,
  size is ignored and the font will fill the available height of the
  output window.

Keyboard mode:
  Choose the translation method of keyboard events.

  "Composed" attempts to show only the final results of key composition.
  Dead keys and any intermediate output during composition is not shown.
  Currently works correctly with XIM/IBUS, but only for on-the-spot
  editing. It can cause problems with complex input methods (support for
  wider compatibility is underway).

  "Translated" shows the result of each keypress on the keyboard,
  accounting for the current keyboard locale and modifiers, but not
  composition. Pressing a dead key followed by a letter will show both
  keys.

  "Raw" shows which key caps were pressed on the keyboard, without
  translation. For example, typing "!" (which is often located on top of
  the key "1") requires pressing "Shift+1", which is what this output
  mode shows. "Backspace mode", "Always visible Shift" and "Modifiers
  only" have no effect in this mode.

  "Keysyms" shows the keysyms ("symbolic" names) of each pressed key as
  received by the server. Mostly useful for debugging.

Backspace mode:
  Controls the effect of "backspace" on the text in the output window.

  "Normal" always inserts a backspace symbol in the output window.

  "Baked" simulates the effect of backspace in the text only if the last
  keypress is a regular letter and no caret movement has been detected.
  In any other case, a backspace symbol is inserted instead.

  "Full" is similar to "baked", but will eat through several other, less
  safe keys, such as tabs and returns.

Modifiers mode:
  Select how modifiers keys (such as Control, Alt) are displayed in the
  output window. "Normal" uses traditional PC names (Ctrl+A) while "Mac"
  uses Mac symbols directly (⌘+A). The "Emacs" mode will display
  Emacs-style shortened keyboard sequences (C-A).

Show Modifier sequences only:
  Only show modifier/control sequences in the output window.
  Bare, shifted or translated letters are not shown.

Always show Shift:
  Shift is normally hidden when the control sequence includes a letter
  that can differentiate between a shifted/non-shifted key. For example,
  Shift + "Control+a" is normally shown just as "Control+A" (notice the
  capital "A").

  When "Always show Shift" is used, Shift is always included in modifier
  sequences, if pressed. Has no effect when using the "Emacs" modifiers
  mode.

Show Whitespace characters:
  Convert regular whitespace characters (tabs and spaces) to a visible
  representation instead of showing a blank. Newlines are also hidden
  when unambiguous in multiline mode.

Compress repeats:
  When enabled, contiguous repeated sequences are truncated after the
  requested threshold. A counter of total occurrences is shown instead,
  which is generally more legible.


Advanced usage
--------------

Controlling visibility
~~~~~~~~~~~~~~~~~~~~~~

To disable screenkey while recording (for example, during password
prompts), press both control keys, or both shift keys, or both alt keys
at the same time.

Press the same combination again to resume it.

This has the same effect of toggling the state from the system tray
icon, but it's completely stealth: there's no feedback that screenkey is
being switched on/off.

If you need the viewer to focus on a sentence you just typed, you can
press a silent modifier (such as Shift, or Control) to keep the output
window visible a little longer without prolonging the default timeout.


Interactive placement
~~~~~~~~~~~~~~~~~~~~~

screenkey is normally positioned on the top/center/bottom part of the
screen.

If you're recording a screencast only for a specific application, you
can click on "Select window/region" to select on which window the output
should be overlaid (slop_ must be installed for this task). When a
window has been selected, top/center/bottom refer to the window's
contents. Press "Reset" to restore the original behavior.

When "fixed" is chosen, the position of the output is specified
*directly*. The cursor turns immediately into a crossbar: drag over the
desired screen region (where the text should appear), or press "Esc" to
abort. Again, press "Reset" to restore the original behavior.


Command-line placement
~~~~~~~~~~~~~~~~~~~~~~

The "geometry" argument follows the standard X11 geometry format
(``WxH[+X+Y]``) and can be provided by slop_, which allows to select
windows and/or drag over the desired region interactively without the
need of calculating the coordinates manually.

When a geometry argument has been provided, the position
(top/middle/bottom) becomes relative to the selected rectangle. For
example, to overlay screenkey on top of an existing window, you can
simply do::

  ./screenkey -g $(slop -n -f '%g')

To set the actual text rectangle instead, use "fixed" positioning. Using
slop, you can combine both and simply drag the desired rectangle during
selection::

  ./screenkey -p fixed -g $(slop -n -f '%g')


Choosing a good font
~~~~~~~~~~~~~~~~~~~~

The default font is "Sans Bold", which is usually mapped to "DejaVu
Sans" on most Linux installations (look for the ``ttf-dejavu`` package).
It's a good all-around font which provides all the required glyphs and
has *excellent* readability.

For screencasts about programming, we recommend "DejaVu Sans Mono Bold"
instead, which provides better differentiation among similar letterforms
(0/O, I/l, etc).


Multimedia keys
~~~~~~~~~~~~~~~

"screenkey" supports several multimedia keys. To display them with
symbols instead of text abbreviations, FontAwesome_ needs to be
installed.

On Debian/Ubuntu, the font is available in the ``fonts-font-awesome``
package. On Arch Linux the package is instead ``ttf-font-awesome``.

.. _FontAwesome: http://fontawesome.io/


Tiling window managers
~~~~~~~~~~~~~~~~~~~~~~

"screenkey" should work correctly by default with any tiling window
manager.

The original version of screenkey used to require customization for the
output window to work/float correctly. These settings are *no longer
required* with this fork, and can be safely removed.

If you don't have a system tray, you can either configure screenkey
through command line flags or use ``--show-settings`` to test the
configuration interactively.

To get transparency you need a compositor to be running. For example,
"compton" or "unagi" are popular for their low impact on performance,
but "xcompmgr" also works correctly without any additional
configuration.


Related tools
~~~~~~~~~~~~~

If you're recording a screencast where almost all editing is already
visible (for example, in ``vi`` or most other text editors), consider
using a bigger screen font instead, so that the viewer can read the text
directly while the program is being used.

If the control sequences you're typing are rare, you might even want to
spell what you're doing instead of obscuring the screen with the typing
output.

When doing screencasts involving a lot of mouse activity, or which
require holding down modifiers to perform other mouse actions, key-mon_
might be a good companion to screenkey, or replace it entirely.

key-mon can be configured to show the state of key modifiers
continuously and circle the location of mouse clicks ("visible click").
key-mon and screenkey complete each-other and can be used at the same
time.


Troubleshooting
---------------

Initialization failure
~~~~~~~~~~~~~~~~~~~~~~

Screenkey is very sensitive to improperly configured input methods or
keyboard settings. Installing, removing or "playing around" with some
packages such as ``im-config``, ``ibus``, ``fcitx`` or ``scim`` might
leave the current settings in a half-broken state. Some distributions
are also known to have broken settings by *default*.

In short: the various environment flags (``XMODIFIERS``,
``GTK_IM_MODULE``, ``QT_IM_MODULE`` to name a few) need to be
*consistent*. They either should be all unset, or all set to the *same*
input method. When using ``ibus``, ``fcitx`` or other complex methods,
the corresponding daemon *must* be running.

An "input method" is the mechanism which handles the task of
transforming key presses into characters. Latin languages mostly use a
straightforward key -> character mechanism, but other languages don't
have a key for each possible character and thus need extra logic.
Programs need to be told *which* input method to use, and this is
usually done through environment variables. There is one environment
variable for each graphical toolkit and it's set at the start of the
session, usually by a command in the ``~/.profile`` file. Screenkey can
only record a program correctly if it's using the *same* input method as
the target.

To check the status of the environment, run the following inside a
terminal::

  echo XMODIFIERS=$XMODIFIERS
  echo GTK_IM_MODULE=$GTK_IM_MODULE
  echo QT_IM_MODULE=$QT_IM_MODULE

On a system with a Latin language and without any complex input method
running you should see everything empty::

  XMODIFIERS=
  GTK_IM_MODULE=
  QT_IM_MODULE=

On a system running "ibus" you should see::

  XMODIFIERS=@im=ibus
  GTK_IM_MODULE=ibus
  QT_IM_MODULE=ibus

Additionally, the ibus package must be installed and the ibus daemon
should be running. Check the output of::

  $ pgrep -ax ibus-daemon
  982 /usr/bin/ibus-daemon --xim

``ibus-daemon`` should be present and *must* include ``--xim`` in the
command line. If not, the daemon must be restarted with it! Consult the
documentation of your distribution for more information.

On a system using "fcitx" the following output has to be expected::

  XMODIFIERS=@im=fcitx
  GTK_IM_MODULE=fcitx
  QT_IM_MODULE=fcitx

In this case ``fcitx`` daemon should be running as well::

  $ pgrep -ax fcitx
  1053 /usr/bin/fcitx

If you see *any* mixture of the above, your system is likely to be
incorrectly configured.

If the "ibus" or "fcitx" packages are not installed, there are no
daemons running and the variables are mostly empty, then try simply
unsetting all of them before running Screenkey in a terminal::

  unset XMODIFIERS
  unset GTK_IM_MODULES
  unset QT_IM_MODULES
  screenkey

If screenkey runs correctly after these changes, check your startup
files such as ``~/.profile``, ``~/.bash_profile`` or
``~/.pam_environment`` and remove the offending variables to make the
change permanent. You must log-out and log-in in order to be able to run
Screenkey normally after the change.

If you're running either ``ibus`` or ``fcitx`` but the variables contain
mixed values, try to reset them manually using::

  export XMODIFIERS=@im=ibus
  export GTK_IM_MODULE=ibus
  export QT_IM_MODULE=ibus
  screenkey

Again, if Screenkey works correctly after the change, inspect the
contents of your startup files as above to make the change permanent.

You should always check the documentation of your distribution to see
which input method *should* be running and how it should be configured.
The above guide is not meant to be exhaustive. If nothing works, get in
touch with the authors or file an issue on Gitlab to get more help.


Cannot stop Screenkey or no status icon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can exit from Screenkey by right-clicking on it's status icon and
selecting "Quit".

If you're using GNOME/Unity and cannot see any status icon please make
sure the ``python-appindicator`` package is installed. Run the following
inside a terminal to install as required::

  sudo apt-get install python-appindicator

On any other desktop system Screenkey uses the regular system tray. If
you don't have a systray or you cannot quit an existing Screenkey, use
the following command in a terminal to kill it::

  pkill -f screenkey

The proper way to exit when running Screenkey from a terminal is simply
by interrupting it with ``Ctrl+C``.


No output in GNOME Terminal
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Screenkey cannot currently capture any input directed to native Wayland
programs such as the GNOME Terminal: only X11 programs are supported.

If you need to record a terminal session you'll have to switch to
another X11 terminal emulator such as xterm, urxvt, mlterm, ...


Authors and Copyright
---------------------

"screenkey" can be found at https://www.thregr.org/~wavexx/software/screenkey/

| "screenkey" is distributed under GNU GPLv3+, WITHOUT ANY WARRANTY.
| Copyright(c) 2010-2012: Pablo Seminario <pabluk@gmail.com>
| Copyright(c) 2015-2016: wave++ "Yuri D'Elia" <wavexx@thregr.org>.

screenkey's GIT repository is publicly accessible at:

https://gitlab.com/wavexx/screenkey


Additional Thanks
-----------------

* Benjamin Chrétien
* Dmitry Bushev
* Doug Patti
* Igor Bronovskyi
* Ivan Makfinsky
* Jacob Gardner
* Muneeb Shaikh
* Stanislav Seletskiy
* farrer (launchpad)
* zhum (launchpad)
* 伊冲


.. _Screenflick: http://www.araelium.com/screenflick/
.. _key-mon: https://code.google.com/p/key-mon/
.. _screenkey: https://launchpad.net/screenkey
.. _slop: https://github.com/naelstrof/slop
