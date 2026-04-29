import React from 'react';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { clsx } from 'clsx';

interface ThemeSegmentedControlProps {
  darkMode: boolean;
  onChange: (dark: boolean) => void;
}

const SEGMENTS = [
  { key: false, label: '浅色', icon: Sun },
  { key: true, label: '深色', icon: Moon },
] as const;

const ThemeSegmentedControl = ({ darkMode, onChange }: ThemeSegmentedControlProps) => (
  <div className="flex items-center justify-between">
    <span className="text-sm font-bold text-ios-black">主题</span>
    <div className="relative flex rounded-xl border border-black/5 bg-gray-100/60 p-1">
      {SEGMENTS.map(({ key, label, icon: Icon }) => (
        <button
          key={String(key)}
          onClick={() => onChange(key)}
          className={clsx(
            'relative z-10 flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-bold transition-colors',
            darkMode === key ? 'text-ios-on-accent' : 'text-ios-gray hover:text-ios-black',
          )}
        >
          <Icon size={14} />
          {label}
          {darkMode === key && (
            <motion.div
              layoutId="theme-indicator"
              className="absolute inset-0 rounded-lg bg-ios-accent shadow-md"
              style={{ zIndex: -1 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
        </button>
      ))}
    </div>
  </div>
);

export default ThemeSegmentedControl;
