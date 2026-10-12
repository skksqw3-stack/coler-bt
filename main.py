# -*- coding: utf-8 -*-

"""
Cooler Control
Android App for Cooler Control with Arduino + HC-05

Python 3.10
Kivy 2.2.0
KivyMD 1.2.0

Files needed:
- main.py
- cooler.kv
- bluetooth_manager.py
- time_picker.py
- numeric_keypad.py
- assets/Vazirmatn-Regular.ttf
"""

import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.factory import Factory
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.screenmanager import ScreenManager, Screen

from bluetooth_manager import BluetoothManager
from time_picker import TimePicker
from numeric_keypad import NumericKeypad


# =========================================================
# Settings
# =========================================================

APP_TITLE = "Cooler Control"
KV_FILE = "cooler.kv"
FONT_FILE = os.path.join("assets", "Vazirmatn-Regular.ttf")

SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"


# =========================================================
# Font Registration
# =========================================================

FONT_AVAILABLE = False

try:
    if os.path.exists(FONT_FILE):
        LabelBase.register(
            name="Vazir",
            fn_regular=FONT_FILE
        )
        FONT_AVAILABLE = True
        print("[OK] Persian font loaded:", FONT_FILE)
    else:
        print(
            "[WARN] Persian font not found:",
            FONT_FILE,
            "- Place Vazirmatn-Regular.ttf in assets folder."
        )
except Exception as exc:
    print("[ERROR] Font loading failed:", exc)


# =========================================================
# Home Screen
# =========================================================

class HomeScreen(Screen):
    temperature = StringProperty("--.-")
    humidity = StringProperty("--.-")
    rtc_time = StringProperty("--:--")
    connection_text = StringProperty("Disconnected")
    connected = BooleanProperty(False)


# =========================================================
# Timer Screen
# =========================================================

class TimerScreen(Screen):
    preview = StringProperty("ON: 07:30 | OFF: 19:30")
    feedback = StringProperty("Select ON and OFF times")


# =========================================================
# Status Screen
# =========================================================

class StatusScreen(Screen):
    temperature = StringProperty("--.- C")
    humidity = StringProperty("--.- %")
    rtc_time = StringProperty("--:--")
    mode = StringProperty("Unknown")
    pump = StringProperty("Unknown")
    motor = StringProperty("Unknown")
    timer = StringProperty("Unknown")


# =========================================================
# Settings Screen
# =========================================================

class SettingsScreen(Screen):
    selected_device = StringProperty("")
    connection_text = StringProperty("Disconnected")
    clock_display = StringProperty("--:--")
    clock_feedback = StringProperty("Enter 4 digits for clock")


# =========================================================
# Main App
# =========================================================

