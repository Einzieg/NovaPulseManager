import React, { useEffect, useRef, useState } from 'react';
import { X, Edit3 } from 'lucide-react';
import { clsx } from 'clsx';

interface PromptModalProps {
  isOpen: boolean;
  title: string;
  description?: string;
  defaultValue?: string;
  placeholder?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: (value: string) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export default function PromptModal({
  isOpen,
  title,
  description,
  defaultValue = '',
  placeholder = '',
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isLoading = false,
}: PromptModalProps) {
  const [value, setValue] = useState(defaultValue);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset value when opening
  useEffect(() => {
    if (isOpen) {
      setValue(defaultValue);
      // Focus input after animation
      const t = setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
      return () => clearTimeout(t);
    }
  }, [isOpen, defaultValue]);

  // Handle ESC and Enter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen || isLoading) return;
      
      if (e.key === 'Escape') {
        onCancel();
      } else if (e.key === 'Enter' && value.trim()) {
        onConfirm(value.trim());
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isLoading, value, onConfirm, onCancel]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/20 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div 
        className="w-full max-w-sm overflow-hidden rounded-[32px] border border-white/60 bg-ios-surface/90 shadow-2xl backdrop-blur-xl animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        <div className="p-6">
          {/* Header */}
          <div className="mb-6 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-ios-accent text-ios-on-accent shadow-lg">
              <Edit3 size={20} />
            </div>
            <h3 className="mb-2 text-lg font-[800] italic tracking-tight text-ios-black uppercase">
              {title}
            </h3>
            {description && (
              <p className="text-xs font-medium text-ios-gray leading-relaxed">
                {description}
              </p>
            )}
          </div>

          {/* Input */}
          <div className="mb-2">
            <input
              ref={inputRef}
              type="text"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={placeholder}
              disabled={isLoading}
              className="w-full rounded-2xl border border-black/5 bg-ios-surface/50 px-4 py-3 font-bold text-ios-black placeholder:text-black/20 focus:border-ios-black/20 focus:bg-ios-surface focus:outline-none focus:ring-0 transition-all text-center"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-px bg-black/5 border-t border-black/5">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="bg-ios-surface/50 p-4 text-[10px] font-black uppercase tracking-widest text-ios-gray hover:bg-ios-surface hover:text-ios-black transition-colors disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            onClick={() => value.trim() && onConfirm(value.trim())}
            disabled={isLoading || !value.trim()}
            className="bg-ios-accent p-4 text-[10px] font-black uppercase tracking-widest text-ios-on-accent hover:opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
