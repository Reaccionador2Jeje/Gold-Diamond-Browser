# Gold & Diamond Browser — Ecosystem Integration

Status: planning document for the desktop browser and future web-engine integration.

## Engine boundary
- Treat Qt WebEngine/Chromium as the current rendering engine unless the implementation changes.
- Do not describe Lapislazuli as powering the browser until a real integration is merged and tested.
- Keep private browsing claims limited to data the application actually avoids storing.
- Document download handling, profile storage and permissions.

## Next tasks
1. Add smoke tests for startup, navigation and tab lifecycle.
2. Document profile and private-tab storage behavior precisely.
3. Add tests for download path handling and URL parsing.
4. Track Lapislazuli integration as a separate milestone with measurable engine APIs.