"use client";

interface Props {
  value: string;
  onChange: (v: string) => void;
  scenarios?: { id: string; name: string }[];
}

const DEFAULT_SCENARIOS = [
  { id: "net_zero_2050", name: "Net Zero 2050" },
  { id: "below_2c", name: "Below 2°C" },
  { id: "delayed_transition", name: "Delayed Transition" },
  { id: "current_policies", name: "Current Policies" },
];

export default function ScenarioSelector({ value, onChange, scenarios }: Props) {
  const list = scenarios ?? DEFAULT_SCENARIOS;
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
    >
      {list.map((s) => (
        <option key={s.id} value={s.id}>
          {s.name}
        </option>
      ))}
    </select>
  );
}
