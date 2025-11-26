# Pipeline to extract species names from the UniProt Reference Clusters (UniRef) for MSA analysis.
Two Jupyter notebooks. One that creates a lookup SQLite database extracting all the species names present in the 

## Usage

### MSA_Similarity.ipynb

The MSA provided by ColabFold doesn't include species names. It only contains the UniProt IDs of sequences present in the alignment. To extract species names and present them in a plot, we need to reverse the search and retrieve species information from the UniProt database using these IDs.

This jupyter notebook provides the data pipeline that extracts all the species names from the MSA, based on the UniRef100 database. This database needs to be downloaded locally (Note: this is a very large file ~121Gb) in order to create the lookup table which will hold the species names, paired with their UniProt IDs.

### MSA_Analysis.ipynb

The second Jupyter notebook that actually uses the lookup table to analyse the MSA and present the N number of species (as defined by the user) with the greater similarity to the sequence provided for folding by AF2/ColabFold.

### As presented in the articles below
1. [Playing with a Nobel prize winner tool: Exploring AlphaFold with ColabFold](https://www.linkedin.com/pulse/playing-nobel-prize-winner-tool-exploring-alphafold-delitheos-cn6fc/?trackingId=BFnZwRJXQny9kcgWgaSVwQ%3D%3D)
2. [Playing with a Nobel prize winner tool (part 2): Interpreting the results of ColabFold-AF2](https://www.linkedin.com/pulse/playing-nobel-prize-winner-tool-part-2-interpreting-results-delitheos-cn6fc/?trackingId=BFnZwRJXQny9kcgWgaSVwQ%3D%3D)
3. [Playing with a Nobel prize winner tool (part 3): Further analysis of the results of ColabFold-AF2](https://www.linkedin.com/pulse/playing-nobel-prize-winner-tool-part-3-further-analysis-delitheos-cn6fc/?trackingId=BFnZwRJXQny9kcgWgaSVwQ%3D)
