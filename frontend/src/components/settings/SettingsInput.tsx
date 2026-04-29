import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface SettingsInputProps {
  label: string;
  value: string;
  type?: 'text' | 'password';
  placeholder?: string;
  onChange: (value: string) => void;
}

const SettingsInput = ({ label, value, type = 'text', placeholder, onChange }: SettingsInputProps) => {
  const [visible, setVisible] = useState(false);
  const isPassword = type === 'password';

  return (
    <div className="space-y-1.5">
      <span className="text-sm font-bold text-ios-black">{label}</span>
      <div className="relative">
        <input
          type={isPassword && !visible ? 'password' : 'text'}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-xl border border-black/5 bg-ios-surface/60 px-3 py-2 pr-10 text-sm font-medium text-ios-black shadow-sm outline-none backdrop-blur-md transition-colors placeholder:text-ios-gray/40 hover:bg-ios-surface/80 focus:ring-2 focus:ring-ios-black/10"
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setVisible((v) => !v)}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-ios-gray/60 transition-colors hover:text-ios-black"
          >
            {visible ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}
      </div>
    </div>
  );
};

export default SettingsInput;
