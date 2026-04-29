import React, { useEffect } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { clsx } from 'clsx';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm: () => void;
  onCancel: () => void;
  isLoading?: boolean;
  isDanger?: boolean;
}

export default function ConfirmModal({
  isOpen,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  isLoading = false,
  isDanger = false,
}: ConfirmModalProps) {
  // Handle ESC key
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (isOpen && e.key === 'Escape' && !isLoading) {
        onCancel();
      }
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isOpen, isLoading, onCancel]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/20 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div 
        className="w-full max-w-sm overflow-hidden rounded-[32px] border border-white/60 bg-ios-surface/90 shadow-2xl backdrop-blur-xl animate-in zoom-in-95 duration-200"
        role="dialog"
        aria-modal="true"
      >
        <div className="p-6 text-center">
          {/* Icon */}
          <div className={clsx(
            "mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl shadow-lg",
            isDanger ? "bg-rose-100 text-rose-500" : "bg-gray-100 text-gray-500"
          )}>
            <AlertCircle size={24} />
          </div>

          {/* Content */}
          <h3 className="mb-2 text-lg font-[800] italic tracking-tight text-ios-black uppercase">
            {title}
          </h3>
          {description && (
            <p className="text-xs font-medium text-ios-gray leading-relaxed px-4">
              {description}
            </p>
          )}
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
            onClick={onConfirm}
            disabled={isLoading}
            className={clsx(
              "p-4 text-[10px] font-black uppercase tracking-widest transition-colors disabled:opacity-50",
              isDanger 
                ? "bg-rose-50 text-rose-500 hover:bg-rose-100" 
                : "bg-ios-accent text-ios-on-accent hover:opacity-90"
            )}
          >
            {isLoading ? 'Processing...' : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
