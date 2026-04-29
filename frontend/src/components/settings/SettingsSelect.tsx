import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { clsx } from 'clsx';

interface SettingsSelectProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}

const SettingsSelect = ({ label, value, options, onChange }: SettingsSelectProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [pos, setPos] = useState({ top: 0, right: 0 });
  const buttonRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const updatePos = useCallback(() => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();
    setPos({ top: rect.bottom + 6, right: window.innerWidth - rect.right });
  }, []);

  const toggle = useCallback(() => {
    if (!isOpen) updatePos();
    setIsOpen((v) => !v);
  }, [isOpen, updatePos]);

  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (
        buttonRef.current?.contains(target) ||
        dropdownRef.current?.contains(target)
      ) return;
      setIsOpen(false);
    };
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsOpen(false);
    };
    const handleScroll = () => setIsOpen(false);
    const scrollParent = buttonRef.current?.closest('.custom-scrollbar');

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    scrollParent?.addEventListener('scroll', handleScroll);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
      scrollParent?.removeEventListener('scroll', handleScroll);
    };
  }, [isOpen]);

  const dropdown = (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={dropdownRef}
          initial={{ opacity: 0, y: 4, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 4, scale: 0.95 }}
          transition={{ duration: 0.15 }}
          style={{ position: 'fixed', top: pos.top, right: pos.right, zIndex: 9999 }}
          className="min-w-[140px] overflow-hidden rounded-xl border border-white/60 bg-ios-surface/90 p-1 shadow-deep backdrop-blur-xl"
        >
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => { onChange(opt); setIsOpen(false); }}
              className={clsx(
                'flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors',
                value === opt ? 'font-bold text-ios-blue' : 'font-medium text-ios-black hover:bg-ios-black/5',
              )}
            >
              {opt}
              {value === opt && <Check size={14} />}
            </button>
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );

  return (
    <div className="flex items-center justify-between">
      <span className="text-sm font-bold text-ios-black">{label}</span>
      <div>
        <button
          ref={buttonRef}
          onClick={toggle}
          aria-haspopup="listbox"
          aria-expanded={isOpen}
          className="flex min-w-[120px] items-center justify-between gap-2 rounded-xl border border-white/60 bg-ios-surface/50 px-3 py-2 text-sm font-bold text-ios-black shadow-sm backdrop-blur-md transition-colors hover:bg-ios-surface/70"
        >
          {value}
          <ChevronDown size={14} className={clsx('text-ios-gray transition-transform', isOpen && 'rotate-180')} />
        </button>
        {createPortal(dropdown, document.body)}
      </div>
    </div>
  );
};

export default SettingsSelect;
