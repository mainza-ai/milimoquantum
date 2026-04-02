/* Milimo Quantum — Module Drawer (Expandable) */
import { useState, useEffect, useRef } from 'react';
import { extensionRegistry, type Extension } from '../../extensions/registry';
import { useWorkspace } from '../../contexts/WorkspaceContext';

interface ModuleDrawerProps {
    isExpanded: boolean;
}

interface ExtensionCategory {
    label: string;
    extensions: Extension[];
}

export function ModuleDrawer({ isExpanded }: ModuleDrawerProps) {
    const { activeExtensions, openExtension } = useWorkspace();
    const drawerRef = useRef<HTMLDivElement>(null);
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        if (!isExpanded) return;

        function handleClick(e: MouseEvent) {
            if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
                // Don't close if clicking the toggle button
                const toggleBtn = document.getElementById('module-drawer-toggle');
                if (toggleBtn && toggleBtn.contains(e.target as Node)) return;
            }
        }

        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, [isExpanded]);

    const allExtensions = extensionRegistry.getAll();

    const categories: ExtensionCategory[] = [
        {
            label: 'Tools',
            extensions: allExtensions.filter(e => e.category === 'tool'),
        },
        {
            label: 'Science',
            extensions: allExtensions.filter(e => e.category === 'science'),
        },
        {
            label: 'Industry',
            extensions: allExtensions.filter(e => e.category === 'industry'),
        },
        {
            label: 'Advanced',
            extensions: allExtensions.filter(e => e.category === 'advanced'),
        },
    ].filter(cat => cat.extensions.length > 0);

    const filteredCategories = searchQuery
        ? categories.map(cat => ({
            ...cat,
            extensions: cat.extensions.filter(e =>
                e.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                e.description.toLowerCase().includes(searchQuery.toLowerCase())
            ),
        })).filter(cat => cat.extensions.length > 0)
        : categories;

    return (
        <div
            ref={drawerRef}
            className={`
                absolute bottom-full left-0 right-0 z-50
                bg-[#12121a] border border-white/[0.08] rounded-t-xl
                shadow-[0_-8px_32px_rgba(0,0,0,0.5)]
                transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]
                ${isExpanded ? 'max-h-[320px] opacity-100 translate-y-0' : 'max-h-0 opacity-0 translate-y-2 pointer-events-none'}
            `}
        >
            {/* Search bar */}
            <div className="px-4 pt-3 pb-2 border-b border-white/[0.04]">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search modules..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full py-2 px-3 pl-8 rounded-lg
                            bg-white/[0.04] border border-white/[0.06]
                            text-[12px] text-[#e8e8ed] placeholder-[#505060]
                            focus:outline-none focus:border-[#3ecfef]/30
                            transition-all duration-200"
                    />
                    <svg
                        className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#505060]"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                    </svg>
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-[#505060] hover:text-[#8a8a9a]"
                        >
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    )}
                </div>
            </div>

            {/* Categories scrollable */}
            <div className="overflow-y-auto max-h-[240px] px-3 py-2">
                {filteredCategories.length === 0 ? (
                    <div className="py-6 text-center">
                        <p className="text-[12px] text-[#505060]">No modules found</p>
                    </div>
                ) : (
                    filteredCategories.map((category) => (
                        <div key={category.label} className="mb-3 last:mb-0">
                            <div className="px-2 py-1 text-[9px] text-[#505060] uppercase tracking-[0.12em] font-semibold">
                                {category.label}
                            </div>
                            <div className="grid grid-cols-4 gap-1.5">
                                {category.extensions.map((ext) => {
                                    const isActive = activeExtensions.some(e => e.extensionId === ext.id && e.isOpen);
                                    return (
                                        <ModuleButton
                                            key={ext.id}
                                            extension={ext}
                                            isActive={isActive}
                                            onClick={() => openExtension(ext.id)}
                                        />
                                    );
                                })}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

interface ModuleButtonProps {
    extension: Extension;
    isActive: boolean;
    onClick: () => void;
}

function ModuleButton({ extension, isActive, onClick }: ModuleButtonProps) {
    return (
        <button
            onClick={onClick}
            title={extension.description}
            className={`
                flex flex-col items-center justify-center gap-1 py-2.5 px-2 rounded-lg
                transition-all duration-150 cursor-pointer
                ${isActive
                    ? 'bg-[#3ecfef]/10 border border-[#3ecfef]/30'
                    : 'bg-white/[0.02] border border-transparent hover:bg-white/[0.04] hover:border-white/[0.06]'
                }
            `}
        >
            <span className="text-[18px] leading-none">{extension.icon}</span>
            <span className={`
                text-[10px] font-medium leading-tight text-center truncate w-full
                ${isActive ? 'text-[#3ecfef]' : 'text-[#8a8a9a]'}
            `}>
                {extension.name}
            </span>
        </button>
    );
}

export function ModuleDrawerToggle({ isExpanded, onClick }: { isExpanded: boolean; onClick: () => void }) {
    return (
        <button
            id="module-drawer-toggle"
            onClick={onClick}
            title={isExpanded ? 'Collapse modules' : 'Expand modules'}
            className={`
                w-full py-2 px-3 rounded-lg text-[11px]
                flex items-center justify-center gap-1.5
                transition-all duration-150 cursor-pointer
                ${isExpanded
                    ? 'bg-[#3ecfef]/10 text-[#3ecfef] border border-[#3ecfef]/20'
                    : 'text-[#636370] hover:text-[#8a8a9a] hover:bg-white/[0.04]'
                }
            `}
        >
            <svg
                className={`w-3.5 h-3.5 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
            >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
            </svg>
            <span>{isExpanded ? 'Hide Modules' : 'Modules'}</span>
        </button>
    );
}