class CoolerApp(App):
    title = APP_TITLE

    def build(self):
        # ============ Variables ============
        self._clock_digits = ""
        self._log_lines = []
        self._closing = False
        self._last_status = {}

        # ============ Background ============
        Window.clearcolor = (0.055, 0.075, 0.12, 1)

        # ============ Register for KV ============
        try:
            Factory.register("TimePicker", cls=TimePicker)
            Factory.register("NumericKeypad", cls=NumericKeypad)
        except Exception as exc:
            print("[WARN] Factory register error:", exc)

        # ============ Load KV ============
        kv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            KV_FILE
        )

        if not os.path.isfile(kv_path):
            raise FileNotFoundError(
                f"KV file not found: {kv_path}"
            )

        try:
            Builder.load_file(kv_path)
            print("[OK] KV loaded:", kv_path)
        except Exception as exc:
            print("[ERROR] KV loading failed:", exc)
            raise

        # ============ Screens ============
        self.sm = ScreenManager()

        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(TimerScreen(name="timer"))
        self.sm.add_widget(StatusScreen(name="status"))
        self.sm.add_widget(SettingsScreen(name="settings"))

        # ============ Bluetooth ============
        try:
            self.bluetooth = BluetoothManager(
                on_line=self.on_bluetooth_line,
                on_state=self.on_bluetooth_state
            )
        except Exception as exc:
            print("[ERROR] Bluetooth init failed:", exc)
            self.bluetooth = None

        # ============ Schedule ============
        Clock.schedule_once(self._initial_setup, 0.5)

        return self.sm

    # =====================================================
    # Initial Setup
    # =====================================================

    def _initial_setup(self, _dt):
        """Initial setup after UI loads"""
        self.refresh_devices()
        self.add_log("App is ready.")

        if FONT_AVAILABLE:
            self.add_log("Persian font loaded.")
        else:
            self.add_log("Warning: Persian font not found.")

    # =====================================================
    # On Stop
    # =====================================================

    def on_stop(self):
        """Called when app closes"""
        self._closing = True
        try:
            if self.bluetooth:
                self.bluetooth.disconnect()
        except Exception as exc:
            print("Error disconnecting Bluetooth:", exc)

    # =====================================================
    # Log
    # =====================================================

    def add_log(self, message):
        """
        Add message to Status screen log.
        Can be called from Bluetooth thread.
        """
        message = str(message)

        def update_log(_dt):
            if self._closing:
                return

            self._log_lines.append(message)
            self._log_lines = self._log_lines[-250:]

            try:
                if not hasattr(self, "sm"):
                    return

                screen = self.sm.get_screen("status")

                if "log_text" in screen.ids:
                    screen.ids.log_text.text = "\n".join(self._log_lines)

            except Exception as exc:
                print("Error updating log:", exc)

        Clock.schedule_once(update_log, 0)

    # =====================================================
    # Send Bluetooth Command
    # =====================================================

    def send_command(self, command):
        """
        Send command to Arduino.
        BluetoothManager.send adds LF automatically.
        """
        command = str(command).strip("\r\n")

        if not command:
            self.add_log("!! Empty command.")
            return False

        if not self.bluetooth:
            self.add_log("!! BluetoothManager not available.")
            return False

        if not self.bluetooth.is_connected():
            self.add_log("!! Bluetooth not connected; command not sent.")
            return False

        self.add_log(">> " + command)

        try:
            self.bluetooth.send(command)
            return True
        except Exception as exc:
            self.add_log("!! Send error: " + str(exc))
            return False

    # =====================================================
    # Fixed Commands
    # =====================================================

    def toggle(self, command):
        """
        Fixed commands:
        1 = Pump
        2 = Slow Motor
        3 = Fast Motor
        4 = Auto/Manual Mode
        T = Timer
        """
        allowed_commands = {"1", "2", "3", "4", "T"}

        if command not in allowed_commands:
            self.add_log("!! Invalid fixed command: " + str(command))
            return

        self.send_command(command)

    def request_time(self):
        """Request current time from Arduino"""
        self.send_command("t")

    def request_help_fa(self):
        """Request Persian help"""
        self.send_command("hFA")

    def request_help_en(self):
        """Request English help"""
        self.send_command("hEN")

    def refresh_status(self):
        """Request full status"""
        self.add_log("Requesting full status...")
        self.send_command("s")

    # =====================================================
    # Bluetooth Response Handler
    # =====================================================

    def on_bluetooth_line(self, line):
        """
        This is called from Bluetooth thread;
        UI update is scheduled on Clock.
        """
        line = str(line).strip()

        if not line:
            return

        self.add_log("<< " + line)

        Clock.schedule_once(
            lambda _dt, value=line: self.parse_arduino_line(value),
            0
        )

    def on_bluetooth_state(self, connected, message):
        """Connection state callback"""

        def update_ui(_dt):
            if self._closing:
                return

            try:
                home = self.sm.get_screen("home")
                settings = self.sm.get_screen("settings")

                home.connected = bool(connected)
                home.connection_text = "Connected" if connected else "Disconnected"
                settings.connection_text = "Connected" if connected else "Disconnected"

                self.add_log("** " + str(message))

            except Exception as exc:
                print("Error showing Bluetooth state:", exc)

        Clock.schedule_once(update_ui, 0)

    # =====================================================
    # Parse Arduino Response
    # =====================================================

    def parse_arduino_line(self, line):
        """
        Parse Arduino response lines.
        Examples:
        Temp: 28.5 C
        Humidity: 45.0 %
        Time: 14:30
        Mode: Auto
        Pump: ON
        Motor: Slow
        Timer: ON
        """
        line = str(line).strip()

        if not line:
            return

        try:
            home = self.sm.get_screen("home")
            status = self.sm.get_screen("status")

            # Temperature
            if line.startswith("Temp:"):
                value = line.split(":", 1)[1].strip()
                value = value.replace(" C", "").replace("C", "").strip()
                home.temperature = value
                status.temperature = value + " C"
                self._last_status["temperature"] = value

            # Humidity
            elif line.startswith("Humidity:"):
                value = line.split(":", 1)[1].strip()
                value = value.replace("%", "").strip()
                home.humidity = value
                status.humidity = value + " %"
                self._last_status["humidity"] = value

            # Time (format 1: Time: 14:30)
            elif line.startswith("Time:"):
                value = line.split(":", 1)[1].strip()
                home.rtc_time = value
                status.rtc_time = value
                self._last_status["time"] = value

            # Time (format 2: Time 14:30)
            elif line.startswith("Time "):
                value = line[5:].strip()
                home.rtc_time = value
                status.rtc_time = value
                self._last_status["time"] = value

            # Mode
            elif line.startswith("Mode:"):
                value = line.split(":", 1)[1].strip()
                status.mode = value
                self._last_status["mode"] = value

            # Pump
            elif line.startswith("Pump:"):
                value = line.split(":", 1)[1].strip()
                status.pump = value
                self._last_status["pump"] = value

            # Motor
            elif line.startswith("Motor:"):
                value = line.split(":", 1)[1].strip()
                status.motor = value
                self._last_status["motor"] = value

            # Timer
            elif line.startswith("Timer:"):
                value = line.split(":", 1)[1].strip()
                status.timer = value
                self._last_status["timer"] = value

            # ON Time
            elif line.startswith("ON Time:"):
                value = line.split(":", 1)[1].strip()
                self.add_log("ON time: " + value)

            # OFF Time
            elif line.startswith("OFF Time:"):
                value = line.split(":", 1)[1].strip()
                self.add_log("OFF time: " + value)

            # Other messages remain in log

        except Exception as exc:
            self.add_log("!! Parse error: " + str(exc))

    # =====================================================
    # Paired Bluetooth Devices
    # =====================================================

    def refresh_devices(self):
        """
        Get list of paired HC-05 devices
        and other Bluetooth Classic devices.
        """
        try:
            if not self.bluetooth:
                self.add_log("!! BluetoothManager not available.")
                return

            devices = self.bluetooth.get_paired_devices()

            settings = self.sm.get_screen("settings")

            if "device_spinner" not in settings.ids:
                return

            spinner = settings.ids.device_spinner

            spinner.values = [
                f"{name} [{address}]"
                for name, address in devices
            ]

            if devices:
                if spinner.text not in spinner.values:
                    spinner.text = spinner.values[0]

                settings.selected_device = spinner.text
                self.add_log(f"{len(devices)} paired device(s) found.")
            else:
                spinner.text = "No paired device found"
                settings.selected_device = ""
                self.add_log("No paired device found.")

        except Exception as exc:
            self.add_log("!! Device list error: " + str(exc))

    def connect_selected(self):
        """Connect to device selected in Spinner"""
        try:
            settings = self.sm.get_screen("settings")

            if "device_spinner" not in settings.ids:
                self.add_log("!! Device list not found.")
                return

            selected = settings.ids.device_spinner.text

            if not selected or "[" not in selected:
                settings.clock_feedback = "Select a paired device first."
                return

            address = selected.rsplit("[", 1)[1].rstrip("]")

            settings.clock_feedback = "Connecting..."
            self.add_log("Requesting connection to " + address)

            def connect_worker():
                try:
                    self.bluetooth.connect(address)
                except Exception as exc:
                    self.add_log("!! Connection failed: " + str(exc))

            threading.Thread(target=connect_worker, daemon=True).start()

        except Exception as exc:
            self.add_log("!! Connect start error: " + str(exc))

    def disconnect_bluetooth(self):
        """Disconnect Bluetooth"""
        try:
            if self.bluetooth:
                self.bluetooth.disconnect()
        except Exception as exc:
            self.add_log("!! Disconnect error: " + str(exc))

    # =====================================================
    # Dynamic Timer Commands
    # =====================================================

    def update_timer_preview(self):
        """Update timer preview"""
        try:
            screen = self.sm.get_screen("timer")

            if ("on_picker" not in screen.ids or
                    "off_picker" not in screen.ids):
                return

            on_time = screen.ids.on_picker.get_time_string()
            off_time = screen.ids.off_picker.get_time_string()

            screen.preview = (
                f"ON: {on_time[:2]}:{on_time[2:]}"
                f" | OFF: {off_time[:2]}:{off_time[2:]}"
            )

        except Exception as exc:
            self.add_log("!! Timer preview error: " + str(exc))

    def save_timer(self):
        """
        Send ONHHMM first.
        Then send OFFHHMM after 500ms.
        """
        try:
            screen = self.sm.get_screen("timer")

            on_time = screen.ids.on_picker.get_time_string()
            off_time = screen.ids.off_picker.get_time_string()

            if not self._valid_hhmm(on_time):
                screen.feedback = "Invalid ON time."
                return

            if not self._valid_hhmm(off_time):
                screen.feedback = "Invalid OFF time."
                return

            on_command = "ON" + on_time
            off_command = "OFF" + off_time

            if not self.send_command(on_command):
                screen.feedback = "Send failed; check Bluetooth."
                return

            screen.feedback = "ON sent; sending OFF..."

            def send_off(_dt):
                if self.send_command(off_command):
                    screen.feedback = "Settings sent."
                else:
                    screen.feedback = "OFF send failed."

            Clock.schedule_once(send_off, 0.5)

        except Exception as exc:
            self.add_log("!! Timer set error: " + str(exc))

    @staticmethod
    def _valid_hhmm(value):
        """Validate 4-digit HHMM string (00:00 - 23:59)"""
        if not isinstance(value, str):
            return False

        if len(value) != 4 or not value.isdigit():
            return False

        hour = int(value[:2])
        minute = int(value[2:])

        return (0 <= hour <= 23) and (0 <= minute <= 59)

    # =====================================================
    # RTC Keypad
    # =====================================================

    def clock_key(self, key):
        """
        Numeric keypad input.
        Example: 1, 4, 3, 0, OK → S1430
        """
        settings = self.sm.get_screen("settings")

        if key == "⌫" or key == "DEL":
            self._clock_digits = self._clock_digits[:-1]

        elif key == "CLR" or key == "Clear":
            self._clock_digits = ""

        elif key == "OK" or key == "✓" or key == "Enter":
            self._send_rtc_time()
            return

        elif str(key).isdigit() and len(self._clock_digits) < 4:
            self._clock_digits += str(key)

        self._update_clock_display()

        settings.clock_feedback = (
            f"{len(self._clock_digits)} of 4 digits entered"
            if self._clock_digits
            else "Enter 4 digits for clock"
        )

    def _update_clock_display(self):
        """Show 4 digits as HH:MM"""
        settings = self.sm.get_screen("settings")
        digits = self._clock_digits.ljust(4, "-")
        settings.clock_display = digits[:2] + ":" + digits[2:]

    def _send_rtc_time(self):
        """Validate and send S + HHMM"""
        settings = self.sm.get_screen("settings")

        if len(self._clock_digits) != 4:
            settings.clock_feedback = "Enter exactly 4 digits."
            return

        if not self._valid_hhmm(self._clock_digits):
            settings.clock_feedback = "Invalid time; range 00:00 - 23:59."
            return

        command = "S" + self._clock_digits

        if self.send_command(command):
            settings.clock_feedback = (
                "Clock command sent: "
                + self._clock_digits[:2]
                + ":"
                + self._clock_digits[2:]
            )
        else:
            settings.clock_feedback = "Send failed; check Bluetooth."

    # =====================================================
    # Screen Navigation
    # =====================================================

    def open_home(self):
        self.sm.current = "home"

    def open_timer(self):
        self.sm.current = "timer"
        self.update_timer_preview()

    def open_status(self):
        self.sm.current = "status"
        self.refresh_status()

    def open_settings(self):
        self.sm.current = "settings"
        self.refresh_devices()


# =========================================================
# Run
# =========================================================

if __name__ == "__main__":
    CoolerApp().run()