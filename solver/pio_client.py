import subprocess
import time
from typing import List, Optional

class PioSolverClient:
    """
    Wrapper for PioSolver's Universal Poker Interface (UPI).
    Handles communication via stdin/stdout.
    """
    def __init__(self, executable_path: str = "PioSolver-basic.exe"):
        self.executable_path = executable_path
        self.process = None

    def connect(self):
        """Starts the solver process."""
        try:
            self.process = subprocess.Popen(
                [self.executable_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Consume header
            self._read_response()
        except FileNotFoundError:
            print(f"Solver executable not found at {self.executable_path}. Running in Mock Mode.")
            self.process = None

    def send_command(self, command: str) -> List[str]:
        """Sends a UPI command and returns the response lines."""
        if not self.process:
            return ["MOCK_RESPONSE: OK"]

        # PioSolver expects commands ending with newline
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

        return self._read_response()

    def _read_response(self) -> List[str]:
        """Reads lines until a defined end marker (usually empty line or prompt)."""
        lines = []
        if not self.process:
            return lines

        while True:
            line = self.process.stdout.readline()
            if not line: break
            line = line.strip()
            if line == "END": # Hypothetical UPI terminator
                break
            lines.append(line)
        return lines

    def lock_node(self, node_id: str, strategy: List[float]):
        """
        Sends a 'lock_node' command to force a strategy.
        strategy: List of probabilities [fold, call, raise]
        """
        # Format: lock_node NODE_ID PROBS...
        probs_str = " ".join(map(str, strategy))
        cmd = f"lock_node {node_id} {probs_str}"
        self.send_command(cmd)

    def solve(self):
        self.send_command("go")
