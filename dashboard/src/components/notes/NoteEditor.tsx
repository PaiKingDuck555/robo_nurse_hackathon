"use client";

interface NoteEditorProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

export default function NoteEditor({ value, onChange, disabled }: NoteEditorProps) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full h-full min-h-[200px] rounded-lg border border-gray-200 bg-white p-3 text-sm text-gray-800 font-mono leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
      placeholder="Click 'Generate Note' to create a doctor note from the intake data..."
    />
  );
}
