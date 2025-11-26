#!/usr/bin/env python3
import numpy as np
import matplotlib.pyplot as plt
import json
import argparse
import sys
import os

def validate_openfold_json(data):
    """Validate that the JSON contains expected OpenFold structure."""
    required_keys = ['plddt', 'mean_plddt']
    if not all(key in data for key in required_keys):
        # Try to find similar keys (case-insensitive)
        lower_keys = [k.lower() for k in data.keys()]
        if 'plddt' not in data:
            if 'plDDT'.lower() in lower_keys:
                data['plddt'] = data['plDDT']
            elif 'confidence'.lower() in lower_keys:
                data['plddt'] = data['confidence']
            else:
                raise ValueError(f"File missing required keys. Found keys: {list(data.keys())}")

def load_plddt_from_file(file_path):
    """Load pLDDT scores from the JSON file."""
    if not os.path.exists(file_path):
        raise ValueError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        validate_openfold_json(data)
        return np.array(data['plddt'])
    except json.JSONDecodeError:
        # Try to handle common formatting issues
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            # Handle potential single quotes
            content = content.replace("'", '"')
            data = json.loads(content)
            validate_openfold_json(data)
            return np.array(data['plddt'])
        except Exception as e:
            print(f"File content preview (first 200 chars):\n{content[:200]}")
            raise ValueError(f"Invalid JSON format: {str(e)}")

def calculate_statistics(plddt, label):
    """Calculate and print statistics for pLDDT scores."""
    stats = {
        'mean': np.mean(plddt),
        'median': np.median(plddt),
        'min': np.min(plddt),
        'max': np.max(plddt),
        'length': len(plddt)
    }
    
    print(f"\nStatistics for {label}:")
    print(f"  Length: {stats['length']} residues")
    print(f"  Mean pLDDT: {stats['mean']:.2f}")
    print(f"  Median pLDDT: {stats['median']:.2f}")
    print(f"  Min pLDDT: {stats['min']:.2f}")
    print(f"  Max pLDDT: {stats['max']:.2f}")
    
    return stats

def plot_plddt_comparison(plddt1, plddt2, title1="Prediction 1", title2="Prediction 2", output_file=None):
    """Plot comparison of pLDDT scores."""
    if len(plddt1) != len(plddt2):
        print("⚠️ Truncating to shorter length:", min(len(plddt1), len(plddt2)))
        min_len = min(len(plddt1), len(plddt2))
        plddt1 = plddt1[:min_len]
        plddt2 = plddt2[:min_len]

    residues = np.arange(1, len(plddt1) + 1)
    
    plt.figure(figsize=(12, 6))
    plt.plot(residues, plddt1, label=title1, color='blue')
    plt.plot(residues, plddt2, label=title2, color='red')
    plt.fill_between(residues, plddt1, plddt2, where=(plddt1>plddt2), 
                   color='blue', alpha=0.2, label=f'Higher in {title1}')
    plt.fill_between(residues, plddt1, plddt2, where=(plddt2>plddt1),
                   color='red', alpha=0.2, label=f'Higher in {title2}')
    
    plt.xlabel('Residue Number')
    plt.ylabel('pLDDT Score')
    plt.title('pLDDT Score Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}.png")
    else:
        plt.show()

def compare_plddt_files(file1, file2, label1="Prediction 1", label2="Prediction 2", output_file=None):
    """Compare pLDDT scores from the two files."""
    print("Processing files...")
    plddt1 = load_plddt_from_file(file1)
    plddt2 = load_plddt_from_file(file2)
    
    # Get the filenames of the files for user to check
    filename1 = os.path.basename(file1)
    filename2 = os.path.basename(file2)
    
    print(f"{filename1} loaded with {len(plddt1)} residues")
    print(f"{filename2} loaded with {len(plddt2)} residues")
    
    # Calculate and display statistics
    stats1 = calculate_statistics(plddt1, label1)
    stats2 = calculate_statistics(plddt2, label2)
    
    # Create comparison plot
    plot_plddt_comparison(plddt1, plddt2, label1, label2, output_file)
    
    return stats1, stats2

def main():
    parser = argparse.ArgumentParser(
        description='OpenFold pLDDT Comparison Tool - Compare pLDDT scores from two OpenFold JSON output files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s model1.json model2.json
  %(prog)s model1.json model2.json --label1 "Experiment 1" --label2 "Experiment 2"
  %(prog)s model1.json model2.json --output comparison_plot.png
        """
    )
    
    parser.add_argument('file1', help='First OpenFold JSON file')
    parser.add_argument('file2', help='Second OpenFold JSON file')
    parser.add_argument('--label1', default='Prediction 1', help='Label for first file (default: Prediction 1)')
    parser.add_argument('--label2', default='Prediction 2', help='Label for second file (default: Prediction 2)')
    parser.add_argument('--output', '-o', help='Output file to save the plot (optional)')
    
    args = parser.parse_args()
    
    try:
        compare_plddt_files(args.file1, args.file2, args.label1, args.label2, args.output)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTips:")
        print("- Make sure you're providing OpenFold output JSON files")
        print("- Check the files contain 'plddt' scores")
        print("- Try opening the files in a text editor to verify their contents")
        sys.exit(1)

if __name__ == "__main__":
    print("OpenFold pLDDT Comparison Tool")
    print("Compare two OpenFold JSON output files to compare their pLDDT scores\n")
    main()