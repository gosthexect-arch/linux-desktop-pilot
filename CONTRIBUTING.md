# Contributing to Linux Desktop Pilot

Thank you for helping make visual Linux workflows more reliable. Code, desktop
validation reports, reproducible bug reports and documentation are welcome.
Contributions are accepted under the repository's MIT license.

## A useful first contribution

- Run the reference tasks on GNOME or KDE Plasma and report what actually happened.
- Reproduce a focus, scaling, input or recovery issue with synthetic data.
- Improve a small helper without changing the user's desktop configuration.
- Make installation easier to understand or translate documentation.

The [open issues](https://github.com/gosthexect-arch/linux-desktop-pilot/issues)
are a good starting point. For a substantial change, describe the problem and
proposed behavior in an issue before investing in a large implementation.

## Work locally

Fork the repository, clone your fork and create a branch. Run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/build_release.py
```

Helpers and regression tests use the Python standard library. CI runs on Linux
across the supported Python versions without controlling a real desktop.

## What to include in a pull request

Explain the trigger, the resulting behavior and how you verified it. Keep the
change focused. Add regression coverage when a transport or installation bug
would otherwise recur. Documentation-only changes do not need artificial tests.

Do not add hard-coded personal paths, credentials, private conversations,
screenshots of unrelated windows or downloaded runtime binaries. Keep optional
backends optional and preserve existing user configuration.

The skill ID `linux-visual-computer-use` stays stable for existing installations.
The public project name is Linux Desktop Pilot. Avoid changing the skill ID
without an explicit migration plan.

## Report desktop and model compatibility

Use the [desktop validation issue form](https://github.com/gosthexect-arch/linux-desktop-pilot/issues/new?template=desktop-validation.yml).
Include distribution, compositor/version, session type, runtime, relevant
monitor scales, application and model/host identity when known. Record unknown
values as unknown. Provide the task, expected result, observed result and route.

A unit test or doctor report is not an end-to-end desktop pass. A mock chat or
canvas is not proof that WhatsApp or Blender works. Test with synthetic/local
data where possible and share only relevant, redacted evidence. Sending a real
message or modifying a real project requires that user's task authorization.

Follow [the acceptance cases](linux-visual-computer-use/references/acceptance.md).
Clearly separate passed, failed, blocked and not-run results.

## Presentation and discoverability

The README should lead with a useful outcome, an honest compatibility statement,
simple installation and concrete examples. Keep evidence current. Do not add
invented user counts, endorsements, rankings or claims of universal compatibility.
The [presentation research](docs/presentation-research.md) records the sources
that informed the initial layout; those observations are not proof of causation.

For security concerns, use GitHub's private vulnerability reporting if available;
otherwise open an issue that describes the impact without exposing secrets or
an exploitable private installation. Communicate respectfully and keep feedback
specific to the proposed work.
