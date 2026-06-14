import asyncio
import csv
import struct
import threading
import time
from collections import deque
from tkinter import BOTH, BOTTOM, DISABLED, END, LEFT, NORMAL, RIGHT, TOP, Button, Canvas, Frame, Label, Listbox, StringVar, Tk, filedialog

from bleak import BleakClient, BleakScanner

SERVICE_UUID = "0000ec00-0000-1000-8000-00805f9b34fb"
COMMAND_UUID = "0000ec01-0000-1000-8000-00805f9b34fb"
DATA_UUID = "0000ec02-0000-1000-8000-00805f9b34fb"
SAMPLE_RATE = 500

class EcgBleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LilyGO ECG BLE Viewer")
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        self.devices = []
        self.client = None
        self.samples = []
        self.graph = deque(maxlen=SAMPLE_RATE * 10)
        self.packet_count = 0
        self.last_sample_count = 0
        self.last_rate_time = time.time()
        self.status = StringVar(value="Disconnected")
        self.rate = StringVar(value="0 SPS")
        self.packets = StringVar(value="0 packets")
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
        ]:
            Button(buttons, text=text, command=command).pack(fill=BOTH, padx=2, pady=1)
        info = Frame(self.root)
        info.pack(side=TOP, fill=BOTH)
        Label(info, textvariable=self.status).pack(side=LEFT, padx=8)
        Label(info, textvariable=self.rate).pack(side=LEFT, padx=8)
        Label(info, textvariable=self.packets).pack(side=LEFT, padx=8)
        self.canvas = Canvas(self.root, width=1000, height=420, bg="black")
        self.canvas.pack(side=BOTTOM, fill=BOTH, expand=True)

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
        base = len(self.samples)
        for i, value in enumerate(values):
            ts = now - (len(values) - 1 - i) / SAMPLE_RATE
            self.samples.append((ts, value))
            self.graph.append(value)

    def _draw(self):
        self.canvas.delete("all")
        w = max(self.canvas.winfo_width(), 10)
        h = max(self.canvas.winfo_height(), 10)
        data = list(self.graph)
        if len(data) > 1:
            mn, mx = min(data), max(data)
            span = max(mx - mn, 1)
            pts = []
            for i, v in enumerate(data):
                x = i * (w - 1) / (len(data) - 1)
                y = h - 1 - ((v - mn) * (h - 20) / span + 10)
                pts.extend((x, y))
            self.canvas.create_line(*pts, fill="#00ff66", width=1)
        self.root.after(50, self._draw)

    def _stats(self):
        now = time.time()
        delta = max(now - self.last_rate_time, 0.001)
        sps = (len(self.samples) - self.last_sample_count) / delta
        self.last_sample_count = len(self.samples)
        self.last_rate_time = now
        self.rate.set(f"{sps:.1f} SPS")
        self.packets.set(f"{self.packet_count} packets")
        self.root.after(1000, self._stats)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "sample"])
            writer.writerows(self.samples)

if __name__ == "__main__":
    root = Tk()
    app = EcgBleApp(root)
    root.mainloop()
