import { extensionRegistry } from './registry';
import SettingsPanel from '../components/layout/SettingsPanel';
import { AnalyticsDashboard } from '../components/layout/AnalyticsDashboard';
import { SearchPanel } from '../components/layout/SearchPanel';
import { MarketplacePanel } from '../components/layout/MarketplacePanel';
import { ProjectsPanel } from '../components/layout/ProjectsPanel';
import { QuantumDashboard } from '../components/layout/QuantumDashboard';
import { LearningAcademy } from '../components/layout/LearningAcademy';

export function registerCorePlugins() {
    extensionRegistry.register({
        id: 'search',
        name: 'Search',
        description: 'Global Search',
        icon: '🔍',
        component: SearchPanel,
        category: 'tool'
    });

    extensionRegistry.register({
        id: 'analytics',
        name: 'Analytics',
        description: 'Global Analytics Dashboard',
        icon: '📊',
        component: AnalyticsDashboard,
        category: 'tool'
    });

    extensionRegistry.register({
        id: 'projects',
        name: 'Projects',
        description: 'Saved Projects & Conversations',
        icon: '📁',
        component: ProjectsPanel,
        category: 'tool'
    });

    extensionRegistry.register({
        id: 'dashboard',
        name: 'Dashboard',
        description: 'Quantum Hardware Dashboard',
        icon: '⚛️',
        component: QuantumDashboard,
        category: 'tool'
    });

    extensionRegistry.register({
        id: 'academy',
        name: 'Academy',
        description: 'Learning Academy',
        icon: '🎓',
        component: LearningAcademy,
        category: 'tool'
    });

    extensionRegistry.register({
        id: 'marketplace',
        name: 'Marketplace',
        description: 'Algorithms & Extensions',
        icon: '🏪',
        component: MarketplacePanel,
        category: 'tool'
    });
    
    extensionRegistry.register({
        id: 'settings',
        name: 'Settings',
        description: 'System Settings',
        icon: '⚙️',
        component: SettingsPanel,
        category: 'tool'
    });
}
