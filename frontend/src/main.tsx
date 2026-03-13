import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

import { WorkspaceProvider } from './contexts/WorkspaceContext'
import { registerCorePlugins } from './extensions/core-plugins'
import { registerMQDDExtension } from './extensions/mqdd'
import { registerAutoresearchExtension } from './extensions/autoresearch'

import { ProjectProvider } from './contexts/ProjectContext'

// Register base extensions immediately
registerCorePlugins()
registerMQDDExtension()
registerAutoresearchExtension()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <WorkspaceProvider>
      <ProjectProvider>
        <App />
      </ProjectProvider>
    </WorkspaceProvider>
  </StrictMode>,
)
