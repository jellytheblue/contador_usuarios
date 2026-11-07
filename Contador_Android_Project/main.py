# -*- coding: utf-8 -*-
__version__ = "1.0.0"

from pathlib import Path
import json
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.modalview import ModalView
from kivy.utils import platform

from counter_core import load_data, save_data, count_users, reset_if_due, new_id, normalize_data

# Paleta clara, azul lavanda y verde para estados activos.
BG = (0.945, 0.961, 0.984, 1)
PANEL = (1, 1, 1, 1)
TEXT = (0.105, 0.16, 0.26, 1)
MUTED = (0.43, 0.49, 0.59, 1)
BLUE = (0.25, 0.40, 0.68, 1)
BLUE_DARK = (0.18, 0.30, 0.52, 1)
BLUE_PALE = (0.91, 0.94, 0.99, 1)
GREEN = (0.19, 0.59, 0.45, 1)
GREEN_PALE = (0.90, 0.96, 0.93, 1)
RED = (0.79, 0.30, 0.36, 1)
BORDER = (0.84, 0.88, 0.93, 1)
WHITE = (1, 1, 1, 1)


def rounded_background(widget, color, radius=dp(18), border=None):
    with widget.canvas.before:
        widget._bg_color = Color(*color)
        widget._bg_rect = RoundedRectangle(pos=widget.pos, size=widget.size,
                                           radius=[radius])
        if border:
            widget._border_color = Color(*border)
            widget._border_line = Line(rounded_rectangle=(widget.x, widget.y,
                                                           widget.width, widget.height,
                                                           radius), width=1)
    def update(*_):
        widget._bg_rect.pos = widget.pos
        widget._bg_rect.size = widget.size
        if border:
            widget._border_line.rounded_rectangle = (widget.x, widget.y,
                                                       widget.width, widget.height,
                                                       radius)
    widget.bind(pos=update, size=update)


class Card(BoxLayout):
    def __init__(self, *args, color=PANEL, padding=dp(14), spacing=dp(9), **kwargs):
        super().__init__(*args, padding=padding, spacing=spacing, **kwargs)
        rounded_background(self, color, dp(20), BORDER)


class ActionButton(Button):
    def __init__(self, *args, bg=BLUE, fg=WHITE, radius=dp(14), **kwargs):
        super().__init__(*args, **kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = fg
        self.bold = True
        self.font_size = sp(13)
        self._normal_bg = bg
        self._down_bg = tuple(max(0, c * 0.88) for c in bg[:3]) + (bg[3],)
        with self.canvas.before:
            self._button_color = Color(*self._normal_bg)
            self._button_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                                  radius=[radius])
        self.bind(pos=self._update_rect, size=self._update_rect,
                  state=self._update_state)
    def _update_rect(self, *_):
        self._button_rect.pos = self.pos
        self._button_rect.size = self.size
    def _update_state(self, *_):
        self._button_color.rgba = self._down_bg if self.state == "down" else self._normal_bg


class SoftInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = False
        self.font_size = sp(15)
        self.foreground_color = TEXT
        self.cursor_color = BLUE
        self.hint_text_color = MUTED
        self.padding = [dp(13), dp(13), dp(13), dp(10)]
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            Color(*BLUE_PALE)
            self._input_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                                 radius=[dp(13)])
        self.bind(pos=self._sync, size=self._sync)
    def _sync(self, *_):
        self._input_rect.pos = self.pos
        self._input_rect.size = self.size


