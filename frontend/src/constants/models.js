// Must mirror the MODULES tuple in backend/api/routes/models.py exactly.

export const MODULES = [
  { value: "visual", label: "Visual" },
  { value: "audio_energy", label: "Audio Energy" },
  { value: "commentary", label: "Commentary" },
]

export const MODULE_LABELS = Object.fromEntries(
  MODULES.map((m) => [m.value, m.label])
)
