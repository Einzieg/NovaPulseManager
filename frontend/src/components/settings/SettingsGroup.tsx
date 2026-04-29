import React from 'react';

interface SettingsGroupProps {
  title: string;
  children: React.ReactNode;
}

const SettingsGroup = ({ title, children }: SettingsGroupProps) => (
  <div className="rounded-2xl border border-white/60 bg-ios-surface/50 p-5 backdrop-blur-md">
    <h3 className="mb-4 text-[10px] font-black uppercase tracking-[0.2em] text-ios-gray">
      {title}
    </h3>
    <div className="space-y-4">{children}</div>
  </div>
);

export default SettingsGroup;
