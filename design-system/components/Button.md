# Button

Compact 8px-radius button for every action in SmartCash and on sprint slides.

- `primary` (lavender `primary`): ONE per view, the main action ("Start sprint", "Add expense"). Hover `primary-hover`, pressed `primary-focus`.
- `secondary` (`surface-1` + `hairline` border): the other actions.
- `tertiary`: text-only, for Cancel / low emphasis.
- `inverse` (white on dark): rare, a single section-opening CTA.
- Never pill-round a button; corners are always `radius-md`. Min height 36px (44px on touch).
- Focus: 2px `primary-focus` ring. The consumer provides the label and `onClick`.
