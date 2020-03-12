# -*- coding: utf-8 -*-
# "screenkey" is distributed under GNU GPLv3+, WITHOUT ANY WARRANTY.
# Copyright(c) 2010-2012: Pablo Seminario <pabluk@gmail.com>
# Copyright(c) 2015-2016: wave++ "Yuri D'Elia" <wavexx@thregr.org>.

from . import *
from .labelmanager import LabelManager

from threading import Timer
import json
import os
import subprocess

import gi
# gi.require_version('Gtk', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('Pango', '1.0')

from gi.repository import GLib
GLib.threads_init()

from gi.repository import Gtk, Gdk, Pango
import cairo


START = Gtk.Align.START
CENTER = Gtk.Align.CENTER
END = Gtk.Align.END
FILL =Gtk.Align.FILL
TOP = Gtk.PositionType.TOP
BOTTOM = Gtk.PositionType.BOTTOM
RIGHT = Gtk.PositionType.RIGHT
LEFT = Gtk.PositionType.LEFT
HORIZONTAL = Gtk.Orientation.HORIZONTAL
VERTICAL = Gtk.Orientation.VERTICAL
IF_VALID = Gtk.SpinButtonUpdatePolicy.IF_VALID


class Screenkey(Gtk.Window):
    STATE_FILE = os.path.join(GLib.get_user_config_dir(), 'screenkey.json')

    def __init__(self, logger, options, show_settings=False):
        Gtk.Window.__init__(self, Gtk.WindowType.POPUP)

        self.exit_status = None
        self.timer_hide = None
        self.timer_min = None
        self.logger = logger

        defaults = Options({'no_systray': False,
                            'timeout': 2.5,
                            'recent_thr': 0.1,
                            'compr_cnt': 3,
                            'ignore': [],
                            'position': 'bottom',
                            'persist': False,
                            'font_desc': 'Sans Bold',
                            'font_size': 'medium',
                            'font_color': 'white',
                            'bg_color': 'black',
                            'opacity': 0.8,
                            'key_mode': 'composed',
                            'bak_mode': 'baked',
                            'mods_mode': 'normal',
                            'mods_only': False,
                            'multiline': False,
                            'vis_shift': False,
                            'vis_space': True,
                            'geometry': None,
                            'screen': 0})
        self.options = self.load_state()
        if self.options is None:
            self.options = defaults
        else:
            # copy missing defaults
            for k, v in defaults.items():
                if k not in self.options:
                    self.options[k] = v
        if options is not None:
            # override with values from constructor
            for k, v in options.items():
                if v is not None:
                    self.options[k] = v

        self.set_keep_above(True)
        self.set_accept_focus(False)
        self.set_focus_on_map(False)
        self.set_app_paintable(True)

        self.label = Gtk.Label()
        self.label.set_attributes(Pango.AttrList())
        self.label.set_ellipsize(Pango.EllipsizeMode.START)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.show()
        self.add(self.label)

        self.font = Pango.FontDescription(self.options.font_desc)
        self.update_colors()

        self.set_size_request(0, 0)
        self.set_gravity(Gdk.Gravity.CENTER)
        self.connect("configure-event", self.on_configure)
        self.connect("draw", self.on_draw)

        scr = self.get_screen()
        scr.connect("size-changed", self.on_configure)
        scr.connect("monitors-changed", self.on_monitors_changed)
        self.set_active_monitor(self.options.screen)

        visual = scr.get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        self.labelmngr = None
        self.enabled = True
        self.on_change_mode()

        self.make_menu()
        self.make_about_dialog()
        self.make_preferences_dialog()

        if not self.options.no_systray:
            self.make_systray()

        self.connect("delete-event", self.quit)
        if show_settings:
            self.on_preferences_dialog()
        if self.options.persist:
            self.show()


    def quit(self, widget=None, data=None, exit_status=os.EX_OK):
        self.labelmngr.stop()
        self.exit_status = exit_status
        Gtk.main_quit()


    def load_state(self):
        """Load stored options"""
        options = None
        try:
            with open(self.STATE_FILE, 'r') as f:
                options = Options(json.load(f))
                self.logger.debug("Options loaded.")
        except IOError:
            self.logger.debug("file %s does not exists." % self.STATE_FILE)
        except ValueError:
            self.logger.debug("file %s is invalid." % self.STATE_FILE)

        # compatibility with previous versions (0.5)
        if options and options.key_mode == 'normal':
            options.key_mode = 'composed'

        return options


    def store_state(self, options):
        """Store options"""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(options._store, f)
                self.logger.debug("Options saved.")
        except IOError:
            self.logger.debug("Cannot open %s." % self.STATE_FILE)


    def set_active_monitor(self, monitor):
        scr = self.get_screen()
        if monitor >= scr.get_n_monitors():
            self.monitor = 0
        else:
            self.monitor = monitor
        self.update_geometry()


    def on_monitors_changed(self, *_):
        self.set_active_monitor(self.monitor)


    def update_font(self):
        _, window_height = self.get_size()
        text = self.label.get_text()
        lines = text.count('\n') + 1
        self.font.set_absolute_size((50 * window_height // lines // 100) * 1000)
        self.label.get_pango_context().set_font_description(self.font)


    def update_colors(self):
        self.label.modify_fg(Gtk.StateFlags.NORMAL, Gdk.color_parse(self.options.font_color))
        self.bg_color = Gdk.color_parse(self.options.bg_color)


    def on_draw(self, widget, cr):
        cr.set_source_rgba(self.bg_color.red_float,
                           self.bg_color.green_float,
                           self.bg_color.blue_float,
                           self.options.opacity)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        return False


    def on_configure(self, *_):
        window_x, window_y = self.get_position()
        window_width, window_height = self.get_size()

        # TODO: set event mask
        # mask = Gdk.Pixmap(None, window_width, window_height, 1)
        # gc = Gdk.GC(mask)
        # gc.set_foreground(Gdk.Color(pixel=0))
        # mask.draw_rectangle(gc, True, 0, 0, window_width, window_height)
        # self.input_shape_combine_mask(mask, 0, 0)

        # set some proportional inner padding
        self.label.set_padding(window_width // 100, 0)

        self.update_font()


    def update_geometry(self, configure=False):
        if self.options.position == 'fixed' and self.options.geometry is not None:
            self.move(*self.options.geometry[0:2])
            self.resize(*self.options.geometry[2:4])
            self.update_font()
            return

        if self.options.geometry is not None:
            area_geometry = self.options.geometry
        else:
            geometry = self.get_screen().get_monitor_geometry(self.monitor)
            area_geometry = [geometry.x, geometry.y, geometry.width, geometry.height]

        if self.options.font_size == 'large':
            window_height = 24 * area_geometry[3] // 100
        elif self.options.font_size == 'medium':
            window_height = 12 * area_geometry[3] // 100
        else:
            window_height = 8 * area_geometry[3] // 100
        self.resize(area_geometry[2], window_height)

        if self.options.position == 'top':
            window_y = area_geometry[1] + area_geometry[3] // 10
        elif self.options.position == 'center':
            window_y = area_geometry[1] + area_geometry[3] // 2 - window_height // 2
        else:
            window_y = area_geometry[1] + area_geometry[3] * 9 // 10 - window_height
        self.move(area_geometry[0], window_y)
        self.update_font()


    def on_statusicon_popup(self, widget, button, timestamp, data=None):
        if button == 3 and data:
            data.show()
            data.popup_at_pointer(None)


    def show(self):
        super(Screenkey, self).show()


    def on_labelmngr_error(self):
        msg = Gtk.MessageDialog(parent=self,
                                type=Gtk.MESSAGE_ERROR,
                                buttons=Gtk.BUTTONS_OK,
                                message_format="Error initializing Screenkey")
        text = _('Screenkey failed to initialize. This is usually a sign of an improperly '
                 'configured input method or desktop keyboard settings. Please see the <a '
                 'href="{url}">troubleshooting documentation</a> for further diagnosing '
                 'instructions.\n\nScreenkey cannot recover and will now quit!')
        msg.format_secondary_markup(text.format(url=ERROR_URL))
        msg.run()
        msg.destroy()
        self.quit(exit_status=os.EX_SOFTWARE)


    def on_label_change(self, markup):
        if markup is None:
            self.on_labelmngr_error()
            return

        _, attr, text, _ = Pango.parse_markup(markup, -1, ' ')
        self.label.set_text(text)
        self.label.set_attributes(attr)
        self.update_font()

        if not self.get_property('visible'):
            self.show()
        if self.timer_hide:
            self.timer_hide.cancel()
        if self.options.timeout > 0:
            self.timer_hide = Timer(self.options.timeout, self.on_timeout_main)
            self.timer_hide.start()
        if self.timer_min:
            self.timer_min.cancel()
        self.timer_min = Timer(self.options.recent_thr * 2, self.on_timeout_min)
        self.timer_min.start()


    def on_timeout_main(self):
        if not self.options.persist:
            self.hide()
        self.label.set_text('')
        self.labelmngr.clear()


    def on_timeout_min(self):
        self.label.set_attributes()


    def restart_labelmanager(self):
        self.logger.debug("Restarting LabelManager.")
        if self.labelmngr:
            self.labelmngr.stop()
        self.labelmngr = LabelManager(self.on_label_change, logger=self.logger,
                                      key_mode=self.options.key_mode,
                                      bak_mode=self.options.bak_mode,
                                      mods_mode=self.options.mods_mode,
                                      mods_only=self.options.mods_only,
                                      multiline=self.options.multiline,
                                      vis_shift=self.options.vis_shift,
                                      vis_space=self.options.vis_space,
                                      recent_thr=self.options.recent_thr,
                                      compr_cnt=self.options.compr_cnt,
                                      ignore=self.options.ignore,
                                      pango_ctx=self.label.get_pango_context())
        self.labelmngr.start()


    def on_change_mode(self):
        if not self.enabled:
            return
        self.restart_labelmanager()


    def on_show_keys(self, widget, data=None):
        self.enabled = widget.get_active()
        if self.enabled:
            self.logger.debug("Screenkey enabled.")
            self.restart_labelmanager()
        else:
            self.logger.debug("Screenkey disabled.")
            self.labelmngr.stop()


    def on_preferences_dialog(self, widget=None, data=None):
        self.prefs.show()


    def on_preferences_changed(self, widget=None, data=None):
        self.store_state(self.options)
        self.prefs.hide()
        return True


    def make_preferences_dialog(self):
        # TODO: switch to something declarative or at least clean-up the following mess
        self.prefs = prefs = Gtk.Dialog(APP_NAME, None,
                                        Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                        (Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE),
                                        use_header_bar=True,
                                        destroy_with_parent=True,
                                        resizable=False)
        prefs.connect("response", self.on_preferences_changed)
        prefs.connect("delete-event", self.on_preferences_changed)

        def on_sb_time_changed(widget, data=None):
            self.options.timeout = widget.get_value()
            self.logger.debug("Timeout value changed: %f." % self.options.timeout)

        def on_cbox_sizes_changed(widget, data=None):
            self.options.font_size = widget.props.active_id
            self.update_geometry()
            self.logger.debug("Window size changed: %s." % self.options.font_size)

        def on_cbox_modes_changed(widget, data=None):
            self.options.key_mode = widget.props.active_id
            self.on_change_mode()
            self.logger.debug("Key mode changed: %s." % self.options.key_mode)

        def on_cbox_bak_changed(widget, data=None):
            self.options.bak_mode = widget.props.active_id
            self.on_change_mode()
            self.logger.debug("Bak mode changed: %s." % self.options.bak_mode)

        def on_cbox_mods_changed(widget, data=None):
            self.options.mods_mode = widget.props.active_id
            self.on_change_mode()
            self.logger.debug("Mods mode changed: %s." % self.options.mods_mode)

        def on_cbox_modsonly_changed(widget, data=None):
            self.options.mods_only = widget.get_active()
            self.on_change_mode()
            self.logger.debug("Modifiers only changed: %s." % self.options.mods_only)

        def on_cbox_visshift_changed(widget, data=None):
            self.options.vis_shift = widget.get_active()
            self.on_change_mode()
            self.logger.debug("Visible Shift changed: %s." % self.options.vis_shift)

        def on_cbox_visspace_changed(widget, data=None):
            self.options.vis_space = widget.get_active()
            self.on_change_mode()
            self.logger.debug("Show Whitespace changed: %s." % self.options.vis_space)

        def on_cbox_position_changed(widget, data=None):
            new_position = widget.props.active_id
            if self.options.position != 'fixed' and new_position == 'fixed':
                new_geom = on_btn_sel_geom(widget)
                if not new_geom:
                    self.cbox_positions.props.active_id = self.options.position
                    return
            self.options.position = new_position
            self.update_geometry()
            self.logger.debug("Window position changed: %s." % self.options.position)

        def on_cbox_screen_changed(widget, data=None):
            self.options.screen = widget.get_active()
            self.set_active_monitor(self.options.screen)
            self.logger.debug("Screen changed: %d." % self.options.screen)

        def on_cbox_persist_changed(widget, data=None):
            self.options.persist = widget.get_active()
            if not self.get_property('visible'):
                self.show()
            else:
                self.on_label_change(self.label.get_text())
            self.logger.debug("Persistent changed: %s." % self.options.persist)

        def on_sb_compr_changed(widget, data=None):
            self.options.compr_cnt = widget.get_value_as_int()
            self.on_change_mode()
            self.logger.debug("Compress repeats value changed: %d." % self.options.compr_cnt)

        def on_cbox_compr_changed(widget, data=None):
            compr_enabled = widget.get_active()
            self.sb_compr.set_sensitive(compr_enabled)
            self.options.compr_cnt = self.sb_compr.get_value_as_int() if compr_enabled else 0
            self.on_change_mode()
            self.logger.debug("Compress repeats value changed: %d." % self.options.compr_cnt)

        def on_btn_sel_geom(widget, data=None):
            try:
                ret = subprocess.check_output(['slop', '-f', '%x %y %w %h %i'])
            except subprocess.CalledProcessError:
                return False
            except OSError:
                msg = Gtk.MessageDialog(parent=self,
                                        type=Gtk.MESSAGE_ERROR,
                                        buttons=Gtk.BUTTONS_OK,
                                        message_format="Error running \"slop\"")
                msg.format_secondary_markup(_("\"slop\" is required for interactive selection. "
                                              "See <a href=\"{url}\">{url}</a>").format(url=SLOP_URL))
                msg.run()
                msg.destroy()
                return False

            data = map(int, ret.split(' '))
            self.options.geometry = data[0:4]
            self.options.window = data[4]
            if not self.options.window or \
               self.options.window == self.get_screen().get_root_window().xid:
                # region selected, switch to fixed
                self.options.window = None
                self.options.position = 'fixed'
                self.cbox_positions.props.active_id = self.options.position

            self.update_geometry()
            self.btn_reset_geom.set_sensitive(True)
            return True

        def on_btn_reset_geom(widget, data=None):
            self.options.geometry = None
            if self.options.position == 'fixed':
                self.options.position = 'bottom'
                self.cbox_positions.props.active_id = self.options.position
            self.update_geometry()
            widget.set_sensitive(False)

        def on_adj_opacity_changed(widget, data=None):
            self.options.opacity = widget.get_value()
            self.update_colors()

        def on_font_color_changed(widget, data=None):
            self.options.font_color = widget.get_color().to_string()
            self.update_colors()

        def on_bg_color_changed(widget, data=None):
            self.options.bg_color = widget.get_color().to_string()
            self.update_colors()

        def on_btn_font(widget, data=None):
            widget.props.label = widget.props.font
            self.options.font_desc = widget.props.font
            self.font = widget.props.font_desc
            self.update_font()

        frm_time = Gtk.Frame(label_widget=Gtk.Label("<b>%s</b>" % _("Time"),
                                                    use_markup=True),
                             border_width=4,
                             shadow_type=Gtk.ShadowType.NONE,
                             margin=6, hexpand=True)
        vbox_time = Gtk.Grid(orientation=VERTICAL,
                             row_spacing=6, margin=6)
        hbox_time = Gtk.Grid(column_spacing=6)
        lbl_time1 = Gtk.Label(_("Display for"))
        lbl_time2 = Gtk.Label(_("seconds"))
        sb_time = Gtk.SpinButton(digits=1,
                                 numeric=True,
                                 update_policy=IF_VALID,
                                 value=self.options.timeout)
        sb_time.set_increments(0.5, 1.0)
        sb_time.set_range(0.5, 10.0)
        sb_time.connect("value-changed", on_sb_time_changed)
        hbox_time.add(lbl_time1)
        hbox_time.add(sb_time)
        hbox_time.add(lbl_time2)
        vbox_time.add(hbox_time)

        chk_persist = Gtk.CheckButton(_("Persistent window"),
                                      active=self.options.persist)
        chk_persist.connect("toggled", on_cbox_persist_changed)
        vbox_time.add(chk_persist)

        frm_time.add(vbox_time)

        frm_position = Gtk.Frame(label_widget=Gtk.Label("<b>%s</b>" % _("Position"),
                                                        use_markup=True),
                                 border_width=4,
                                 shadow_type=Gtk.ShadowType.NONE,
                                 margin=6, hexpand=True)
        grid_position = Gtk.Grid(row_spacing=6, column_spacing=6,
                                 margin=6)

        lbl_screen = Gtk.Label(_("Screen"),
                               halign=START)
        cbox_screen = Gtk.ComboBoxText()
        scr = self.get_screen()
        for i in range(scr.get_n_monitors()):
            cbox_screen.insert_text(i, '%d: %s' % (i, scr.get_monitor_plug_name(i)))
        cbox_screen.set_active(self.monitor)
        cbox_screen.connect("changed", on_cbox_screen_changed)

        lbl_positions = Gtk.Label(_("Position"),
                                  halign=START)
        self.cbox_positions = Gtk.ComboBoxText(name='position')
        for id_, text in POSITIONS.items():
            self.cbox_positions.append(id_, text)
            if id_ == self.options.position:
                self.cbox_positions.props.active_id = id_
        self.cbox_positions.connect("changed", on_cbox_position_changed)

        self.btn_reset_geom = Gtk.Button(_("Reset"))
        self.btn_reset_geom.connect("clicked", on_btn_reset_geom)
        self.btn_reset_geom.set_sensitive(self.options.geometry is not None)

        hbox_position = Gtk.Grid(column_spacing=6, halign=END)
        hbox_position.add(self.cbox_positions)
        hbox_position.add(self.btn_reset_geom)

        btn_sel_geom = Gtk.Button(_("Select window/region"),
                                  halign=FILL, hexpand=True)
        btn_sel_geom.connect("clicked", on_btn_sel_geom)

        grid_position.add(lbl_screen)
        grid_position.attach_next_to(cbox_screen, lbl_screen, RIGHT, 1, 1)
        grid_position.attach_next_to(lbl_positions, lbl_screen, BOTTOM, 1, 1)
        grid_position.attach_next_to(hbox_position, lbl_positions, RIGHT, 1, 1)
        grid_position.attach_next_to(btn_sel_geom, lbl_positions, BOTTOM, 2, 1)

        frm_aspect = Gtk.Frame(label_widget=Gtk.Label("<b>%s</b>" % _("Font"),
                                                      use_markup=True),
                               border_width=4,
                               shadow_type=Gtk.ShadowType.NONE,
                               margin=6, hexpand=True)
        grid_aspect = Gtk.Grid(row_spacing=6, column_spacing=6,
                               margin=6)

        frm_position.add(grid_position)

        lbl_font = Gtk.Label(_("Font"),
                             hexpand=True, halign=START)
        btn_font = Gtk.FontButton(self.options.font_desc,
                                  font=self.options.font_desc,
                                  level=Gtk.FontChooserLevel.STYLE,
                                  use_font=True, show_size=False)
        btn_font.connect("font-set", on_btn_font)

        lbl_sizes = Gtk.Label(_("Size"),
                              halign=START)
        cbox_sizes = Gtk.ComboBoxText(name='size')
        for id_, text in FONT_SIZES.items():
            cbox_sizes.append(id_, text)
            if id_ == self.options.font_size:
                cbox_sizes.props.active_id = id_
        cbox_sizes.connect("changed", on_cbox_sizes_changed)

        grid_aspect.add(lbl_font)
        grid_aspect.attach_next_to(btn_font, lbl_font, RIGHT, 1, 1)
        grid_aspect.attach_next_to(lbl_sizes, lbl_font, BOTTOM, 1, 1)
        grid_aspect.attach_next_to(cbox_sizes, lbl_sizes, RIGHT, 1, 1)
        frm_aspect.add(grid_aspect)

        frm_kbd = Gtk.Frame(label_widget=Gtk.Label("<b>%s</b>" % _("Keys"),
                                                   use_markup=True),
                            border_width=4,
                            shadow_type=Gtk.ShadowType.NONE,
                            margin=6)
        grid_kbd = Gtk.Grid(row_spacing=6, column_spacing=6,
                            margin=6)

        lbl_modes = Gtk.Label(_("Keyboard mode"),
                              halign=START)
        cbox_modes = Gtk.ComboBoxText(name='mode')
        for id_, text in KEY_MODES.items():
            cbox_modes.append(id_, text)
            if id_ == self.options.key_mode:
                cbox_modes.props.active_id = id_
        cbox_modes.connect("changed", on_cbox_modes_changed)

        lbl_bak = Gtk.Label(_("Backspace mode"),
                            halign=START)
        cbox_bak = Gtk.ComboBoxText()
        for id_, text in BAK_MODES.items():
            cbox_bak.append(id_, text)
            if id_ == self.options.bak_mode:
                cbox_bak.props.active_id = id_
        cbox_bak.connect("changed", on_cbox_bak_changed)

        lbl_mods = Gtk.Label(_("Modifiers mode"),
                             halign=START)
        cbox_mods = Gtk.ComboBoxText()
        for id_, text in MODS_MODES.items():
            cbox_mods.append(id_, text)
            if id_ == self.options.mods_mode:
                cbox_mods.props.active_id = id_
        cbox_mods.connect("changed", on_cbox_mods_changed)

        chk_modsonly = Gtk.CheckButton(_("Show Modifier sequences only"),
                                       active=self.options.mods_only)
        chk_modsonly.connect("toggled", on_cbox_modsonly_changed)

        chk_visshift = Gtk.CheckButton(_("Always show Shift"),
                                       active=self.options.vis_shift)
        chk_visshift.connect("toggled", on_cbox_visshift_changed)

        chk_visspace = Gtk.CheckButton(_("Show Whitespace characters"),
                                       active=self.options.vis_space)
        chk_visspace.connect("toggled", on_cbox_visspace_changed)

        hbox_compr = Gtk.Grid(column_spacing=6)
        chk_compr = Gtk.CheckButton(_("Compress repeats after"),
                                    active=self.options.compr_cnt > 0)
        chk_compr.connect("toggled", on_cbox_compr_changed)
        self.sb_compr = Gtk.SpinButton(digits=0,
                                       numeric=True,
                                       update_policy=IF_VALID,
                                       value=self.options.compr_cnt or 3)
        self.sb_compr.set_increments(1, 1)
        self.sb_compr.set_range(1, 100)
        self.sb_compr.connect("value-changed", on_sb_compr_changed)
        hbox_compr.add(chk_compr)
        hbox_compr.add(self.sb_compr)

        grid_kbd.add(lbl_modes)
        grid_kbd.attach_next_to(cbox_modes, lbl_modes, RIGHT, 1, 1)
        grid_kbd.attach_next_to(lbl_bak, lbl_modes, BOTTOM, 1, 1)
        grid_kbd.attach_next_to(cbox_bak, lbl_bak, RIGHT, 1, 1)
        grid_kbd.attach_next_to(lbl_mods, lbl_bak, BOTTOM, 1, 1)
        grid_kbd.attach_next_to(cbox_mods, lbl_mods, RIGHT, 1, 1)
        grid_kbd.attach_next_to(chk_modsonly, lbl_mods, BOTTOM, 2, 1)
        grid_kbd.attach_next_to(chk_visshift, chk_modsonly, BOTTOM, 2, 1)
        grid_kbd.attach_next_to(chk_visspace, chk_visshift, BOTTOM, 2, 1)
        grid_kbd.attach_next_to(hbox_compr, chk_visspace, BOTTOM, 2, 1)
        frm_kbd.add(grid_kbd)

        frm_color = Gtk.Frame(label_widget=Gtk.Label("<b>%s</b>" % _("Color"),
                                                     use_markup=True),
                              border_width=4,
                              shadow_type=Gtk.ShadowType.NONE,
                              margin=6)
        grid_color = Gtk.Grid(orientation=VERTICAL,
                              row_spacing=6, column_spacing=6,
                              margin=6)

        lbl_font_color = Gtk.Label(_("Font color"),
                                   halign=START)
        btn_font_color = Gtk.ColorButton(color=Gdk.color_parse(self.options.font_color),
                                         title=_("Text color"),
                                         halign=END)
        btn_font_color.connect("color-set", on_font_color_changed)

        lbl_bg_color = Gtk.Label(_("Background color"),
                                 halign=START)
        btn_bg_color = Gtk.ColorButton(color=Gdk.color_parse(self.options.bg_color),
                                       title=_("Background color"),
                                       halign=END)
        btn_bg_color.connect("color-set", on_bg_color_changed)

        lbl_opacity = Gtk.Label(_("Opacity"),
                                halign=START)
        adj_opacity = Gtk.Adjustment(self.options.opacity, 0, 1.0, 0.1, 0, 0)
        adj_opacity.connect("value-changed", on_adj_opacity_changed)
        adj_scale = Gtk.Scale(adjustment=adj_opacity,
                              hexpand=True, halign=FILL)

        grid_color.add(lbl_font_color)
        grid_color.attach_next_to(btn_font_color, lbl_font_color, RIGHT, 1, 1)
        grid_color.attach_next_to(lbl_bg_color, lbl_font_color, BOTTOM, 1, 1)
        grid_color.attach_next_to(btn_bg_color, lbl_bg_color, RIGHT, 1, 1)
        grid_color.attach_next_to(lbl_opacity, lbl_bg_color, BOTTOM, 1, 1)
        grid_color.attach_next_to(adj_scale, lbl_opacity, RIGHT, 1, 1)
        frm_color.add(grid_color)

        hbox_main = Gtk.Grid(column_homogeneous=True)
        vbox_main = Gtk.Grid(orientation=VERTICAL)
        vbox_main.add(frm_time)
        vbox_main.add(frm_position)
        vbox_main.add(frm_aspect)
        hbox_main.add(vbox_main)
        vbox_main = Gtk.Grid(orientation=VERTICAL)
        vbox_main.add(frm_kbd)
        vbox_main.add(frm_color)
        hbox_main.add(vbox_main)

        box = prefs.get_content_area()
        box.add(hbox_main)
        box.show_all()


    def make_menu(self):
        self.menu = menu = Gtk.Menu()

        show_item = Gtk.CheckMenuItem(_("Show keys"))
        show_item.set_active(True)
        show_item.connect("toggled", self.on_show_keys)
        show_item.show()
        menu.append(show_item)

        preferences_item = Gtk.MenuItem(_("Preferences"))
        preferences_item.connect("activate", self.on_preferences_dialog)
        preferences_item.show()
        menu.append(preferences_item)

        about_item = Gtk.MenuItem(_("About"))
        about_item.connect("activate", self.on_about_dialog)
        about_item.show()
        menu.append(about_item)

        separator_item = Gtk.SeparatorMenuItem()
        separator_item.show()
        menu.append(separator_item)

        image = Gtk.MenuItem(_("Quit"))
        image.connect("activate", self.quit)
        image.show()
        menu.append(image)
        menu.show()


    def make_systray(self):
        try:
            import appindicator
            self.systray = appindicator.Indicator(
                APP_NAME, 'indicator-messages', appindicator.CATEGORY_APPLICATION_STATUS)
            self.systray.set_status(appindicator.STATUS_ACTIVE)
            self.systray.set_attention_icon("indicator-messages-new")
            self.systray.set_icon("preferences-desktop-keyboard-shortcuts")
            self.systray.set_menu(self.menu)
            self.logger.debug("Using AppIndicator.")
        except ImportError:
            self.systray = Gtk.StatusIcon()
            self.systray.set_from_icon_name("preferences-desktop-keyboard-shortcuts")
            self.systray.connect("popup-menu", self.on_statusicon_popup, self.menu)
            self.logger.debug("Using StatusIcon.")


    def make_about_dialog(self):
        self.about = about = Gtk.AboutDialog(use_header_bar=True)
        about.set_program_name(APP_NAME)
        about.set_version(VERSION)
        about.set_copyright("""
        Copyright(c) 2010-2012: Pablo Seminario <pabluk@gmail.com>
        Copyright(c) 2015-2016: wave++ "Yuri D'Elia" <wavexx@thregr.org>
        """)
        about.set_comments(APP_DESC)
        about.set_documenters(
                ["José María Quiroga <pepelandia@gmail.com>"]
        )
        about.set_website(APP_URL)
        about.set_icon_name('preferences-desktop-keyboard-shortcuts')
        about.set_logo_icon_name('preferences-desktop-keyboard-shortcuts')
        about.connect("response", lambda *_: about.hide_on_delete())
        about.connect("delete-event", lambda *_: about.hide_on_delete())


    def on_about_dialog(self, widget, data=None):
        self.about.show()


    def run(self):
        Gtk.main()
        return self.exit_status
