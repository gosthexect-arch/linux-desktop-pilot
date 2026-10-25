# Transferable GUI workflows

## Browser

Find the requested window, inspect a screenshot, identify the active tab/dialogs
and navigate with the address bar, tabs, rendered links and controls. Page
search, accessibility and keyboard traversal are valid. Do not use Codex web
search, DOM queries, HTTP or a debugging endpoint to complete or verify an
interface-only task. Use screenshots to understand visual organization.

Test navigation, form correction, accents, scrolling, context menus, file dialogs
and tab changes on synthetic data. Do not expand into unrelated history/accounts.

## WhatsApp and communication software

Use the actual client or visible authenticated web app. Verify contact/group
identity before composing; display names can be ambiguous. Read only relevant
messages and scope captures to the task. Do not extract sessions or inject code.

Drafting and sending are distinct. Tests default to a synthetic local draft or a
specifically designated conversation. An authorized send requires verification
of recipient, exact message and attachments, followed by inspection of the sent
UI state. A general app test never authorizes sending to a real contact.

Account for Enter versus Shift+Enter in multiline drafts. If delivery is
uncertain, inspect the conversation before retrying to prevent duplicates.
Follow existing explicit human authorization without redundant approvals.

## Blender and creative applications

Use the already-open project when that is the user's request. Identify the
project, selected object, active editor, mode and unsaved state. Preserve work
with a copy when appropriate. Do not clear an existing scene to follow a tutorial.

Default and Industry Compatible keymaps differ. Observe the actual keymap/version
when a shortcut behaves differently. Use menus, operator search and visible
property fields as alternate routes. The pointer's editor region affects keys.

Checkpoint selection, geometry changes, another view angle, material changes,
Save As and reopening a test copy. Viewport pixels matter: a renamed Outliner
entry does not establish correct geometry. Test middle-button orbit, modifier
pan, zoom, selection, numeric transforms and modal accept/cancel. Use visible
navigation controls if a gesture is unavailable. Python, CLI scripts, RPC and
generated meshes cannot substitute for the interface-only workflow.

## Other applications

Infer structure from screenshots, roles, tooltips, menus and visible help.
Identify one small step with an observable result. Standard controls often use
accessibility; custom surfaces need pixels/gestures. This applies to office tools,
file managers, ERP/CRM, design tools and remote GUI sessions. Remote desktops add
an inner focus/coordinate boundary: establish control inside that viewport.
Ask only for genuinely missing destination/intent information while continuing
independent work. Examples are not an application whitelist.
