# -*- coding: utf-8 -*-
"""Thread-safe Bluetooth Classic SPP manager for Android HC-05."""
import threading
import time

SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"


class BluetoothManager:
    def __init__(self, on_line=None, on_state=None):
        self.on_line = on_line or (lambda line: None)
        self.on_state = on_state or (lambda connected, message: None)
        self._adapter = None
        self._socket = None
        self._reader_thread = None
        self._stop_event = threading.Event()
        self._write_lock = threading.Lock()
        self._state_lock = threading.RLock()
        self._connected = False
        self._device = None
        self._init_android()

    def _init_android(self):
        try:
            from jnius import autoclass
            self._BluetoothAdapter = autoclass("android.bluetooth.BluetoothAdapter")
            self._UUID = autoclass("java.util.UUID")
            self._adapter = self._BluetoothAdapter.getDefaultAdapter()
        except Exception:
            self._adapter = None

    def _notify(self, connected, message):
        try:
            self.on_state(bool(connected), str(message))
        except Exception:
            pass

    def get_paired_devices(self):
        if self._adapter is None:
            raise RuntimeError("Bluetooth فقط در محیط اندروید در دسترس است")
        if not self._adapter.isEnabled():
            raise RuntimeError("بلوتوث گوشی خاموش است")
        result = []
        for device in self._adapter.getBondedDevices().toArray():
            try:
                result.append((str(device.getName() or "بدون نام"), str(device.getAddress())))
            except Exception:
                continue
        return sorted(result, key=lambda item: item[0].lower())

    def connect(self, address):
        self.disconnect(notify=False)
        if self._adapter is None:
            raise RuntimeError("Android Bluetooth API در دسترس نیست")
        if not self._adapter.isEnabled():
            raise RuntimeError("ابتدا بلوتوث گوشی را روشن کنید")
        try:
            device = self._adapter.getRemoteDevice(address)
            uuid = self._UUID.fromString(SPP_UUID)
            try:
                socket = device.createRfcommSocketToServiceRecord(uuid)
                socket.connect()
            except Exception:
                try:
                    socket.close()
                except Exception:
                    pass
                # HC-05 modules sometimes need the insecure SPP socket.
                socket = device.createInsecureRfcommSocketToServiceRecord(uuid)
                socket.connect()
            with self._state_lock:
                self._socket = socket
                self._device = device
                self._connected = True
                self._stop_event.clear()
            self._reader_thread = threading.Thread(target=self.read_loop, daemon=True)
            self._reader_thread.start()
            self._notify(True, "اتصال برقرار شد: " + str(device.getName()))
        except Exception as exc:
            self.disconnect(notify=False)
            self._notify(False, "اتصال ناموفق: " + str(exc))
            raise

    def disconnect(self, notify=True):
        self._stop_event.set()
        with self._state_lock:
            sock = self._socket
            self._socket = None
            self._connected = False
            self._device = None
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        if notify:
            self._notify(False, "اتصال قطع شد")

    def is_connected(self):
        with self._state_lock:
            if not self._connected or self._socket is None:
                return False
            try:
                return bool(self._socket.isConnected())
            except Exception:
                return self._connected

    def send(self, command):
        """Send command followed by one LF; strip accidental line endings first."""
        if not isinstance(command, str):
            command = str(command)
        command = command.rstrip("\r\n")
        if not command:
            raise ValueError("دستور خالی قابل ارسال نیست")
        with self._state_lock:
            sock = self._socket
            connected = self._connected
        if not connected or sock is None:
            raise ConnectionError("بلوتوث متصل نیست")
        payload = (command + "\n").encode("utf-8")
        with self._write_lock:
            output_stream = sock.getOutputStream()
            output_stream.write(payload)
            output_stream.flush()

    def read_loop(self):
        buffer = bytearray()
        try:
            while not self._stop_event.is_set():
                with self._state_lock:
                    sock = self._socket
                if sock is None:
                    break
                stream = sock.getInputStream()
                available = int(stream.available())
                if available <= 0:
                    time.sleep(0.03)
                    continue
                for _ in range(min(available, 512)):
                    value = int(stream.read())
                    if value < 0:
                        raise ConnectionError("ارتباط بلوتوث بسته شد")
                    if value == 10:  # LF
                        line = buffer.decode("utf-8", errors="replace").rstrip("\r")
                        buffer.clear()
                        if line:
                            try:
                                self.on_line(line)
                            except Exception:
                                pass
                    else:
                        if len(buffer) < 4096:
                            buffer.append(value)
                        else:
                            buffer.clear()
        except Exception as exc:
            if not self._stop_event.is_set():
                self._notify(False, "خطای دریافت: " + str(exc))
        finally:
            if not self._stop_event.is_set():
                self.disconnect(notify=True)
