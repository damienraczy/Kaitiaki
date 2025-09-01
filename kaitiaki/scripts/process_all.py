#!/usr/bin/env python3
# kaitiaki/scripts/process_all.py
"""
Script complet pour traiter les documents avec parsing intelligent
Usage: python -m kaitiaki.scripts.process_all
"""

import sys
from pathlib import Path
import subprocess
import time

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

def run_step(step_name: str, module_path: str):
    """Execute a processing step"""
    print(f"\n{'='*50}")
    print(f"🚀 ÉTAPE: {step_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        # Run as module to ensure proper imports
        result = subprocess.run([
            sys.executable, "-m", module_path
        ], check=True, capture_output=True, text=True, cwd=project_root)
        
        print(result.stdout)
        if result.stderr:
            print("⚠️ Warnings/Errors:")
            print(result.stderr)
            
        elapsed = time.time() - start_time
        print(f"✅ {step_name} completed in {elapsed:.2f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        print(f"❌ {step_name} failed after {elapsed:.2f}s")
        print(f"Return code: {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ {step_name} failed after {elapsed:.2f}s with exception: {e}")
        return False

def main():
    """Run complete processing pipeline"""
    print("🎯 KAITIAKI - PIPELINE DE TRAITEMENT COMPLET")
    print(f"Working directory: {project_root}")
    
    # Check that we have PDFs to process
    raw_dir = project_root / "kaitiaki" / "data" / "raw"
    pdf_files = list(raw_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {raw_dir}")
        print("Please add PDF files to process before running this script.")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files to process")
    
    pipeline_steps = [
        ("1. PDF Parsing (Basic + Intelligent)", "kaitiaki.ingest.parse_pdf"),
        ("2. Text Normalization & Chunking", "kaitiaki.ingest.normalize"), 
        ("3. Vector & BM25 Indexing", "kaitiaki.ingest.indexer"),
    ]
    
    total_start = time.time()
    
    for step_name, module_path in pipeline_steps:
        success = run_step(step_name, module_path)
        if not success:
            print(f"\n❌ Pipeline stopped at: {step_name}")
            print("Please fix the errors and try again.")
            return
    
    total_elapsed = time.time() - total_start
    
    print(f"\n🎉 PIPELINE COMPLETE!")
    print(f"Total processing time: {total_elapsed:.2f}s")
    print("\n📊 Next steps:")
    print("1. Start the API server: python -m kaitiaki.api.server")
    print("2. Run evaluation: python -m kaitiaki.eval.evaluate")
    print("3. Test Qdrant connection: python -m kaitiaki.scripts.test_qdrant_connection")
    
    # Show some final statistics
    try:
        from kaitiaki.utils.settings import CFG
        import json
        
        processed_dir = Path(CFG["paths"]["data_processed"])
        normalized_files = list(processed_dir.glob("*.normalized.json"))
        
        total_chunks = 0
        intelligent_docs = 0
        
        for f in normalized_files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                total_chunks += len(data.get("chunks", []))
                if data.get("parsing_method") == "intelligent":
                    intelligent_docs += 1
            except:
                continue
        
        print(f"\n📈 Final Statistics:")
        print(f"   • PDF files processed: {len(pdf_files)}")
        print(f"   • Documents normalized: {len(normalized_files)}")
        print(f"   • Total chunks created: {total_chunks}")
        print(f"   • Intelligent parsing used: {intelligent_docs}")
        
    except Exception as e:
        print(f"Could not gather final statistics: {e}")

if __name__ == "__main__":
    main()