"""r36_ssh.py — reusable SSH helpers for R36S deployment scripts.

All functions assume default credentials unless overridden.  They use UTF-8
for text I/O and avoid shell-quoting pitfalls by using SFTP for file
transfers and explicit sudo password handling for remote commands.
"""

import os
import shlex

import paramiko

HOST = "192.168.1.87"
USER = "ark"
PASS = "ark"


class R36SSH:
    """Context-manager friendly SSH connection to the R36S."""

    def __init__(self, host=HOST, user=USER, password=PASS, timeout=10):
        self.host = host
        self.user = user
        self.password = password
        self.timeout = timeout
        self._client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def connect(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._client.connect(
            self.host,
            port=22,
            username=self.user,
            password=self.password,
            timeout=self.timeout,
        )
        return self._client

    def close(self):
        if self._client:
            self._client.close()
            self._client = None

    @property
    def client(self):
        if self._client is None:
            raise RuntimeError("SSH not connected")
        return self._client

    def run(self, cmd, sudo=False, timeout=30):
        """Run a remote command.  Returns (stdout, stderr, exit_code)."""
        if sudo:
            # Pass the password via stdin to sudo -S.
            full = f"echo {self.password} | sudo -S {cmd}"
        else:
            full = cmd
        stdin, stdout, stderr = self.client.exec_command(full, timeout=timeout)
        if sudo:
            stdin.write(self.password + "\n")
            stdin.flush()
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        code = stdout.channel.recv_exit_status()
        return out, err, code

    def run_sudo(self, cmd, timeout=30):
        """Convenience wrapper for sudo commands."""
        return self.run(cmd, sudo=True, timeout=timeout)

    def put(self, local_path, remote_path, mode="755", sudo=True):
        """Upload a local file to a remote path using SFTP + optional sudo cp."""
        local_path = os.path.abspath(local_path)
        if not os.path.exists(local_path):
            raise FileNotFoundError(local_path)

        basename = os.path.basename(remote_path)
        tmp = f"/tmp/r36_put_{basename}"
        mode_oct = int(mode, 8)

        sftp = self.client.open_sftp()
        sftp.put(local_path, tmp)
        sftp.chmod(tmp, mode_oct)
        sftp.close()

        if sudo:
            quoted_tmp = shlex.quote(tmp)
            quoted_remote = shlex.quote(remote_path)
            # cp -p preserves the executable bits set above.  chmod may fail if
            # the destination binary is already running, so ignore that specific
            # failure as long as the file exists with the requested mode.
            out, err, code = self.run_sudo(
                f"cp -f {quoted_tmp} {quoted_remote} && "
                f"(chmod {mode} {quoted_remote} 2>/dev/null || true) && "
                f"stat -c '%a' {quoted_remote}"
            )
            self.run(f"rm -f {quoted_tmp}")
        else:
            out, err, code = self.run(
                f"cp {shlex.quote(tmp)} {shlex.quote(remote_path)} && "
                f"chmod {mode} {shlex.quote(remote_path)}"
            )
            self.run(f"rm -f {shlex.quote(tmp)}")

        if code != 0:
            raise RuntimeError(f"put failed: {err}")

        # Verify the remote mode matches what was requested (sudo path only).
        if sudo and out.strip():
            try:
                actual_mode = int(out.strip(), 8)
                if (actual_mode & 0o777) != mode_oct:
                    raise RuntimeError(f"put failed: mode {oct(actual_mode)} != requested {oct(mode_oct)}")
            except ValueError:
                pass
        return out, err, code

    def remove(self, remote_path, sudo=True):
        """Remove a remote file or directory."""
        cmd = f"rm -rf {shlex.quote(remote_path)}"
        return self.run(cmd, sudo=sudo)


def connect(host=HOST, user=USER, password=PASS, timeout=10):
    """Return a connected R36SSH instance."""
    ssh = R36SSH(host=host, user=user, password=password, timeout=timeout)
    ssh.connect()
    return ssh


def get_client(host=HOST, user=USER, password=PASS, timeout=10):
    """Return a raw connected paramiko SSHClient.

    Use this for legacy scripts that call c.exec_command(...) directly.
    """
    return connect(host=host, user=user, password=password, timeout=timeout).client


def connect_with_retry(retries=24, delay=5, host=HOST, user=USER, password=PASS, timeout=5):
    """Try to connect, retrying every `delay` seconds. Returns R36SSH instance."""
    import time

    for i in range(retries):
        try:
            return connect(host=host, user=user, password=password, timeout=timeout)
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(delay)
    raise RuntimeError("Should never reach here")


def get_client_with_retry(retries=24, delay=5, host=HOST, user=USER, password=PASS, timeout=5):
    """Like connect_with_retry but returns the raw paramiko SSHClient."""
    return connect_with_retry(
        retries=retries, delay=delay, host=host, user=user, password=password, timeout=timeout
    ).client
