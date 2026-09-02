# Clean Environment Test

Use a Windows test machine, Windows Sandbox, or a new virtual machine. Do not
copy `%LOCALAPPDATA%\GameTuner` from a development computer. The smoke test does
not require Steam, Epic, GOG, an installed game, or access to GitHub.

## 1. Prepare the source tree

Copy or clone the repository, then open PowerShell at the repository root.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

If PowerShell blocks activation, run the commands through `cmd.exe`, or run the
Python executable directly as shown below.

## 2. Verify the offline safety path

```powershell
python tools\clean_environment_smoke_test.py
python -m pytest -q
python -m compileall -q .
```

Expected result: the smoke test prints `PASS`, all pytest tests pass, and
`compileall` returns no output. The smoke test verifies that writes are blocked
without explicit test-mode consent and that a metadata-only diagnostic ZIP is
anonymous and contains no configuration-text copy.

## 3. Verify the customer GUI workflow

```powershell
python main.py
```

Check the following manually:

1. The window starts even when no game platform is installed.
2. `Check Rules` can be skipped without preventing the application from opening.
3. `Enable Test Writes` shows a confirmation. Select No and verify it stays disabled.
4. Select any detected game and use `Export Diagnostics`. Choose No when asked to
   include content. Confirm the generated ZIP is stored below
   `%LOCALAPPDATA%\GameTuner\reports`.

For a game in a `write_verified` Release rule, repeat step 3 and select Yes. A
write attempt must still create a backup and must restore it if validation fails.

## 4. Optional EXE packaging test

Build the executable on a development machine, then copy only the generated
`dist\GameTuner` folder to a second clean machine:

```powershell
pyinstaller --noconfirm --windowed --name GameTuner main.py
```

On the second machine, run `GameTuner.exe` and repeat the GUI checks above. Do
not distribute customer diagnostic ZIP files, `%LOCALAPPDATA%\GameTuner`, or any
unreviewed verification candidate with the executable.