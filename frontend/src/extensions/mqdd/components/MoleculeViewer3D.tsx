
import React, { useRef, useEffect, useState } from 'react';
import { LoaderIcon } from './Icons';
import type { Interaction } from '../types';

declare const $3Dmol: any;
type ProteinStyle = 'cartoon' | 'surface' | 'electrostatic';
type InteractionType = Interaction['type'];

interface MoleculeViewer3DProps {
  smiles: string;
  pdbId?: string;
  interactions?: Interaction[];
  className?: string;
}

const SpinIcon: React.FC<{isSpinning: boolean, className?: string}> = ({ isSpinning, className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
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

  useEffect(() => {
    const load3Dmol = async () => {
      if (typeof $3Dmol === 'undefined') {
        setLoadingMessage('Loading 3D library...');
        return new Promise<void>((resolve, reject) => {
          const script = document.createElement('script');
          script.src = 'https://cdnjs.cloudflare.com/ajax/libs/3Dmol/2.0.4/3Dmol-min.js';
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject(new Error('Failed to load $3Dmol library'));
          document.head.appendChild(script);
        });
      }
    };

    const initViewer = async () => {
      try {
        await load3Dmol();
        
        const viewerElement = viewerRef.current;
        if (viewerElement && !viewerInstanceRef.current) {
            if (typeof $3Dmol === 'undefined') {
                throw new Error("3D library ($3Dmol) could not be initialized.");
            }
            viewerInstanceRef.current = $3Dmol.createViewer(viewerElement, {
                backgroundColor: '#262626',
                backgroundAlpha: 1,
                camera: { fov: 45 }
            });
            
            const resizeObserver = new ResizeObserver(() => {
                viewerInstanceRef.current?.resize();
            });
            resizeObserver.observe(viewerElement);
            
            // Clean up observer
            return () => {
                resizeObserver.unobserve(viewerElement);
                if (viewerInstanceRef.current) viewerInstanceRef.current = null;
            };
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize 3D viewer');
        setIsLoading(false);
      }
    };

    initViewer();
  }, []);


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
            } else if (proteinStyle === 'surface') {
                viewer.addSurface($3Dmol.SurfaceType.VDW, { opacity: 0.85, colorscheme: 'whiteCarbon' }, proteinSelection);
                viewer.addStyle(bindingSiteInProtein, { stick: { colorscheme: "cyanCarbon", radius: 0.15 }});
            } else { // Electrostatic
                viewer.addSurface($3Dmol.SurfaceType.MS, { opacity: 0.85, colorscheme: 'pqr' }, proteinSelection);
                viewer.addStyle(bindingSiteInProtein, { stick: { colorscheme: "cyanCarbon", radius: 0.15 }});
            }

            if (interactions && interactions.length > 0) {
                 if (!isMounted) return;
                 setLoadingMessage('Rendering interactions...');
                 const interactionColors: Record<InteractionType, string> = {
                    HydrogenBond: '#38bdf8',
                    Hydrophobic: '#fbbf24',
                    PiStacking: '#a78bfa',
                 };
                 interactions.forEach(interaction => {
                    if (visibleInteractions[interaction.type]) {
                        const proteinAtoms = { model: proteinModel, index: interaction.proteinAtoms };
                        const ligandAtoms = { model: ligandModel, index: interaction.ligandAtoms };

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
        className={`px-2 py-1 text-xs font-medium rounded ${proteinStyle === style ? 'bg-mq-cyan text-mq-black' : 'bg-mq-surface/50 hover:bg-mq-hover text-mq-text-secondary'} transition-apple disabled:opacity-50`}
    >
        {label}
    </button>
  );

  return (
    <div className={`relative w-full h-full min-h-[300px] rounded-2xl overflow-hidden bg-[#12121e] border border-mq-border ${className}`}>
        <div ref={viewerRef} className="w-full h-full" />
        <div className="absolute top-4 right-4 flex gap-2 z-10">
            {hasPdbId && (
                <>
                    <ProteinStyleButton style="cartoon" label="Cartoon" />
                    <ProteinStyleButton style="surface" label="Surface" />
                    <ProteinStyleButton style="electrostatic" label="ESP" />
                </>
            )}
            <button
                onClick={toggleSpin}
                disabled={isLoading || !!error}
                className="w-8 h-8 rounded-lg bg-mq-surface/50 hover:bg-mq-hover flex items-center justify-center text-mq-text transition-apple disabled:opacity-50"
                aria-label={isSpinning ? 'Pause rotation' : 'Start rotation'}
            >
                <SpinIcon isSpinning={isSpinning} className="w-4 h-4" />
            </button>
        </div>
         {hasInteractions && (
            <div className="absolute bottom-4 left-4 flex gap-2 z-10 bg-mq-surface/60 backdrop-blur-md p-2 rounded-xl border border-mq-border">
                {(Object.keys(visibleInteractions) as InteractionType[]).map(type => (
                    <button 
                        key={type} 
                        onClick={() => toggleInteractionVisibility(type)} 
                        className={`px-3 py-1.5 text-[11px] font-bold rounded-lg transition-apple uppercase tracking-wider ${
                            visibleInteractions[type] 
                            ? 'text-white shadow-glow-subtle' 
                            : 'text-mq-text-tertiary bg-mq-void/40 hover:bg-mq-void/60'
                        }`} 
                        style={{backgroundColor: visibleInteractions[type] ? {HydrogenBond: '#0ea5e9', Hydrophobic: '#f59e0b', PiStacking: '#8b5cf6'}[type] : undefined}}
                    >
                        {type.replace('Bond','').replace('Stacking', ' π-Stack')}
                    </button>
                ))}
            </div>
        )}
        {isLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-mq-cyan bg-[#12121e]/80 backdrop-blur-sm">
                <LoaderIcon className="w-10 h-10 animate-spin" />
                <p className="mt-4 text-[13px] font-mono tracking-widest uppercase opacity-70">{loadingMessage}</p>
            </div>
        )}
        {!isLoading && error && (
             <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-mq-red p-8 text-xs bg-[#12121e]/95">
                <div className="w-12 h-12 rounded-full border border-mq-red/30 flex items-center justify-center text-xl mb-4">⚠️</div>
                <p className="font-bold text-[14px] mb-2 uppercase tracking-wide">Model Loading Error</p>
                <p className="max-w-xs text-mq-text-tertiary text-[12px] leading-relaxed">{error}</p>
            </div>
        )}
    </div>
  );
};

export default MoleculeViewer3D;
