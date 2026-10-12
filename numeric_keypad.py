# -*- coding: utf-8 -*-
"""Four-digit numeric keypad for RTC time entry."""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import StringProperty


class NumericKeypad(BoxLayout):
    value = StringProperty("")
    on_change = None
    on_confirm = None

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", spacing="8dp", **kwargs)
        self.display = Label(text="--:--", font_size="30sp", size_hint_y=None, height="58dp")
        self.add_widget(self.display)
        grid = GridLayout(cols=3, spacing="6dp", size_hint_y=None, height="220dp")
        for key in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "⌫", "0", "تأیید"):
            button = Button(text=key, font_size="18sp")
            button.bind(on_release=lambda instance, k=key: self.press(k))
            grid.add_widget(button)
        self.add_widget(grid)

    def press(self, key):
        if key == "⌫":
            self.value = self.value[:-1]
        elif key == "تأیید":
            if callable(self.on_confirm):
                self.on_confirm(self.get_value())
            self._update_display()
            return
        elif key.isdigit() and len(self.value) < 4:
            self.value += key
        self._update_display()
        if callable(self.on_change):
            self.on_change(self.get_value())

    def _update_display(self):
        digits = self.value.ljust(4, "–")
        self.display.text = digits[:2] + ":" + digits[2:]

    def get_value(self):
        return self.value

    def clear(self):
        self.value = ""
        self._update_display()
        if callable(self.on_change):
            self.on_change(self.get_value())
