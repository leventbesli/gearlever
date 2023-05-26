import threading
import time
import logging
from typing import Optional, Callable
from .lib.utils import qq
from gi.repository import Gtk, GObject, Adw, Gdk, Gio, Pango, GLib
from .State import state
from .models.AppListElement import InstalledStatus
from .providers.AppImageProvider import AppImageListElement, AppImageUpdateLogic
from .providers.providers_list import appimage_provider
from .lib.async_utils import _async, idle
from .lib.utils import cleanhtml, key_in_dict, set_window_cursor, get_application_window
from .components.CustomComponents import CenteringBox, LabelStart
from .components.AppDetailsConflictModal import AppDetailsConflictModal


class AppDetails(Gtk.ScrolledWindow):
    """The presentation screen for an application"""
    __gsignals__ = {
        "uninstalled-app": (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, (object, )),
    }

    def __init__(self):
        super().__init__()
        self.app_list_element: AppImageListElement = None
        self.common_btn_css_classes = ['pill', 'text-button']

        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=10, margin_bottom=10, margin_start=20, margin_end=20,)

        # 1st row
        self.details_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.icon_slot = Gtk.Box()

        title_col = CenteringBox(orientation=Gtk.Orientation.VERTICAL, hexpand=True, spacing=2)
        self.title = Gtk.Label(label='', css_classes=['title-1'], hexpand=True, halign=Gtk.Align.CENTER)
        self.version = Gtk.Label(label='', halign=Gtk.Align.CENTER, css_classes=['dim-label'])
        self.app_id = Gtk.Label(
            label='',
            halign=Gtk.Align.CENTER,
            css_classes=['dim-label'],
            ellipsize=Pango.EllipsizeMode.END,
            max_width_chars=100,
        )

        for el in [self.title, self.app_id, self.version]:
            title_col.append(el)

        self.source_selector_hdlr = None
        self.source_selector = Gtk.ComboBoxText()
        self.source_selector_revealer = Gtk.Revealer(child=self.source_selector, transition_type=Gtk.RevealerTransitionType.CROSSFADE)

        # Trust app check button
        self.trust_app_check_button = Gtk.CheckButton(label=_('I have verified the source of this app'))
        self.trust_app_check_button.connect('toggled', self.after_trust_buttons_interaction)

        self.trust_app_check_button_revealer = Gtk.Revealer(
            child=self.trust_app_check_button, 
        )

        # Action buttons
        self.primary_action_button = Gtk.Button(label='', valign=Gtk.Align.CENTER, css_classes=self.common_btn_css_classes)
        self.secondary_action_button = Gtk.Button(label='', valign=Gtk.Align.CENTER, visible=False, css_classes=self.common_btn_css_classes)

        action_buttons_row = CenteringBox(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.primary_action_button.connect('clicked', self.on_primary_action_button_clicked)
        self.secondary_action_button.connect('clicked', self.on_secondary_action_button_clicked)

        for el in [self.trust_app_check_button_revealer, self.secondary_action_button, self.primary_action_button]:
            action_buttons_row.append(el)

        for el in [self.icon_slot, title_col, action_buttons_row]:
            self.details_row.append(el)

        # preview row
        self.previews_row = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_top=20,
        )

        # row
        self.desc_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, margin_top=20, margin_bottom=20)
        self.description = Gtk.Label(label='', halign=Gtk.Align.START, wrap=True, selectable=True)

        self.desc_row_spinner = Gtk.Spinner(spinning=True, visible=True)
        self.desc_row.append(self.desc_row_spinner)

        self.desc_row.append(self.description)

        # row
        self.third_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)

        for el in [self.details_row, self.previews_row, self.desc_row, self.third_row]:
            self.main_box.append(el)

        clamp = Adw.Clamp(child=self.main_box, maximum_size=600, margin_top=10, margin_bottom=20)
        
        self.set_trust_button(trusted=True)
        self.set_child(clamp)

    def set_app_list_element(self, el: AppImageListElement):
        self.app_list_element = el
        self.provider = appimage_provider

        self.load()

    def set_from_local_file(self, file: Gio.File):
        if appimage_provider.can_install_file(file):
            list_element = appimage_provider.create_list_element_from_file(file)

            self.set_trust_button(trusted=(list_element.installed_status is InstalledStatus.INSTALLED))

            self.set_app_list_element(list_element)
            return True

        logging.warn('Trying to open an unsupported file')
        return False


    @idle
    def complete_load(self, icon: Gtk.Image, load_completed_callback: Optional[Callable]):
        self.show_row_spinner(True)

        self.details_row.remove(self.icon_slot)
        self.icon_slot = icon
        icon.set_pixel_size(128)
        self.details_row.prepend(self.icon_slot)

        self.title.set_label(cleanhtml(self.app_list_element.name))

        version_label = self.app_list_element.version
        version_label = '' if not version_label else f'<small>{version_label}</small>'

        self.version.set_markup(version_label)
        self.app_id.set_markup(f'<small>{self.app_list_element.app_id}</small>')

        self.app_id.set_visible(len(self.app_list_element.app_id) > 0)
        self.version.set_visible(len(version_label) > 0)

        self.description.set_label(
            self.provider.get_description(self.app_list_element)
        )

        self.third_row.remove(self.extra_data)
        self.extra_data = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.third_row.append(self.extra_data)

        self.install_button_label_info = None


        # Load the boxed list with additional information
        gtk_list = Gtk.ListBox(css_classes=['boxed-list'], margin_bottom=20)

        row = Adw.ActionRow(title=f'{self.provider.name.capitalize()} Gen. {self.app_list_element.generation}', subtitle='Package type')
        row_img = Gtk.Image(resource=self.provider.icon, pixel_size=34)
        row.add_prefix(row_img)
        gtk_list.append(row)

        self.extra_data.append(gtk_list)

        self.update_installation_status()
        self.show_row_spinner(False)

        if load_completed_callback is not None:
            load_completed_callback()

    @_async
    def load(self, load_completed_callback: Optional[Callable]=None):
        self.show_row_spinner(True)
        icon = Gtk.Image(icon_name='application-x-executable-symbolic')

        if self.trust_app_check_button.get_active():
            icon = self.provider.get_icon(self.app_list_element)

            if self.app_list_element.installed_status is not InstalledStatus.INSTALLED:
                self.provider.refresh_title(self.app_list_element)

        self.complete_load(icon, load_completed_callback)

    @_async
    def install_file(self, el: AppImageListElement):
        try:
            self.provider.install_file(el)
        except Exception as e:
            logging.error(str(e))

        self.update_installation_status()

    def on_conflict_modal_close(self, widget, data: str):
        if data == 'cancel':
            self.app_list_element.update_logic = None
            return

        self.app_list_element.update_logic = AppImageUpdateLogic[data]
        self.on_primary_action_button_clicked()

    def on_primary_action_button_clicked(self, button: Optional[Gtk.Button]=None):
        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.app_list_element.set_installed_status(InstalledStatus.UNINSTALLING)
            self.update_installation_status()

            self.provider.uninstall(self.app_list_element)
            self.emit('uninstalled-app', self)

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            if self.provider.is_updatable(self.app_list_element) and not self.app_list_element.update_logic:
                confirm_modal = AppDetailsConflictModal(app_name=self.app_list_element.name)

                confirm_modal.modal.connect('response', self.on_conflict_modal_close)
                confirm_modal.modal.present()
                return

            self.app_list_element.set_installed_status(InstalledStatus.INSTALLING)

            if self.trust_app_check_button.get_active():
                self.update_installation_status()
                self.install_file(self.app_list_element)

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.provider.uninstall(self.app_list_element)

        self.update_installation_status()

    def on_secondary_action_button_clicked(self, button: Gtk.Button):
        if self.app_list_element.installed_status in [InstalledStatus.INSTALLED, InstalledStatus.NOT_INSTALLED]:
            if self.trust_app_check_button.get_active():
                try:
                    pre_launch_label = self.secondary_action_button.get_label()
                    GLib.idle_add(lambda: self.secondary_action_button.set_label(_('Launching...')))
                    self.provider.run(self.app_list_element)
                    self.post_launch_animation(restore_as=pre_launch_label)

                except Exception as e:
                    logging.error(str(e))

    @_async
    def post_launch_animation(self, restore_as):
        GLib.idle_add(lambda: self.secondary_action_button.set_sensitive(False))
        time.sleep(3)

        GLib.idle_add(lambda: self.secondary_action_button.set_label(restore_as))
        GLib.idle_add(lambda: self.secondary_action_button.set_sensitive(True))

    def update_status_callback(self, status: bool):
        if not status:
            self.app_list_element.set_installed_status(InstalledStatus.ERROR)

        self.update_installation_status()

    def update_installation_status(self):
        self.primary_action_button.set_css_classes(self.common_btn_css_classes)
        self.secondary_action_button.set_visible(False)
        self.secondary_action_button.set_css_classes(self.common_btn_css_classes)
        self.source_selector.set_visible(False)

        if self.app_list_element.installed_status == InstalledStatus.INSTALLED:
            self.secondary_action_button.set_label(_('Launch'))
            self.secondary_action_button.set_visible(True)

            self.primary_action_button.set_label(_('Remove'))
            self.primary_action_button.set_css_classes([*self.common_btn_css_classes, 'destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UNINSTALLING:
            self.primary_action_button.set_label(_('Uninstalling...'))

        elif self.app_list_element.installed_status == InstalledStatus.INSTALLING:
            self.primary_action_button.set_label(_('Installing...'))

        elif self.app_list_element.installed_status == InstalledStatus.NOT_INSTALLED:
            # self.secondary_action_button.set_sensitive(False)
            # self.primary_action_button.set_sensitive(False)

            self.secondary_action_button.set_visible(True)
            self.primary_action_button.set_css_classes([*self.common_btn_css_classes, 'suggested-action'])

            self.primary_action_button.set_label(_('Move to the app menu'))
            self.secondary_action_button.set_label(_('Launch'))

        elif self.app_list_element.installed_status == InstalledStatus.UPDATE_AVAILABLE:
            self.secondary_action_button.set_label(_('Update'))
            self.secondary_action_button.set_css_classes([*self.common_btn_css_classes, 'suggested-action'])
            self.secondary_action_button.set_visible(True)

            self.primary_action_button.set_label(_('Remove'))
            self.primary_action_button.set_css_classes([*self.common_btn_css_classes, 'destructive-action'])

        elif self.app_list_element.installed_status == InstalledStatus.UPDATING:
            self.primary_action_button.set_label(_('Updating'))

        elif self.app_list_element.installed_status == InstalledStatus.ERROR:
            self.primary_action_button.set_label(_('Error'))
            self.primary_action_button.set_css_classes([*self.common_btn_css_classes, 'destructive-action'])

    def provider_refresh_installed_status(self, status: Optional[InstalledStatus] = None, final=False):
        if status:
            self.app_list_element.installed_status = status

        self.update_installation_status()

    def show_row_spinner(self, status: bool):
        self.desc_row_spinner.set_visible(status)
        self.desc_row_spinner.set_spinning(status)

    def set_trust_button(self, trusted=False):
        if trusted:
            self.trust_app_check_button_revealer.set_reveal_child(False)
            self.trust_app_check_button.set_active(True)
            self.secondary_action_button.set_sensitive(True),
            self.primary_action_button.set_sensitive(True)
        else:
            self.trust_app_check_button_revealer.set_reveal_child(True)
            self.trust_app_check_button.set_active(False)
            self.secondary_action_button.set_sensitive(False)
            self.primary_action_button.set_sensitive(False)

    def after_trust_buttons_interaction(self, widget):
        if self.app_list_element and self.trust_app_check_button.get_active():
            self.app_list_element.trusted = True

            self.trust_app_check_button_revealer.set_reveal_child(False)
            self.title.set_label('...')
            self.load(load_completed_callback=lambda: [
                self.secondary_action_button.set_sensitive(True),
                self.primary_action_button.set_sensitive(True)
            ])