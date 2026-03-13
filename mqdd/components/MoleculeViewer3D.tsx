
import React, { useRef, useEffect, useState } from 'react';
import { LoaderIcon } from './Icons';
import { Interaction } from '../types';

declare const $3Dmol: any;

type ProteinStyle = 'cartoon' | 'surface';
type InteractionType = Interaction['type'];

interface MoleculeViewer3DProps {
  smiles: string;
  pdbId?: string;
  interactions?: Interaction[];
  className?: string;
}

const SpinIcon: React.FC<{isSpinning: boolean, className?: string}> = ({ isSpinning, className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        {isSpinning ? (
            <>
                <path d="M6 9v6" />
                <path d="M10 9v6" />
            </>
        ) : (
            <path d="M5 3l14 9-14 9V3z" />
        )}
    </svg>
);


const MoleculeViewer3D: React.FC<MoleculeViewer3DProps> = ({ smiles, pdbId, interactions, className }) => {
  const viewerRef = useRef<HTMLDivElement>(null);
  const viewerInstanceRef = useRef<any>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [loadingMessage, setLoadingMessage] = useState('Initializing...');
  const [error, setError] = useState<string | null>(null);
  const [proteinStyle, setProteinStyle] = useState<ProteinStyle>('cartoon');
  const [isSpinning, setIsSpinning] = useState(false);
  const [visibleInteractions, setVisibleInteractions] = useState<Record<InteractionType, boolean>>({
    HydrogenBond: true,
    Hydrophobic: true,
    PiStacking: true,
  });

  const hasPdbId = typeof pdbId === 'string' && pdbId.trim().length > 0 && pdbId.trim().toLowerCase() !== 'null';
  const hasInteractions = hasPdbId && interactions && interactions.length > 0;

  // Effect 1: Initialize the viewer instance and set up ResizeObserver.
  useEffect(() => {
    const viewerElement = viewerRef.current;
    let resizeObserver: ResizeObserver | null = null;

    if (viewerElement && !viewerInstanceRef.current) {
        viewerInstanceRef.current = $3Dmol.createViewer(viewerElement, {
            backgroundColor: '#262626',
            backgroundAlpha: 1,
            camera: { fov: 45 }
        });
        
        resizeObserver = new ResizeObserver(() => {
            if (viewerInstanceRef.current) {
                viewerInstanceRef.current.resize();
            }
        });
        resizeObserver.observe(viewerElement);
    }

    return () => {
      if (resizeObserver && viewerElement) {
        resizeObserver.unobserve(viewerElement);
      }
      if (viewerInstanceRef.current) {
        viewerInstanceRef.current = null;
      }
    };
  }, []); // Empty dependency array ensures this runs only on mount and unmount.


  // Effect 2: Load models and interactions whenever the inputs change.
  useEffect(() => {
    let isMounted = true;
    const viewer = viewerInstanceRef.current;

    const loadModels = async () => {
      if (!viewer) return;

      setIsLoading(true);
      setError(null);
      setLoadingMessage('Initializing...');
      
      if(isSpinning) viewer.spin(false);
      setIsSpinning(false);
      
      viewer.removeAllModels();
      viewer.removeAllShapes();
      viewer.removeAllLabels();
      
      if (!smiles || smiles.trim() === '') {
        setError("Input SMILES string is empty.");
        setIsLoading(false);
        return;
      }

      try {
        let ligandModel;
        try {
          if (!isMounted) return;
          setLoadingMessage('Generating 3D ligand...');
          const sdfResponse = await fetch(`https://cactus.nci.nih.gov/chemical/structure/${encodeURIComponent(smiles)}/file?format=sdf&get3d=true`);
          if (!sdfResponse.ok) {
            throw new Error(`NCI CACTUS API failed (status: ${sdfResponse.status}). The SMILES string may be malformed or the service is down.`);
          }
          const sdfData = await sdfResponse.text();

          if (!isMounted) return;
          if (!sdfData || !sdfData.includes('M  END') || sdfData.includes('<h1>Not Found</h1>')) {
            throw new Error("Could not resolve SMILES to a valid 3D structure (SDF). Please check the SMILES string.");
          }
          ligandModel = viewer.addModel(sdfData, 'sdf');
          viewer.setStyle({ model: ligandModel }, { stick: { radius: 0.1, colorscheme: 'Jmol' }, sphere: { scale: 0.25, colorscheme: 'Jmol' } });
        } catch (ligandError) {
            const message = ligandError instanceof Error ? ligandError.message : "An unknown error occurred.";
            throw new Error(`Failed to load ligand: ${message}`);
        }
        
        if (hasPdbId) {
          try {
            if (!isMounted) return;
            setLoadingMessage(`Fetching protein ${pdbId}...`);
            const proteinResponse = await fetch(`https://files.rcsb.org/download/${pdbId}.pdb`);
             if (!proteinResponse.ok) {
                throw new Error(`Could not fetch PDB ID '${pdbId}' from rcsb.org (status: ${proteinResponse.status}). Please verify the ID is correct.`);
            }
            const proteinData = await proteinResponse.text();
            if (!isMounted) return;
             if (!proteinData || !proteinData.startsWith('HEADER')) {
                throw new Error(`The data received for PDB ID '${pdbId}' does not appear to be a valid PDB file.`);
            }

            if (!isMounted) return;
            setLoadingMessage(`Rendering protein ${pdbId}...`);
            const proteinModel = viewer.addModel(proteinData, 'pdb');
            const proteinSelection = { model: proteinModel };
            const bindingSiteInProtein = { and: [proteinSelection, { within: { distance: 5, sel: { model: ligandModel } }}] };
            
            if (proteinStyle === 'cartoon') {
                viewer.setStyle(proteinSelection, { cartoon: { colorscheme: 'ssPyMOL', opacity: 0.8 } });
                viewer.addStyle(bindingSiteInProtein, { stick: { colorscheme: "cyanCarbon", radius: 0.15 } });
            } else { // Surface
                viewer.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.85, colorscheme: 'whiteCarbon' }, proteinSelection);
                viewer.addStyle(bindingSiteInProtein, { stick: { colorscheme: "cyanCarbon", radius: 0.15 }});
            }

            if (interactions && interactions.length > 0) {
                 if (!isMounted) return;
                 setLoadingMessage('Rendering interactions...');
                 const interactionColors: Record<InteractionType, string> = {
                    HydrogenBond: '#38bdf8', // light blue
                    Hydrophobic: '#fbbf24', // amber
                    PiStacking: '#a78bfa', // violet
                 };
                 interactions.forEach(interaction => {
                    if (visibleInteractions[interaction.type]) {
                        const proteinAtoms = { model: proteinModel, index: interaction.proteinAtoms };
                        const ligandAtoms = { model: ligandModel, index: interaction.ligandAtoms };

                        // Add dashed line for interaction
                        const pAtom = viewer.selectedAtoms(proteinAtoms)[0];
                        const lAtom = viewer.selectedAtoms(ligandAtoms)[0];
                        if (pAtom && lAtom) {
                            viewer.addShape({
                                line: {
                                    start: { x: pAtom.x, y: pAtom.y, z: pAtom.z },
                                    end: { x: lAtom.x, y: lAtom.y, z: lAtom.z },
                                    color: interactionColors[interaction.type],
                                    dashed: true,
                                    dashLength: 0.2,
                                    gapLength: 0.2,
                                }
                            });
                        }
                        
                        // Add residue label
                        viewer.addResLabels({and: [proteinAtoms, {bonds: 0}]}, {
                            font: 'Arial',
                            fontSize: 10,
                            fontColor: '#e5e5e5',
                            backgroundColor: '#171717',
                            backgroundOpacity: 0.7,
                        });
                    }
                 });
            }

          } catch (proteinError) {
              const message = proteinError instanceof Error ? proteinError.message : "An unknown error occurred.";
              throw new Error(`Failed to load protein: ${message}`);
          }
        }
        
        if (!isMounted) return;
        setLoadingMessage('Finalizing view...');
        viewer.zoomTo();
        viewer.render();
        setIsLoading(false);

      } catch (err) {
        if (isMounted) {
          const errorMessage = err instanceof Error ? err.message : "An unknown error occurred during 3D model loading.";
          setError(errorMessage);
          setIsLoading(false);
        }
      }
    };

    loadModels();

    return () => {
      isMounted = false;
    };
  }, [smiles, pdbId, interactions, proteinStyle, hasPdbId, visibleInteractions]);
  
  // Effect 3: Synchronize the spin state with the viewer instance.
  useEffect(() => {
    const viewer = viewerInstanceRef.current;
    if (viewer && !isLoading && !error) {
        viewer.spin(isSpinning, { speed: 0.5 });
    }
  }, [isSpinning, isLoading, error]);

  const toggleSpin = () => {
      if(!isLoading && !error) {
          setIsSpinning(prev => !prev);
      }
  }

  const toggleInteractionVisibility = (type: InteractionType) => {
    setVisibleInteractions(prev => ({...prev, [type]: !prev[type]}));
  };

  const ProteinStyleButton: React.FC<{style: ProteinStyle, label: string}> = ({style, label}) => (
    <button
        onClick={() => setProteinStyle(style)}
        disabled={isLoading}
        className={`px-2 py-1 text-xs font-medium rounded ${proteinStyle === style ? 'bg-blue-600 text-white' : 'bg-neutral-600 hover:bg-neutral-500'} transition-colors disabled:opacity-50`}
    >
        {label}
    </button>
  );

  return (
    <div className={`relative w-full h-full min-h-64 rounded-md bg-neutral-800/50 ${className}`}>
        <div ref={viewerRef} className="w-full h-full" />
        <div className="absolute top-2 right-2 flex gap-1.5 z-10">
            {hasPdbId && (
                <>
                    <ProteinStyleButton style="cartoon" label="Cartoon" />
                    <ProteinStyleButton style="surface" label="Surface" />
                </>
            )}
            <button
                onClick={toggleSpin}
                disabled={isLoading || !!error}
                className="p-1.5 rounded bg-neutral-600 hover:bg-neutral-500 disabled:opacity-50"
                aria-label={isSpinning ? 'Pause rotation' : 'Start rotation'}
            >
                <SpinIcon isSpinning={isSpinning} className="w-3.5 h-3.5 text-white" />
            </button>
        </div>
         {hasInteractions && (
            <div className="absolute bottom-2 left-2 flex gap-2 z-10 bg-neutral-900/50 p-1.5 rounded-md">
                {(Object.keys(visibleInteractions) as InteractionType[]).map(type => (
                    <button key={type} onClick={() => toggleInteractionVisibility(type)} className={`px-2 py-1 text-xs rounded-md transition-colors ${visibleInteractions[type] ? 'text-white' : 'text-neutral-500 bg-neutral-700/50 hover:bg-neutral-600/50'}`} style={{backgroundColor: visibleInteractions[type] ? {HydrogenBond: '#0ea5e9', Hydrophobic: '#f59e0b', PiStacking: '#8b5cf6'}[type] : undefined}}>
                        {type.replace('Bond','').replace('Stacking', ' π-Stack')}
                    </button>
                ))}
            </div>
        )}
        {isLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-neutral-400 bg-neutral-800/80 rounded-md">
                <LoaderIcon className="w-8 h-8 animate-spin" />
                <p className="mt-2 text-sm">{loadingMessage}</p>
            </div>
        )}
        {!isLoading && error && (
             <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-red-400 p-4 text-xs bg-neutral-800/95 rounded-md">
                <p className="font-semibold mb-2">Could not load 3D model</p>
                <p className="max-w-md">{error}</p>
            </div>
        )}
    </div>
  );
};

export default MoleculeViewer3D;
