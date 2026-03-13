import React, { useState } from 'react';
import MoleculeViewer3D from './MoleculeViewer3D';
import { MilimoLogoIcon } from './Icons';

interface Test3DPageProps {
  onBack: () => void;
}

const Test3DPage: React.FC<Test3DPageProps> = ({ onBack }) => {
    const [smilesInput, setSmilesInput] = useState('CC(=O)Oc1ccccc1C(=O)O'); // Aspirin
    const [pdbInput, setPdbInput] = useState('6M0J');
    const [viewerProps, setViewerProps] = useState({ smiles: 'CC(=O)Oc1ccccc1C(=O)O', pdbId: '6M0J' });

    const handleRender = () => {
        setViewerProps({ smiles: smilesInput, pdbId: pdbInput });
    };
    
    const loadExample = (smiles: string, pdb: string) => {
        setSmilesInput(smiles);
        setPdbInput(pdb);
        setViewerProps({smiles, pdbId: pdb});
    }

    const examples = [
        { name: 'Aspirin (Ligand only)', smiles: 'CC(=O)Oc1ccccc1C(=O)O', pdb: '' },
        { name: 'Oseltamivir + Neuraminidase (COVID-19)', smiles: 'CCC(CC)O[C@H]1[C@H]([C@@H]([C@H](C=C1C(=O)OCC)N)NC(=O)C)N', pdb: '6M0J' },
        { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', pdb: ''},
        { name: 'Invalid SMILES', smiles: 'this is not a valid smiles', pdb: ''},
        { name: 'Valid SMILES, Invalid PDB', smiles: 'c1ccccc1', pdb: 'INVALID'},
    ]

    return (
        <div className="h-screen bg-neutral-950 text-neutral-200 font-sans flex flex-col items-center p-4">
            <div className="w-full max-w-6xl mx-auto flex flex-col h-full">
                <header className="flex items-center justify-between gap-3 mb-6 p-4 border-b border-neutral-800 flex-shrink-0">
                    <div className="flex items-center gap-3">
                         <MilimoLogoIcon className="w-10 h-10" />
                        <div>
                            <h1 className="text-xl font-bold text-neutral-50">3D Molecule Viewer Test Page</h1>
                            <p className="text-sm text-neutral-400">Isolated environment for testing the MoleculeViewer3D component.</p>
                        </div>
                    </div>
                     <button
                        onClick={onBack}
                        className="bg-neutral-800 hover:bg-neutral-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
                    >
                        &larr; Back to Main App
                    </button>
                </header>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-grow min-h-0">
                    <div className="md:col-span-1 bg-neutral-900 p-4 rounded-lg border border-neutral-800 flex flex-col">
                        <h2 className="text-lg font-semibold mb-4">Controls</h2>
                        
                        <div className="space-y-4">
                            <div>
                                <label htmlFor="smiles" className="block text-sm font-medium text-neutral-400 mb-1">SMILES String</label>
                                <textarea
                                    id="smiles"
                                    value={smilesInput}
                                    onChange={(e) => setSmilesInput(e.target.value)}
                                    placeholder="Enter SMILES string..."
                                    className="w-full bg-neutral-800 border border-neutral-700 rounded-md p-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                    rows={3}
                                />
                            </div>
                            <div>
                                <label htmlFor="pdb" className="block text-sm font-medium text-neutral-400 mb-1">PDB ID (optional)</label>
                                <input
                                    type="text"
                                    id="pdb"
                                    value={pdbInput}
                                    onChange={(e) => setPdbInput(e.target.value)}
                                    placeholder="Enter 4-character PDB ID..."
                                    className="w-full bg-neutral-800 border border-neutral-700 rounded-md p-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                />
                            </div>
                            <button
                                onClick={handleRender}
                                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
                            >
                                Render
                            </button>
                        </div>

                         <div className="mt-6">
                            <h3 className="text-base font-semibold mb-3">Quick Load Examples</h3>
                            <div className="space-y-2">
                                {examples.map(ex => (
                                    <button
                                        key={ex.name}
                                        onClick={() => loadExample(ex.smiles, ex.pdb)}
                                        className="w-full text-left p-2 bg-neutral-800/50 hover:bg-neutral-700/50 rounded-md text-sm text-blue-400 transition-colors"
                                    >
                                        {ex.name}
                                    </button>
                                ))}
                            </div>
                        </div>

                    </div>
                    
                    <div className="md:col-span-2 bg-neutral-900 p-4 rounded-lg border border-neutral-800 flex flex-col">
                         <h2 className="text-lg font-semibold mb-4 flex-shrink-0">Viewer Output</h2>
                         <div className="flex-grow w-full h-full relative min-h-0">
                             <MoleculeViewer3D
                                smiles={viewerProps.smiles}
                                pdbId={viewerProps.pdbId}
                            />
                         </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Test3DPage;