class CounterApp(App):
    title = "Contador de usuarios"

    def build(self):
        Window.clearcolor = BG
        self.data_path = Path(self.user_data_dir) / "contador_usuarios_datos.json"
        self.data, load_warning = load_data(self.data_path)
        self.status_text = "Datos listos" if not load_warning else "Se inició una copia nueva: archivo anterior no válido"
        self.root_layout = BoxLayout(orientation="vertical", padding=[dp(14), dp(12), dp(14), dp(12)])

        self.scroller = ScrollView(do_scroll_x=False, bar_width=dp(3),
                                   scroll_type=["bars", "content"])
        self.content = BoxLayout(orientation="vertical", size_hint_y=None,
                                 spacing=dp(12), padding=[0, 0, 0, dp(8)])
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroller.add_widget(self.content)
        self.root_layout.add_widget(self.scroller)
        self.build_header()
        self.build_summary()
        self.build_groups()
        self.build_timer()
        self.build_add_button()
        self.build_user_section()
        self.build_footer()
        self.refresh_all()
        Clock.schedule_interval(self.tick, 1)
        return self.root_layout

    def label(self, text, size=14, color=TEXT, bold=False, **kwargs):
        widget = Label(text=text, font_size=sp(size), color=color, bold=bold,
                       halign=kwargs.pop("halign", "left"),
                       valign=kwargs.pop("valign", "middle"),
                       **kwargs)
        widget.bind(width=lambda obj, width: setattr(obj, "text_size", (max(1, width), None)))
        return widget

    def build_header(self):
        header = BoxLayout(orientation="horizontal", size_hint_y=None,
                           height=dp(68), spacing=dp(8))
        text_box = BoxLayout(orientation="vertical", spacing=dp(1))
        text_box.add_widget(self.label("Contador", 25, TEXT, True))
        text_box.add_widget(self.label("USUARIOS Y PERSONAJES", 9, MUTED, True))
        header.add_widget(text_box)
        backup = ActionButton(text="Copia JSON", bg=BLUE_PALE, fg=BLUE_DARK,
                              size_hint=(None, None), size=(dp(94), dp(40)))
        backup.bind(on_release=lambda *_: self.open_backup_menu())
        header.add_widget(backup)
        self.content.add_widget(header)

    def build_summary(self):
        card = Card(orientation="vertical", size_hint_y=None, height=dp(126),
                    padding=[dp(17), dp(13), dp(17), dp(13)], spacing=dp(5),
                    color=BLUE_DARK)
        card.add_widget(self.label("ACTIVIDAD GENERAL", 9, (0.78, 0.85, 0.96, 1), True))
        row = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))
        self.active_number = self.label("0", 32, WHITE, True)
        row.add_widget(self.active_number)
        self.summary_detail = self.label("activos de 0 usuarios", 12,
                                         (0.83, 0.88, 0.96, 1))
        row.add_widget(self.summary_detail)
        row.add_widget(Widget())
        card.add_widget(row)
        self.progress_track = Widget(size_hint_y=None, height=dp(7))
        with self.progress_track.canvas:
            Color(0.29, 0.40, 0.59, 1)
            self.progress_bg = RoundedRectangle(pos=self.progress_track.pos,
                                                 size=self.progress_track.size,
                                                 radius=[dp(4)])
            Color(0.35, 0.83, 0.65, 1)
            self.progress_fill = RoundedRectangle(pos=self.progress_track.pos,
                                                   size=(0, self.progress_track.height),
                                                   radius=[dp(4)])
        self.progress_track.bind(pos=self.update_progress, size=self.update_progress)
        card.add_widget(self.progress_track)
        self.content.add_widget(card)

    def update_progress(self, *_):
        self.progress_bg.pos = self.progress_track.pos
        self.progress_bg.size = self.progress_track.size
        active, total = count_users(self.data)
        ratio = active / total if total else 0
        self.progress_fill.pos = self.progress_track.pos
        self.progress_fill.size = (self.progress_track.width * ratio,
                                   self.progress_track.height)

    def section_title(self, title, right_widget=None):
        row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(7))
        row.add_widget(self.label(title, 11, MUTED, True))
        row.add_widget(Widget())
        if right_widget:
            row.add_widget(right_widget)
        return row

    def build_groups(self):
        self.groups_card = Card(orientation="vertical", size_hint_y=None,
                                height=dp(155), spacing=dp(8))
        controls = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        controls.add_widget(self.label("TUS GRUPOS", 10, MUTED, True))
        controls.add_widget(Widget())
        rename = ActionButton(text="Editar", bg=BLUE_PALE, fg=BLUE_DARK,
                              size_hint=(None, None), size=(dp(66), dp(32)))
        rename.bind(on_release=lambda *_: self.prompt_group_rename())
        controls.add_widget(rename)
        remove = ActionButton(text="Eliminar", bg=(0.99, 0.92, 0.93, 1), fg=RED,
                              size_hint=(None, None), size=(dp(78), dp(32)))
        remove.bind(on_release=lambda *_: self.confirm_delete_group())
        controls.add_widget(remove)
        self.groups_card.add_widget(controls)
        self.group_scroll = ScrollView(size_hint_y=None, height=dp(43),
                                       do_scroll_y=False, bar_width=0)
        self.group_row = BoxLayout(size_hint=(None, 1), spacing=dp(7), padding=[0, dp(2)])
        self.group_row.bind(minimum_width=self.group_row.setter("width"))
        self.group_scroll.add_widget(self.group_row)
        self.groups_card.add_widget(self.group_scroll)
        add = ActionButton(text="＋  Nuevo grupo", bg=BLUE_PALE, fg=BLUE_DARK,
                           size_hint_y=None, height=dp(34))
        add.bind(on_release=lambda *_: self.prompt_text(
            "Nuevo grupo", "Nombre del grupo", "", self.add_group))
        self.groups_card.add_widget(add)
        self.content.add_widget(self.groups_card)

    def build_timer(self):
        card = Card(orientation="vertical", size_hint_y=None, height=dp(198), spacing=dp(8))
        top = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        top.add_widget(self.label("↻  REINICIO AUTOMÁTICO", 10, TEXT, True))
        top.add_widget(Widget())
        self.count_pill = ActionButton(text="0 / 0 activos", bg=GREEN_PALE, fg=GREEN,
                                       size_hint=(None, None), size=(dp(112), dp(29)))
        top.add_widget(self.count_pill)
        card.add_widget(top)
        card.add_widget(self.label("Reiniciar todos los interruptores cada", 12, MUTED,
                                   size_hint_y=None, height=dp(22)))
        controls = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(8))
        self.interval_input = SoftInput(text=f"{self.data['reset_interval_hours']:g}",
                                        hint_text="Horas", input_filter="float",
                                        size_hint=(1, None), height=dp(42))
        controls.add_widget(self.interval_input)
        controls.add_widget(self.label("horas", 12, MUTED, size_hint=(None, 1), width=dp(42)))
        apply = ActionButton(text="Aplicar", size_hint=(None, None),
                             size=(dp(92), dp(42)))
        apply.bind(on_release=lambda *_: self.apply_interval())
        controls.add_widget(apply)
        card.add_widget(controls)
        self.timer_label = self.label("Próximo reinicio: --:--:--", 12, BLUE_DARK, True,
                                      size_hint_y=None, height=dp(22))
        card.add_widget(self.timer_label)
        card.add_widget(self.label("Al cumplirse el plazo, todos vuelven a OFF.",
                                   10, MUTED, size_hint_y=None, height=dp(17)))
        self.content.add_widget(card)

    def build_add_button(self):
        add = ActionButton(text="＋   Agregar usuario / personaje", size_hint_y=None,
                           height=dp(49), radius=dp(16))
        add.bind(on_release=lambda *_: self.prompt_text(
            "Agregar usuario", "Nombre del usuario o personaje", "", self.add_user))
        self.add_user_button = add
        self.content.add_widget(add)

    def build_user_section(self):
        self.user_heading = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(7))
        self.user_heading.add_widget(self.label("PERSONAJES DEL GRUPO", 10, MUTED, True))
        self.user_heading.add_widget(Widget())
        self.user_count_label = self.label("0 ACTIVOS · 0 TOTAL", 9, BLUE_DARK, True,
                                           size_hint=(None, 1), width=dp(132), halign="right")
        self.user_heading.add_widget(self.user_count_label)
        self.content.add_widget(self.user_heading)
        self.user_list = BoxLayout(orientation="vertical", size_hint_y=None,
                                   spacing=dp(8))
        self.user_list.bind(minimum_height=self.user_list.setter("height"))
        self.content.add_widget(self.user_list)

    def build_footer(self):
        footer = BoxLayout(size_hint_y=None, height=dp(25), spacing=dp(5))
        footer.add_widget(self.label("Los cambios se guardan automáticamente", 9, MUTED))
        footer.add_widget(Widget())
        self.status_label = self.label(self.status_text, 9, GREEN, True,
                                       size_hint=(None, 1), width=dp(82), halign="right")
        footer.add_widget(self.status_label)
        self.content.add_widget(footer)

    def selected_group(self):
        selected_id = self.data.get("selected_group_id")
        for group in self.data["groups"]:
            if group["id"] == selected_id:
                return group
        self.data["selected_group_id"] = self.data["groups"][0]["id"]
        return self.data["groups"][0]

    def refresh_all(self):
        active, total = count_users(self.data)
        self.active_number.text = str(active)
        self.summary_detail.text = f"activos de {total} usuarios"
        self.count_pill.text = f"{active} / {total} activos"
        self.update_progress()
        self.render_groups()
        self.render_users()
        self.tick(0)

    def render_groups(self):
        self.group_row.clear_widgets()
        for group in self.data["groups"]:
            selected = group["id"] == self.data.get("selected_group_id")
            button = ActionButton(
                text=group["name"], bg=BLUE_DARK if selected else BLUE_PALE,
                fg=WHITE if selected else BLUE_DARK,
                size_hint=(None, None), height=dp(36),
                width=max(dp(90), min(dp(180), dp(25 + len(group["name"]) * 8.2))),
            )
            button.bind(on_release=lambda _btn, gid=group["id"]: self.select_group(gid))
            self.group_row.add_widget(button)

    def render_users(self):
        self.user_list.clear_widgets()
        group = self.selected_group()
        local_active = sum(bool(u.get("active")) for u in group["users"])
        local_total = len(group["users"])
        self.user_count_label.text = f"{local_active} ACTIVOS · {local_total} TOTAL"
        if not group["users"]:
            empty = Card(orientation="vertical", size_hint_y=None, height=dp(112),
                         padding=dp(16), spacing=dp(5))
            empty.add_widget(self.label("Todavía no hay personajes", 14, TEXT, True,
                                        halign="center"))
            empty.add_widget(self.label("Agrega el primero con el botón de arriba.",
                                        11, MUTED, halign="center"))
            self.user_list.add_widget(empty)
        else:
            for user in group["users"]:
                self.user_list.add_widget(self.make_user_card(group, user))

    def make_user_card(self, group, user):
        active = bool(user.get("active", False))
        card = Card(orientation="horizontal", size_hint_y=None, height=dp(76),
                    padding=[dp(11), dp(9)], spacing=dp(6),
                    color=GREEN_PALE if active else PANEL)
        identity = BoxLayout(orientation="vertical", spacing=dp(1))
        name = str(user.get("name", "Usuario"))
        name_label = self.label(name, 13, TEXT, True, shorten=True, max_lines=1)
        identity.add_widget(name_label)
        identity.add_widget(self.label("●  ACTIVO" if active else "○  INACTIVO",
                                       9, GREEN if active else MUTED, True))
        card.add_widget(identity)
        rename = ActionButton(text="✎", bg=BLUE_PALE, fg=BLUE_DARK,
                              size_hint=(None, None), size=(dp(37), dp(39)))
        rename.bind(on_release=lambda *_: self.prompt_text(
            "Renombrar usuario", "Nuevo nombre", user["name"],
            lambda value: self.rename_user(user, value)))
        card.add_widget(rename)
        toggle = ActionButton(text="ON" if active else "OFF",
                              bg=GREEN if active else (0.89, 0.91, 0.94, 1),
                              fg=WHITE if active else MUTED,
                              size_hint=(None, None), size=(dp(55), dp(39)))
        toggle.bind(on_release=lambda *_: self.toggle_user(user))
        card.add_widget(toggle)
        delete = ActionButton(text="×", bg=(0.99, 0.92, 0.93, 1), fg=RED,
                              size_hint=(None, None), size=(dp(37), dp(39)))
        delete.bind(on_release=lambda *_: self.confirm_delete_user(group, user))
        card.add_widget(delete)
        return card

    def select_group(self, group_id):
        self.data["selected_group_id"] = group_id
        self.render_groups()
        self.render_users()
        self.save()

    def add_group(self, name):
        name = name.strip()
        if not name:
            self.show_message("Nombre vacío", "Escribe un nombre para el grupo.")
            return
        group = {"id": new_id(), "name": name, "users": []}
        self.data["groups"].append(group)
        self.data["selected_group_id"] = group["id"]
        self.refresh_all()
        self.save("Grupo creado")

    def prompt_group_rename(self):
        group = self.selected_group()
        self.prompt_text("Renombrar grupo", "Nombre del grupo", group["name"],
                         lambda value: self.rename_group(group, value))

    def rename_group(self, group, value):
        value = value.strip()
        if not value:
            self.show_message("Nombre vacío", "El nombre del grupo no puede quedar vacío.")
            return
        group["name"] = value
        self.render_groups()
        self.save("Grupo renombrado")

    def confirm_delete_group(self):
        group = self.selected_group()
        if len(self.data["groups"]) <= 1:
            self.show_message("No se puede eliminar", "Debe existir al menos un grupo.")
            return
        self.confirm("Eliminar grupo", f"¿Eliminar «{group['name']}» y todos sus usuarios?",
                     lambda: self.delete_group(group))

    def delete_group(self, group):
        self.data["groups"] = [g for g in self.data["groups"] if g["id"] != group["id"]]
        if self.data.get("selected_group_id") == group["id"]:
            self.data["selected_group_id"] = self.data["groups"][0]["id"]
        self.refresh_all()
        self.save("Grupo eliminado")

    def add_user(self, name):
        name = name.strip()
        if not name:
            self.show_message("Nombre vacío", "Escribe un nombre para el usuario.")
            return
        self.selected_group()["users"].append({"id": new_id(), "name": name, "active": False})
        self.refresh_all()
        self.save("Usuario agregado")

    def rename_user(self, user, value):
        value = value.strip()
        if not value:
            self.show_message("Nombre vacío", "El nombre no puede quedar vacío.")
            return
        user["name"] = value
        self.refresh_all()
        self.save("Nombre actualizado")

    def toggle_user(self, user):
        user["active"] = not bool(user.get("active", False))
        self.refresh_all()
        self.save("Estado actualizado")

    def confirm_delete_user(self, group, user):
        self.confirm("Eliminar usuario", f"¿Quieres eliminar a «{user['name']}»?",
                     lambda: self.delete_user(group, user))

    def delete_user(self, group, user):
        group["users"] = [u for u in group["users"] if u["id"] != user["id"]]
        self.refresh_all()
        self.save("Usuario eliminado")

    def apply_interval(self):
        raw = self.interval_input.text.strip().replace(",", ".")
        try:
            hours = float(raw)
            if not 0.5 <= hours <= 720:
                raise ValueError
        except ValueError:
            self.show_message("Intervalo no válido", "Introduce un intervalo entre 0,5 y 720 horas.")
            self.interval_input.text = f"{self.data['reset_interval_hours']:g}"
            return
        self.data["reset_interval_hours"] = hours
        self.data["next_reset_at"] = time.time() + hours * 3600
        self.interval_input.text = f"{hours:g}"
        self.save("Intervalo actualizado")
        self.tick(0)

    def tick(self, _dt):
        if reset_if_due(self.data):
            self.refresh_all()
            self.save("Reinicio automático completado")
        remaining = max(0, int(float(self.data["next_reset_at"]) - time.time()))
        hours, remainder = divmod(remaining, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.timer_label.text = f"Próximo reinicio: {hours:02d}:{minutes:02d}:{seconds:02d}"

    def save(self, message=None, show_feedback=False):
        try:
            save_data(self.data_path, self.data)
            if message:
                self.status_text = message
            elif show_feedback:
                self.status_text = "Guardado correctamente"
            else:
                self.status_text = "Guardado"
        except Exception as exc:
            self.status_text = "Error al guardar"
            self.show_message("Error al guardar", str(exc))
        if hasattr(self, "status_label"):
            self.status_label.text = self.status_text

    def prompt_text(self, title, hint, initial, callback):
        view = ModalView(size_hint=(0.9, None), height=dp(236),
                         background_color=(0.04, 0.07, 0.12, 0.55),
                         auto_dismiss=False)
        panel = Card(orientation="vertical", padding=dp(18), spacing=dp(12))
        panel.add_widget(self.label(title, 17, TEXT, True,
                                    size_hint_y=None, height=dp(29)))
        field = SoftInput(text=initial, hint_text=hint,
                          size_hint_y=None, height=dp(46))
        panel.add_widget(field)
        buttons = BoxLayout(size_hint_y=None, height=dp(43), spacing=dp(8))
        cancel = ActionButton(text="Cancelar", bg=BLUE_PALE, fg=BLUE_DARK)
        cancel.bind(on_release=lambda *_: view.dismiss())
        accept = ActionButton(text="Guardar")
        def do_accept(*_):
            value = field.text.strip()
            view.dismiss()
            callback(value)
        accept.bind(on_release=do_accept)
        buttons.add_widget(cancel)
        buttons.add_widget(accept)
        panel.add_widget(buttons)
        view.add_widget(panel)
        view.open()
        Clock.schedule_once(lambda _dt: setattr(field, "focus", True), 0.25)

    def confirm(self, title, message, callback):
        view = ModalView(size_hint=(0.9, None), height=dp(220),
                         background_color=(0.04, 0.07, 0.12, 0.55),
                         auto_dismiss=False)
        panel = Card(orientation="vertical", padding=dp(18), spacing=dp(12))
        panel.add_widget(self.label(title, 17, TEXT, True,
                                    size_hint_y=None, height=dp(30)))
        panel.add_widget(self.label(message, 13, MUTED))
        buttons = BoxLayout(size_hint_y=None, height=dp(43), spacing=dp(8))
        cancel = ActionButton(text="Cancelar", bg=BLUE_PALE, fg=BLUE_DARK)
        cancel.bind(on_release=lambda *_: view.dismiss())
        yes = ActionButton(text="Eliminar", bg=RED)
        def do_delete(*_):
            view.dismiss()
            callback()
        yes.bind(on_release=do_delete)
        buttons.add_widget(cancel)
        buttons.add_widget(yes)
        panel.add_widget(buttons)
        view.add_widget(panel)
        view.open()

    def show_message(self, title, message):
        view = ModalView(size_hint=(0.9, None), height=dp(190),
                         background_color=(0.04, 0.07, 0.12, 0.55))
        panel = Card(orientation="vertical", padding=dp(18), spacing=dp(12))
        panel.add_widget(self.label(title, 17, TEXT, True,
                                    size_hint_y=None, height=dp(30)))
        panel.add_widget(self.label(message, 12, MUTED))
        close = ActionButton(text="Entendido", size_hint_y=None, height=dp(42))
        close.bind(on_release=lambda *_: view.dismiss())
        panel.add_widget(close)
        view.add_widget(panel)
        view.open()


    def open_backup_menu(self):
        view = ModalView(size_hint=(0.9, None), height=dp(250),
                         background_color=(0.04, 0.07, 0.12, 0.55))
        panel = Card(orientation="vertical", padding=dp(18), spacing=dp(10))
        panel.add_widget(self.label("Copias de seguridad", 17, TEXT, True,
                                    size_hint_y=None, height=dp(30)))
        panel.add_widget(self.label("Importa el JSON de Windows o exporta una copia para guardarla.",
                                    11, MUTED, size_hint_y=None, height=dp(40)))
        import_button = ActionButton(text="Importar copia JSON", bg=BLUE_PALE, fg=BLUE_DARK,
                                     size_hint_y=None, height=dp(43))
        import_button.bind(on_release=lambda *_: (view.dismiss(), self.confirm(
            "Importar datos", "La copia reemplazará los grupos y usuarios actuales.",
            self.choose_import_file)))
        export_button = ActionButton(text="Exportar copia JSON",
                                     size_hint_y=None, height=dp(43))
        export_button.bind(on_release=lambda *_: (view.dismiss(), self.choose_export_file()))
        close = ActionButton(text="Cerrar", bg=(0.93, 0.95, 0.97, 1), fg=MUTED,
                             size_hint_y=None, height=dp(38))
        close.bind(on_release=lambda *_: view.dismiss())
        panel.add_widget(import_button)
        panel.add_widget(export_button)
        panel.add_widget(close)
        view.add_widget(panel)
        view.open()

    def on_start(self):
        if platform == "android":
            try:
                from android import activity
                activity.bind(on_activity_result=self._on_android_activity_result)
                self._android_activity = activity
            except Exception as exc:
                self.status_text = f"Funciones de archivos no disponibles: {exc}"
                self.status_label.text = self.status_text

    def choose_import_file(self):
        if platform != "android":
            self.show_message("Importar copia", "La selección de archivos está disponible en el APK Android.")
            return
        try:
            from jnius import autoclass
            from android import mActivity
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/json")
            mActivity.startActivityForResult(intent, 0xC711)
        except Exception as exc:
            self.show_message("No se pudo abrir el archivo", str(exc))

    def choose_export_file(self):
        if platform != "android":
            self.show_message("Exportar copia", "La exportación mediante selector está disponible en el APK Android.")
            return
        try:
            from jnius import autoclass
            from android import mActivity
            Intent = autoclass("android.content.Intent")
            intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("application/json")
            intent.putExtra(Intent.EXTRA_TITLE, "contador_usuarios_datos.json")
            mActivity.startActivityForResult(intent, 0xC712)
        except Exception as exc:
            self.show_message("No se pudo crear la copia", str(exc))

    def _on_android_activity_result(self, request_code, result_code, intent):
        if request_code not in (0xC711, 0xC712) or intent is None:
            return
        try:
            from jnius import autoclass
            from android import mActivity
            Activity = autoclass("android.app.Activity")
            if int(result_code) != int(Activity.RESULT_OK):
                return
            uri = intent.getData()
            resolver = mActivity.getContentResolver()
            if request_code == 0xC711:
                stream = resolver.openInputStream(uri)
                raw = bytearray()
                try:
                    while True:
                        value = stream.read()
                        if value == -1:
                            break
                        raw.append(value)
                finally:
                    stream.close()
                imported = normalize_data(json.loads(raw.decode("utf-8-sig")))
                self.data = imported
                self.interval_input.text = f"{self.data['reset_interval_hours']:g}"
                self.refresh_all()
                self.save("Copia importada")
                self.show_message("Importación completada", "Los grupos y usuarios se cargaron correctamente.")
            else:
                descriptor = resolver.openFileDescriptor(uri, "w")
                FileOutputStream = autoclass("java.io.FileOutputStream")
                JavaString = autoclass("java.lang.String")
                stream = FileOutputStream(descriptor.getFileDescriptor())
                try:
                    payload = json.dumps(self.data, ensure_ascii=False, indent=2)
                    stream.write(JavaString(payload).getBytes("UTF-8"))
                    stream.flush()
                finally:
                    stream.close()
                    descriptor.close()
                self.show_message("Copia exportada", "El archivo JSON se guardó en la ubicación seleccionada.")
        except Exception as exc:
            self.show_message("No se pudo procesar el archivo", str(exc))

    def on_pause(self):
        self.save()
        return True

    def on_resume(self):
        self.tick(0)

    def on_stop(self):
        self.save()
        if getattr(self, "_android_activity", None):
            try:
                self._android_activity.unbind(on_activity_result=self._on_android_activity_result)
            except Exception:
                pass


if __name__ == "__main__":
    CounterApp().run()
