import json
import matplotlib.pyplot as plt
import argparse
import sys

def load_plddt(json_file):
    """Load pLDDT scores from ColabFold JSON."""
    with open(json_file, "r") as f:
        data = json.load(f)
    return data["plddt"]

def get_chain_boundaries(pdb_file):
    """Parse TER records to find chain boundaries with absolute positions."""
    chain_data = []
    current_chain = None
    current_start = 1
    
    with open(pdb_file, "r") as f:
        for line in f:
            if line.startswith("TER"):
                parts = line.split()
                chain_id = parts[3]       # 4th column (e.g., 'A')
                end_res = int(parts[4])    # 5th column (TER residue number)
                chain_data.append((chain_id, current_start, end_res))
                current_start += end_res  # Next chain starts after this one's length
    
    # Convert to absolute positions
    chain_boundaries = {}
    cumulative = 0
    for i, (chain_id, _, end_res) in enumerate(chain_data):
        chain_length = end_res
        start_abs = cumulative + 1
        end_abs = cumulative + chain_length
        chain_boundaries[chain_id] = (start_abs, end_abs)
        cumulative += chain_length
    
    # Ensure last chain extends to end of protein
    total_residues = sum(end_res for _, _, end_res in chain_data)
    if chain_data:
        last_chain = chain_data[-1][0]
        chain_boundaries[last_chain] = (chain_boundaries[last_chain][0], total_residues)
    
    return chain_boundaries

def plot_plddt_with_chains(plddt, chain_boundaries, model_name="Model", output_file=None):
    """Plot pLDDT with accurate chain shading covering full protein length."""
    plt.figure(figsize=(12, 4))
    plt.plot(range(1, len(plddt) + 1), plddt, color="blue", label="pLDDT")
    
    # Shade chain regions
    colors = ["#FFDDDD", "#DDFFDD", "#DDDDFF"]  # Light red/green/blue
    for i, (chain, (start, end)) in enumerate(chain_boundaries.items()):
        plt.axvspan(start, end, color=colors[i % len(colors)], alpha=0.8, 
                   label=f"Chain {chain}")
        if i > 0:  # Mark chain boundaries
            plt.axvline(x=start, color="black", linestyle="--",
                       label="Chain Boundary" if i == 1 else None)
    
    plt.xlabel("Residue Position")
    plt.ylabel("pLDDT Score")
    plt.title(f"{model_name} - Predicted LDDT per position")
    plt.ylim(0, 110)
    plt.axhline(y=50, color="red", linestyle=":", label="Low Confidence")
    plt.axhline(y=70, color="orange", linestyle=":", label="Medium Confidence")
    plt.axhline(y=90, color="green", linestyle=":", label="High Confidence")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
    plt.grid(alpha=0.3)
    if output_file:
        plt.savefig(f"{output_file}.png", dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}.png\n")
    else:
        plt.show()

def main():
    parser = argparse.ArgumentParser(description="Plot pLDDT with chain shading and pLDDT thresholds.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
                                     Examples:
                                     %(prog)s pdb_file.pdb json_file.json
                                     %(prog)s pdb_file.pdb json_file.json --model_name MyModel
                                     %(prog)s pdb_file.pdb json_file.json --output my_plot
                                     """
                                     )
    
    parser.add_argument("pdb_file", help="Path to the PDB file.")
    parser.add_argument("json_file", help="Path to the ColabFold JSON file.") 
    parser.add_argument("--model_name", "-m", default="Model", help="Model name for the plot title.")
    parser.add_argument("--output", "-o", help="Output file to save the plot (optional).")
    args = parser.parse_args()

    try:
        plot_plddt_with_chains(load_plddt(args.json_file), get_chain_boundaries(args.pdb_file), args.model_name, args.output)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTips:")
        print("- Make sure you're providing correct PDB and JSON files")
        print("- Ensure that the order of the arguments is correct (PDB first, JSON second)")
        print("- Try opening the files in a text editor to verify their contents\n")
        sys.exit(1)
    
if __name__ == "__main__":
    print("*"*25)
    print("pLDDT Visualization Tool")
    print("*"*25,"\n")
    print("Visualize pLDDT scores with accurate chain shading and pLDDT thresholds.\n")

    main()