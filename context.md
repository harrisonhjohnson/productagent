# initiatives.md
# Single source of truth for initiatives, projects, and people.
# Agents read this file first. Keep it current.

people:
  - id: U001
    name: Harrison Johnson
    role: PM
  - id: U002
    name: Jane Smith
    role: Eng Lead
  - id: U003
    name: Alex Rivera
    role: iOS
  - id: U004
    name: Marcus Chen
    role: Data Engineer
  - id: U005
    name: Priya Patel
    role: Designer

initiatives:
  - id: I001
    goal: Launch Canada marketplace by Q3 2026
    window: 2026-Q2 → 2026-Q3
    projects:
      - id: P001
        name: Canada Checkout
        surfaces: [backend, ecom]
        channel: https://slack.com/...
        tracker: https://app.asana.com/...
        prd: https://...
        people: [U001, U002]

      - id: P002
        name: Canada iOS
        surfaces: [ios, ecom]
        channel: https://slack.com/...
        tracker: https://app.asana.com/...
        prd: https://...
        people: [U001, U003]

  - id: I002
    goal: Improve checkout conversion by 10% in Q3 2026
    window: 2026-Q3
    projects:
      - id: P003
        name: Checkout Funnel Instrumentation
        surfaces: [backend, data]
        channel: https://slack.com/...
        tracker: https://app.asana.com/...
        prd: https://...
        people: [U001, U002, U004]

      - id: P004
        name: Checkout Redesign
        surfaces: [ecom, ios, android]
        channel: https://slack.com/...
        tracker: https://app.asana.com/...
        prd: https://...
        people: [U001, U005]
