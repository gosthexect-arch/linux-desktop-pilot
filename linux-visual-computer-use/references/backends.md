# Desktop control adapters

Inspect installed tool schemas. Similarly named tools from Open Computer Use
and computer-use-linux may accept different arguments.

The existing Open Computer Use exposes app discovery, state, mouse, keyboard and
semantic actions. Linux coordinate input is compositor-dependent. `sky_key`,
`sky_click`, `app_post`, `agent_display` and `restore` are not portable Linux
features. Use only supported methods. An empty AT-SPI list does not mean the
compositor has no windows.

## Native Linux backend: Hyprland, GNOME and KDE

The optional [computer-use-linux](https://github.com/agent-sh/computer-use-linux)
provides compositor-aware window targeting, AT-SPI, capture, portal/uinput input
and post-action observations. This adapter was developed against 0.7.25. Its
upstream support declaration does not certify a local session.

`python3 SKILL_DIR/scripts/desktop.py native tools` lists live tools;
`native tools --tool NAME` returns one tool's input schema.
Example one-shot calls, replacing the PID with an observed target:

```text
python3 SKILL_DIR/scripts/desktop.py native call list_windows --args '{}'
python3 SKILL_DIR/scripts/desktop.py native call screenshot --args '{"pid":123,"raise_window":true}' --output-dir /absolute/private/captures
```

Each call initializes a new MCP process and saves returned images privately.
Use a persistent connected MCP for element indexes; one-shot calls reject them.
Observed window IDs/PIDs or semantic selectors can be used if identity is
rechecked. Inspect each tool's targeting schema. `run_shell` is unavailable
through this adapter. An action followed by a capture error must not be replayed
without checking whether the action already happened.

GNOME can require the backend's supported window-control extension. KWin has
its own integration. Portal availability/consent and AT-SPI are separate from
each other. Test real capture and input after doctor. An InputCapture portal is
not a substitute for RemoteDesktop injection. See the
[official RemoteDesktop interface](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html).

If uinput is needed, diagnose device access. Never make `/dev/uinput`
world-writable, run the agent as root or reset desktop configuration to pass a
test. Run setup/extension installation only when necessary and within the
user's installation/repair scope. Do not switch desktop sessions for an ordinary
GUI task.

## Hyprland: direct Wayland fallback

The included fallback uses Hyprland IPC for identity/focus, `grim -s 1` for
logical-region screenshots, `wtype` for keys/text and the virtual pointer
protocol for mouse input. It needs no configuration change or uinput permission.
It detects protocols instead of assuming they exist on GNOME/KWin.

```text
python3 SKILL_DIR/scripts/desktop.py hypr windows
python3 SKILL_DIR/scripts/desktop.py hypr focus --window 0xOBSERVED_ADDRESS
python3 SKILL_DIR/scripts/desktop.py hypr capture --window 0xOBSERVED_ADDRESS --output /absolute/private/before.png
```

View the local image. A JSON sidecar records identity, geometry, workspace and
image digest. Input requires a snapshot less than 60 seconds old, with unchanged
geometry and the intended window still focused. A newly opened modal requires
new window discovery/capture.

```text
python3 SKILL_DIR/scripts/desktop.py hypr click --snapshot /absolute/private/before.png.json --x 230 --y 180 --after /absolute/private/after.png
python3 SKILL_DIR/scripts/desktop.py hypr key --snapshot /absolute/private/after.png.json --key Ctrl+L --after /absolute/private/address.png
python3 SKILL_DIR/scripts/desktop.py hypr text --snapshot /absolute/private/address.png.json --after /absolute/private/typed.png
```

`text` reads literal UTF-8 from stdin, up to 100 Unicode characters per call.
It does not print text or place it in child argv. For longer input, verify each
segment and obtain a fresh snapshot before another segment; do not replay a
whole message after partial failure. Verify the field and destination before
Enter. Use a persistent native backend for long text when it works reliably.

Coordinates refer to the ORIGINAL screenshot dimensions, not a scaled viewer
thumbnail. `click` supports left/right/middle and double click, `move` hover,
`scroll` both axes, and `drag` all three buttons. `--modifiers` accepts
Shift/Ctrl/Alt/Super combinations when virtual keyboard and libxkbcommon are
available. Read `--help` for exact arguments. Cleanup releases held inputs.

Cursor landing is checked through Hyprland before pressing a mouse button.
Moved targets or failed landing cancel input. Capture is a focused desktop
region, not hidden window contents. Do not operate occluded/inactive windows.
There is no automatic retry of a potentially delivered action.

## Install the optional native backend

Prefer an existing CLI/connector. The portable installer can also install the
pinned optional runtime after inspection of the upstream package installer:

```text
python3 SKILL_DIR/scripts/install.py --with-native
```

The installer resolves the current user's data directory; no author-specific
path is required. Upstream downloads release binaries and verifies release
checksums. The locator checks PATH,
`$XDG_DATA_HOME/linux-visual-computer-use/runtime/node_modules/.bin/`, and
`~/.local/share/linux-visual-computer-use/runtime/node_modules/.bin/`.
`LVCU_NATIVE_BIN` can identify an absolute installed executable.

For persistent Codex MCP, add a dedicated entry using the resolved absolute
binary and `mcp` as its sole argument, preserving unrelated config. The helper
does not modify MCP configuration. New registration can need a client reconnect;
the one-shot helper works immediately.

Protocol sources used by the fallback:
[virtual pointer](https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-virtual-pointer-unstable-v1.xml),
[virtual keyboard](https://github.com/atx/wtype/blob/master/protocol/virtual-keyboard-unstable-v1.xml).
