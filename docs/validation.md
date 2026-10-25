# Validation record

Observed on **October 25, 2026**. The maintainer currently has access to Hyprland
only. This is an early release with real evidence for one desktop configuration.

## Real GUI run

Environment: Omarchy 4.0.6, Hyprland 0.56.2, Wayland, Chromium in an isolated
temporary profile. Two monitors were present, both at scale 1; input tests ran
on the first monitor, so the second monitor is not considered validated.

The agent operated a local synthetic page through screenshots, mouse and
keyboard. It did not query the live DOM, use CDP, read internal page state or
call an application API to complete or grade these tasks.

| Observed case | Result |
| --- | --- |
| Window capture and field click | Passed; target field visibly focused |
| Accented text | Passed; `João — criação e operações` read back visually |
| Tab navigation and selection | Passed; selected team changed to Criação |
| Save local form | Passed; visible confirmation matched name and team |
| Follow section link | Passed; gesture section became visible |
| Middle-button + Shift drag | Passed; block moved and visible feedback identified button/modifier |
| Horizontal and vertical scroll | Passed; page reported horizontal 360 and vertical 152 |
| Close window with shortcut | Passed; isolated test window disappeared |
| Focus-change rejection | Passed; input was refused before typing in another window |

The existing Open Computer Use 1.1.2 integration did not discover the app windows
in this session. The direct Hyprland fallback was used instead. The optional
computer-use-linux 0.7.25 backend completed MCP initialization, catalog and window
discovery; its full capture/input route was not accepted from those checks alone.

No user conversations or existing creative projects were changed during the test.
Private local logs/captures are excluded from the repository and release assets.

## Automated engineering checks

**35 regression tests passed**, including:

- Snapshot age, focus, PID, geometry, workspace and image integrity checks.
- Coordinate bounds and negative output origins.
- MCP stdio initialization and errors without automatic action replay.
- Installation into relocated directories containing spaces and Unicode.
- Repeat install, update backup, failure rollback and unrelated-directory refusal.
- Desktop detection with an inherited Hyprland variable and bounded protocol probes.

The full suite also passed from an extracted distribution ZIP. These are
engineering checks, not additional real desktop or model acceptance runs.

## Pending real acceptance

GNOME/Wayland, KDE Plasma/Wayland, live WhatsApp, existing Blender projects,
additional models/hosts, fractional scaling, negative-origin monitor layouts,
the second monitor and the remaining pointer/navigation cases require actual
execution. The transport exposes more actions than this initial run covered.

Use [CONTRIBUTING.md](../CONTRIBUTING.md) and the validation issue form to add
your results. Record the precise tested combination instead of generalizing to
every Linux installation or every model.
