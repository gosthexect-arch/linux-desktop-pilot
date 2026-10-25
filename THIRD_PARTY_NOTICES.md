# Third-party notices

Linux Desktop Pilot's original code, instructions and illustrations are licensed
under MIT. External projects keep their own licenses and are not re-licensed by
this repository. No upstream runtime binaries are included in source or releases.

- [Open Computer Use](https://github.com/iFurySt/open-computer-use): optional
  existing MCP integration, referenced rather than bundled.
- [computer-use-linux](https://github.com/agent-sh/computer-use-linux): optional
  Linux MCP runtime. The installer pins npm package version 0.7.25; installing it
  downloads upstream binaries with their own license notices.
- [wtype](https://github.com/atx/wtype),
  [grim](https://gitlab.freedesktop.org/emersion/grim),
  [Hyprland](https://github.com/hyprwm/Hyprland), Wayland and libxkbcommon are
  system dependencies, not vendored source.
- The transport's wire declarations follow the public
  [virtual pointer protocol](https://github.com/swaywm/wlr-protocols/blob/master/unstable/wlr-virtual-pointer-unstable-v1.xml)
  and [virtual keyboard protocol](https://github.com/atx/wtype/blob/master/protocol/virtual-keyboard-unstable-v1.xml).
- [skills](https://github.com/vercel-labs/skills) is an optional external
  installation CLI. Its telemetry and requirements are separate from this
  project's helpers, which do not implement install-count telemetry.

The repository presentation was independently written after reviewing public
skill directories and READMEs. No upstream branding, artwork or skill
implementation was copied. See the [presentation research](docs/presentation-research.md).
