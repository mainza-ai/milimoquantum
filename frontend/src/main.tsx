import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import { WorkspaceProvider } from './contexts/WorkspaceContext'
import { ProjectProvider } from './contexts/ProjectContext'

// Extension registrations
import { registerCorePlugins } from './extensions/core-plugins'
import { registerMQDDExtension } from './extensions/mqdd'
import { registerAutoresearchExtension } from './extensions/autoresearch'
import { registerHPCExtension } from './extensions/hpc'
import { registerWorkflowExtension } from './extensions/workflow'
import { registerAuditExtension } from './extensions/audit'
import { registerGraphExtension } from './extensions/graph'

// Register all extensions
registerCorePlugins()
registerMQDDExtension()
registerAutoresearchExtension()
registerHPCExtension()
registerWorkflowExtension()
registerAuditExtension()
registerGraphExtension()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WorkspaceProvider>
      <ProjectProvider>
        <App />
      </ProjectProvider>
    </WorkspaceProvider>
  </StrictMode>,
)
