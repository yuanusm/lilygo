import asyncio
import csv
import struct
import threading
import time
from collections import deque
from tkinter import BOTH, BOTTOM, END, LEFT, RIGHT, TOP, Button, Canvas, Frame, Label, Listbox, StringVar, Tk, filedialog

import numpy as np
from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0000ec00-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "0000ec01-0000-1000-8000-00805f9b34fb"
DATA_UUID = "0000ec02-0000-1000-8000-00805f9b34fb"
SAMPLE_RATE = 500
FFT_SIZE = 1024
MONITORED_BINS_HZ = (50, 100, 150)

class EcgBleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LilyGO ECG BLE Viewer")
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.devices = []
        self.client = None
        self.samples = []
        self.recording_samples = []
        self.graph = deque(maxlen=SAMPLE_RATE * 10)
        self.fft_graph = deque(maxlen=FFT_SIZE)
        self.packet_count = 0
        self.last_sample_count = 0
        self.last_rate_time = time.time()
        self.recording_until = None
        self.recording_duration = 0
        self.status = StringVar(value="Disconnected")
        self.rate = StringVar(value="0 SPS")
        self.packets = StringVar(value="0 packets")
        self.recording = StringVar(value="Recording: off")
        self.energy = {hz: StringVar(value=f"{hz} Hz: -- dB") for hz in MONITORED_BINS_HZ}
        self._build_ui()
        self.root.after(50, self._draw)
        self.root.after(1000, self._stats)

    def _build_ui(self):
        top = Frame(self.root)
        top.pack(side=TOP, fill=BOTH)
        self.listbox = Listbox(top, height=5, width=55)
        self.listbox.pack(side=LEFT, padx=4, pady=4)
        buttons = Frame(top)
        buttons.pack(side=RIGHT)
        for text, command in [
            ("Scan BLE", self.scan), ("Connect", self.connect), ("Disconnect", self.disconnect),
            ("Start Raw", lambda: self.send("START_STREAM_RAW")),
            ("Start Filtered", lambda: self.send("START_STREAM_FILTERED")),
            ("Get Buffer Raw", lambda: self.send("GET_BUFFER_RAW")),
            ("Get Buffer Filtered", lambda: self.send("GET_BUFFER_FILTERED")),
            ("Stop", lambda: self.send("STOP_STREAM")), ("Export CSV", self.export_csv),
            ("Record 1 min", lambda: self.start_timed_recording(60)),
            ("Record 5 min", lambda: self.start_timed_recording(300)),
        ]:
            Button(buttons, text=text, command=command).pack(fill=BOTH, padx=2, pady=1)
        info = Frame(self.root)
        info.pack(side=TOP, fill=BOTH)
        Label(info, textvariable=self.status).pack(side=LEFT, padx=8)
        Label(info, textvariable=self.rate).pack(side=LEFT, padx=8)
        Label(info, textvariable=self.packets).pack(side=LEFT, padx=8)
        Label(info, textvariable=self.recording).pack(side=LEFT, padx=8)
        energy_frame = Frame(self.root)
        energy_frame.pack(side=TOP, fill=BOTH)
        for hz in MONITORED_BINS_HZ:
            Label(energy_frame, textvariable=self.energy[hz]).pack(side=LEFT, padx=8)
        plots = Frame(self.root)
        plots.pack(side=BOTTOM, fill=BOTH, expand=True)
        self.canvas = Canvas(plots, width=1000, height=300, bg="black")
        self.canvas.pack(side=TOP, fill=BOTH, expand=True)
        self.fft_canvas = Canvas(plots, width=1000, height=220, bg="#101018")
        self.fft_canvas.pack(side=BOTTOM, fill=BOTH, expand=True)

    def run_coro(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def scan(self):
        async def _scan():
            self.status.set("Scanning...")
            self.devices = await BleakScanner.discover(timeout=5.0, service_uuids=[SERVICE_UUID])
            self.root.after(0, self._update_devices)
        self.run_coro(_scan())

    def _update_devices(self):
        self.listbox.delete(0, END)
        for dev in self.devices:
            self.listbox.insert(END, f"{dev.name or 'Unknown'}  {dev.address}")
        self.status.set(f"Found {len(self.devices)} device(s)")

    def connect(self):
        if not self.devices or self.listbox.curselection() == ():
            return
        dev = self.devices[self.listbox.curselection()[0]]
        async def _connect():
            self.client = BleakClient(dev.address, disconnected_callback=lambda _: self.root.after(0, self._disconnected))
            await self.client.connect()
            await self.client.start_notify(DATA_UUID, self._notification)
            self.root.after(0, lambda: self.status.set("Connected"))
        self.run_coro(_connect())

    def disconnect(self):
        async def _disconnect():
            if self.client:
                await self.client.disconnect()
        self.run_coro(_disconnect())

    def _disconnected(self):
        self.status.set("Disconnected")

    def send(self, command):
        async def _send():
            if self.client and self.client.is_connected:
                await self.client.write_gatt_char(COMMAND_UUID, command.encode(), response=False)
        self.run_coro(_send())

    def _notification(self, _, data: bytearray):
        if len(data) % 2:
            return
        now = time.time()
        values = struct.unpack("<" + "h" * (len(data) // 2), data)
        self.packet_count += 1
        for i, value in enumerate(values):
            ts = now - (len(values) - 1 - i) / SAMPLE_RATE
            row = (ts, value)
            self.samples.append(row)
            if self.recording_until is not None:
                self.recording_samples.append(row)
            self.graph.append(value)
            self.fft_graph.append(value)

    def _draw_series(self, canvas, data, color):
        w = max(canvas.winfo_width(), 10)
        h = max(canvas.winfo_height(), 10)
        if len(data) > 1:
            mn, mx = min(data), max(data)
            span = max(mx - mn, 1)
            pts = []
            for i, v in enumerate(data):
                x = i * (w - 1) / (len(data) - 1)
                y = h - 1 - ((v - mn) * (h - 20) / span + 10)
                pts.extend((x, y))
            canvas.create_line(*pts, fill=color, width=1)

    def _compute_fft(self):
        data = np.asarray(self.fft_graph, dtype=np.float64)
        if data.size < 32:
            return np.array([]), np.array([])
        data = data - np.mean(data)
        window = np.hanning(data.size)
        spectrum = np.fft.rfft(data * window)
        freqs = np.fft.rfftfreq(data.size, d=1.0 / SAMPLE_RATE)
        mag = np.abs(spectrum) / max(np.sum(window) / 2.0, 1.0)
        return freqs, mag

    def _draw_fft(self):
        self.fft_canvas.delete("all")
        w = max(self.fft_canvas.winfo_width(), 10)
        h = max(self.fft_canvas.winfo_height(), 10)
        freqs, mag = self._compute_fft()
        if freqs.size == 0:
            return
        max_freq = min(200, SAMPLE_RATE / 2)
        mask = freqs <= max_freq
        freqs, mag = freqs[mask], mag[mask]
        db = 20 * np.log10(np.maximum(mag, 1e-9))
        floor = max(float(np.max(db)) - 80.0, -120.0)
        ceiling = max(float(np.max(db)), floor + 1.0)
        pts = []
        for f, value in zip(freqs, db):
            x = f * (w - 1) / max_freq
            y = h - 1 - ((value - floor) * (h - 20) / (ceiling - floor) + 10)
            pts.extend((x, y))
        if len(pts) >= 4:
            self.fft_canvas.create_line(*pts, fill="#66ccff", width=1)
        for hz in MONITORED_BINS_HZ:
            idx = int(np.argmin(np.abs(freqs - hz)))
            value = float(db[idx])
            self.energy[hz].set(f"{hz} Hz: {value:.1f} dB")
            x = hz * (w - 1) / max_freq
            self.fft_canvas.create_line(x, 0, x, h, fill="#ffcc00")
            self.fft_canvas.create_text(x + 18, 12, text=f"{hz}", fill="#ffcc00")

    def _draw(self):
        self.canvas.delete("all")
        self._draw_series(self.canvas, list(self.graph), "#00ff66")
        self._draw_fft()
        self.root.after(50, self._draw)

    def _stats(self):
        now = time.time()
        delta = max(now - self.last_rate_time, 0.001)
        sps = (len(self.samples) - self.last_sample_count) / delta
        self.last_sample_count = len(self.samples)
        self.last_rate_time = now
        self.rate.set(f"{sps:.1f} SPS")
        self.packets.set(f"{self.packet_count} packets")
        if self.recording_until is not None:
            remaining = self.recording_until - now
            if remaining <= 0:
                self.finish_timed_recording()
            else:
                self.recording.set(f"Recording: {remaining:.0f}s left")
        self.root.after(1000, self._stats)

    def start_timed_recording(self, seconds):
        self.recording_duration = seconds
        self.recording_samples = []
        self.recording_until = time.time() + seconds
        self.recording.set(f"Recording: {seconds}s left")

    def finish_timed_recording(self):
        duration = self.recording_duration
        rows = list(self.recording_samples)
        self.recording_until = None
        self.recording.set("Recording: saving...")
        filename = time.strftime(f"ecg_recording_{duration//60}min_%Y%m%d_%H%M%S.csv")
        self.write_csv(filename, rows)
        self.recording.set(f"Saved {filename}")

    def write_csv(self, path, rows):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sample"])
            writer.writerows(rows)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            self.write_csv(path, self.samples)

if __name__ == "__main__":
    root = Tk()
    app = EcgBleApp(root)
    root.mainloop()
