# -*- coding: utf-8 -*-
"""Reusable 24-hour time picker with hour and minute wheel-like spinners."""
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty
from kivy.lang import Builder


class TimePicker(BoxLayout):
    hour = NumericProperty(7)
    minute = NumericProperty(30)

    def __init__(self, **kwargs):
        super().__init__(orientation="horizontal", spacing=10, **kwargs)
        self.size_hint_y = None
        self.height = "70dp"
        from kivy.uix.spinner import Spinner
        self.hour_spinner = Spinner(text="07", values=tuple(f"{i:02d}" for i in range(24)),
                                    size_hint=(0.42, 1), font_size="20sp")
        self.minute_spinner = Spinner(text="30", values=tuple(f"{i:02d}" for i in range(60)),
                                      size_hint=(0.42, 1), font_size="20sp")
        from kivy.uix.label import Label
        self.add_widget(self.hour_spinner)
        self.add_widget(Label(text=":", size_hint=(0.16, 1), font_size="22sp"))
        self.add_widget(self.minute_spinner)
        self.hour_spinner.bind(text=self._hour_changed)
        self.minute_spinner.bind(text=self._minute_changed)

    def _hour_changed(self, _spinner, value):
        try:
            self.hour = int(value)
            self.dispatch_time_change()
        except (TypeError, ValueError):
            pass

    def _minute_changed(self, _spinner, value):
        try:
            self.minute = int(value)
            self.dispatch_time_change()
        except (TypeError, ValueError):
            pass

    def dispatch_time_change(self):
        callback = getattr(self, "on_time_change", None)
        if callable(callback):
            callback(self)

    def get_hour(self):
        return int(self.hour)

    def get_minute(self):
        return int(self.minute)

    def get_time_string(self):
        return f"{int(self.hour):02d}{int(self.minute):02d}"

    def set_time(self, h, m):
        h, m = int(h), int(m)
        if not 0 <= h <= 23 or not 0 <= m <= 59:
            raise ValueError("زمان باید بین 00:00 و 23:59 باشد")
        self.hour, self.minute = h, m
        self.hour_spinner.text = f"{h:02d}"
        self.minute_spinner.text = f"{m:02d}"
        self.dispatch_time_change()
