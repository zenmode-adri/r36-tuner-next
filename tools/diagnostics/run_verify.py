"""
Transfer and run verify_audit.sh on R36 via SSH.
Usage: python run_verify.py
"""
import paramiko, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '192.168.1.87'
USER = 'ark'
PASS = 'ark'

SCRIPT_LOCAL = os.path.join(os.path.dirname(__file__), 'verify_audit.sh')
SCRIPT_REMOTE = '/tmp/r36_verify_audit.sh'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

print(f"Connecting to {HOST}...")
try:
    c.connect(HOST, port=22, username=USER, password=PASS, timeout=10)
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# Transfer script via sftp
print("Transferring verify_audit.sh...")
sftp = c.open_sftp()
sftp.put(SCRIPT_LOCAL, SCRIPT_REMOTE)
sftp.close()

# Execute with streaming output
print("Running on device...\n")
print("=" * 50)

cmd = f'echo {PASS} | sudo -S bash {SCRIPT_REMOTE}'
_, out, err = c.exec_command(cmd, get_pty=False)

for line in out:
    print(line, end='', flush=True)

exit_code = out.channel.recv_exit_status()
errs = err.read().decode('utf-8', errors='replace').strip()
if errs:
    print(f"\n[stderr] {errs}")

c.close()
print(f"\nExit code: {exit_code}")
