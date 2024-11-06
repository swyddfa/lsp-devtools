from __future__ import annotations

import logging
import typing

from rich import progress
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style

if typing.TYPE_CHECKING:
    from rich.console import Console
    from rich.console import ConsoleOptions
    from rich.console import RenderResult
    from rich.table import Column


class PacketPipe:
    """Rich renderable that generates the visualisation of the in-flight packets between
    client and server."""

    def __init__(self, server_packets, client_packets):
        self.server_packets = server_packets
        self.client_packets = client_packets

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        pipe_length = width - 2

        client_packets = {int(p * pipe_length) for p in self.client_packets}
        server_packets = {
            pipe_length - int(p * pipe_length) for p in self.server_packets
        }

        yield Segment("[")

        for idx in range(pipe_length):
            if idx in server_packets:
                yield Segment("●", style=Style(color="blue"))
            elif idx in client_packets:
                yield Segment("●", style=Style(color="red"))
            else:
                yield Segment(" ")

        yield Segment("]")

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return Measurement(4, options.max_width)


class PacketPipeColumn(progress.ProgressColumn):
    """Visualizes messages sent between client and server as "packets"."""

    def __init__(
        self, duration: float = 1.0, table_column: Column | None = None
    ) -> None:
        self.client_count = 0
        self.server_count = 0
        self.server_times: list[float] = []
        self.client_times: list[float] = []

        # How long it should take for a packet to propogate.
        self.duration = duration

        super().__init__(table_column)

    def _update_packets(self, task: progress.Task, source: str) -> list[float]:
        """Update the packet positions for the given message source.

        Parameters
        ----------
        task
           The task object

        source
           The message source

        Returns
        -------
        List[float]
         A list of floats in the range [0,1] indicating the number of packets in flight
         and their position
        """
        count_attr = f"{source}_count"
        time_attr = f"{source}_times"

        count = getattr(self, count_attr)
        times = getattr(self, time_attr)
        current_count = task.fields[count_attr]
        current_time = task.get_time()

        if current_count > count:
            setattr(self, count_attr, current_count)
            times.append(current_time)

        packets = []
        new_times = []

        for time in times:
            if (delta := current_time - time) > self.duration:
                continue

            packets.append(delta / self.duration)
            new_times.append(time)

        setattr(self, time_attr, new_times)
        return packets

    def render(self, task: progress.Task) -> PacketPipe:
        """Render the packet pipe."""

        client_packets = self._update_packets(task, "client")
        server_packets = self._update_packets(task, "server")

        return PacketPipe(server_packets=server_packets, client_packets=client_packets)


class SpinnerHandler(logging.Handler):
    """A logging handler that shows a customised progress bar, used to show feedback for
    an active connection."""

    def __init__(self, console: Console, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.server_count = 0
        self.client_count = 0
        self.progress = progress.Progress(
            progress.TextColumn("[red]CLIENT[/red] {task.fields[client_method]}"),
            PacketPipeColumn(),
            progress.TextColumn("{task.fields[server_method]} [blue]SERVER[/blue]"),
            console=console,
            auto_refresh=True,
            expand=True,
        )
        self.task = self.progress.add_task(
            "",
            total=None,
            server_method="",
            client_method="",
            server_count=self.server_count,
            client_count=self.client_count,
        )

    def emit(self, record: logging.LogRecord):
        message = record.args

        if not isinstance(message, dict):
            return

        self.progress.start()

        method = message.get("method", None)
        source = record.__dict__["Message-Source"]
        args = {}

        if method:
            args[f"{source}_method"] = method
            count = getattr(self, f"{source}_count") + 1

            setattr(self, f"{source}_count", count)
            args[f"{source}_count"] = count

        self.progress.update(self.task, **args)
