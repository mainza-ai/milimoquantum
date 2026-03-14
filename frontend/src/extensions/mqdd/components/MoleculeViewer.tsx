
import React, { useRef, useEffect } from 'react';

declare const SmilesDrawer: any;

interface MoleculeViewerProps {
  smiles: string;
  className?: string;
  highlightSmarts?: string;
}

const MoleculeViewer: React.FC<MoleculeViewerProps> = ({ smiles, className, highlightSmarts }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const loadSmilesDrawer = async () => {
      if (typeof SmilesDrawer === 'undefined') {
        return new Promise<void>((resolve, reject) => {
          const script = document.createElement('script');
          script.src = 'https://unpkg.com/smiles-drawer@2.0.1/dist/smiles-drawer.min.js';
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject(new Error('Failed to load SmilesDrawer library'));
          document.head.appendChild(script);
        });
      }
    };

    const drawMolecule = async () => {
      try {
        await loadSmilesDrawer();
        if (canvasRef.current && smiles && typeof SmilesDrawer !== 'undefined') {
          const options = {
              width: 300,
              height: 250,
              themes: {
                dark: {
                    C: '#c1c1c1',
                    O: '#e54545',
                    N: '#4585e5',
                    F: '#8fe545',
                    CL: '#45e58f',
                    BR: '#e58f45',
                    I: '#a045e5',
                    P: '#e5a045',
                    S: '#e5e545',
                    B: '#e545a0',
                    SI: '#a0a0a0',
                    H: '#c1c1c1',
                    BACKGROUND: 'transparent',
                    HIGHLIGHT: 'rgba(239, 68, 68, 0.7)'
                }
            }
          };
          const smilesDrawer = new SmilesDrawer.Drawer(options);

          SmilesDrawer.parse(smiles, (tree: any) => {
            if (!tree) return;
            let atomIdsToHighlight: number[] = [];
            if (highlightSmarts) {
                try {
                    const matches = SmilesDrawer.Smarts.getAtoms(tree, highlightSmarts);
                    atomIdsToHighlight = matches.flat();
                } catch (err) {
                    console.error("Error matching SMARTS pattern:", err);
                }
            }
            smilesDrawer.draw(tree, canvasRef.current, 'dark', false, atomIdsToHighlight);
          }, (err: any) => {
            console.error("SMILES parsing error:", err);
          });
        }
      } catch (err) {
        console.error(err);
      }
    };

    drawMolecule();
  }, [smiles, highlightSmarts]);

  return <canvas ref={canvasRef} className={className}></canvas>;
};

export default MoleculeViewer;
