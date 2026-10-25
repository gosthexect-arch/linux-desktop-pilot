# Acceptance and evidence

Required real sessions: Hyprland/Wayland, GNOME/Wayland and KDE Plasma/Wayland.
Run the same tasks in separate test sessions/VMs when available. A VM must render
the actual compositor and receive input. Do not install/switch the user's desktop
for an ordinary GUI task. Adapter unit tests are not desktop acceptance.

Record date, distribution, compositor/version, session type, runtime,
application/version, monitor layout/scales, results and observed evidence.
Also record the selected model and host when the client exposes their identity.
Otherwise record them as unknown. A model's name alone is not acceptance evidence.
Statuses: passed, failed, blocked, not-run. Only observed results are passes.
A doctor report or one successful key does not pass an entire desktop.

| Case | Required visible result |
| --- | --- |
| Browser | Open test page through UI, switch tabs, back/forward, follow a link, scroll to target |
| Form | Accented text, correction, selection change, local submission and visible confirmation |
| Draft | Compose/edit multiline synthetic text without sending; verify actual contents |
| Real WhatsApp | Navigate to designated conversation and prepare draft; sending needs explicit authorization |
| Pointer/canvas | Hover, single/double/right/middle click, left/middle/modifier drag and both scroll axes |
| Existing Blender project | Edit test copy, inspect geometry/material, save and reopen through UI |
| Recovery | Diagnose different panel/keymap/path and reach goal through another route |
| Stale state | Focus/resize/workspace change after capture must refuse input until reobserved |
| Monitors | Operate each monitor; test scaling/negative origins only on real matching layouts |
| Interruption | Reobserve after dialog/focus change; avoid replaying possibly completed actions |

Use `scripts/gui-fixture.html` for a synthetic browser test. Its visible output
is the oracle. Do not inspect DOM, console, CDP, HTTP or files to grade its live
UI. Source inspection while developing the fixture is separate from a GUI run.
An isolated browser profile/window can be launched as test setup; operate the
test via GUI afterward. Loading the fixture alone does not pass navigation.

Unavailable Blender/WhatsApp cases are not-run, not replaced by mock canvas/chat
passes. Keep screenshots private and scoped; do not log text payloads by default.

Run helper regressions with `python3 -m unittest discover -s tests -v` from the
source project. Test snapshot freshness, focus/geometry, coordinate bounds,
protocol declarations, pre-mutation input rejection, and MCP errors that must not
trigger action replay. These checks do not certify other desktops/apps.
The source suite also exercises portable installation, preserved backups,
rollback and desktop detection with inherited session variables. Re-run the
visual reference task after a model/host change; simulated capability cases do
not constitute a multi-model benchmark.
